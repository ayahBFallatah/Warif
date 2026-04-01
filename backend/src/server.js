const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const winston = require('winston');
const promClient = require('prom-client');

// Import middleware and routes
const { errorHandler } = require('./middleware/errorHandler');
const { requestLogger } = require('./middleware/requestLogger');
const { authMiddleware } = require('./middleware/authMiddleware');
const { validateRequest } = require('./middleware/validationMiddleware');

// Import routes
const authRoutes = require('./controllers/authController');
const deviceRoutes = require('./controllers/deviceController');
const sensorRoutes = require('./controllers/sensorController');
const alertRoutes = require('./controllers/alertController');
const actuatorRoutes = require('./controllers/actuatorController');

// Import services
const { initializeDatabase } = require('./services/databaseService');
const { initializeMQTT } = require('./services/mqttService');
const { initializeRedis } = require('./services/redisService');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: process.env.CORS_ORIGIN?.split(',') || ["http://localhost:3000", "http://localhost:8501"],
    methods: ["GET", "POST"]
  }
});

// Prometheus metrics
const collectDefaultMetrics = promClient.collectDefaultMetrics;
collectDefaultMetrics({ register: promClient.register });

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));

app.use(cors({
  origin: process.env.CORS_ORIGIN?.split(',') || ["http://localhost:3000", "http://localhost:8501"],
  credentials: true
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Apply rate limiting to all routes
app.use(limiter);

// Request logging
app.use(requestLogger);

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    const db = require('./services/databaseService');
    await db.pool.query('SELECT 1');
    
    // Check Redis connection
    const redis = require('./services/redisService');
    await redis.ping();
    
    res.json({ 
      status: 'healthy', 
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: process.env.npm_package_version || '1.0.0'
    });
  } catch (err) {
    res.status(503).json({ 
      status: 'unhealthy', 
      error: err.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Prometheus metrics endpoint
app.get('/metrics', async (req, res) => {
  try {
    res.set('Content-Type', promClient.register.contentType);
    res.end(await promClient.register.metrics());
  } catch (err) {
    res.status(500).end(err);
  }
});

// API routes
app.use('/api/auth', authRoutes);
app.use('/api/devices', authMiddleware, deviceRoutes);
app.use('/api/sensors', authMiddleware, sensorRoutes);
app.use('/api/alerts', authMiddleware, alertRoutes);
app.use('/api/actuators', authMiddleware, actuatorRoutes);

// WebSocket connection management
const connectedClients = new Map();

io.on('connection', (socket) => {
  const clientId = socket.id;
  connectedClients.set(clientId, socket);
  
  winston.info(`Client connected: ${clientId}`);
  
  socket.on('subscribe', (data) => {
    const { deviceId, topics } = data;
    if (deviceId) {
      socket.join(`device:${deviceId}`);
      winston.info(`Client ${clientId} subscribed to device: ${deviceId}`);
    }
    if (topics && Array.isArray(topics)) {
      topics.forEach(topic => socket.join(topic));
    }
  });
  
  socket.on('disconnect', () => {
    connectedClients.delete(clientId);
    winston.info(`Client disconnected: ${clientId}`);
  });
});

// Error handling middleware
app.use(errorHandler);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ 
    error: 'Route not found',
    path: req.originalUrl,
    method: req.method
  });
});

// Global error handler for uncaught exceptions
process.on('uncaughtException', (err) => {
  winston.error('Uncaught Exception:', err);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  winston.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Graceful shutdown
const gracefulShutdown = (signal) => {
  winston.info(`Received ${signal}. Starting graceful shutdown...`);
  
  server.close(() => {
    winston.info('HTTP server closed');
    process.exit(0);
  });
  
  // Force close after 30 seconds
  setTimeout(() => {
    winston.error('Could not close connections in time, forcefully shutting down');
    process.exit(1);
  }, 30000);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Initialize services and start server
const PORT = process.env.API_PORT || 8000;

async function startServer() {
  try {
    winston.info('Starting Green Engine Backend...');
    
    // Initialize services
    await initializeDatabase();
    await initializeRedis();
    await initializeMQTT();
    
    // Start server
    server.listen(PORT, () => {
      winston.info(`🚀 Green Engine Backend running on port ${PORT}`);
      winston.info(`📊 Health check: http://localhost:${PORT}/health`);
      winston.info(`📈 Metrics: http://localhost:${PORT}/metrics`);
    });
    
  } catch (error) {
    winston.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

module.exports = { app, server, io };
