const mqtt = require('mqtt');
const winston = require('winston');
const Joi = require('joi');
const { pool } = require('./databaseService');
const { redisClient } = require('./redisService');
const { broadcastSensorUpdate } = require('./websocketService');

// Telemetry schema validation
const telemetrySchema = Joi.object({
  device_id: Joi.string().required().pattern(/^[A-Z0-9-]+$/),
  location_id: Joi.string().required(),
  timestamp: Joi.date().iso().required(),
  readings: Joi.object({
    temperature_c: Joi.number().min(-50).max(100).required(),
    humidity_pct: Joi.number().min(0).max(100).required(),
    par_umol_m2_s: Joi.number().min(0).max(2000).required(),
    soil_moisture_pct: Joi.number().min(0).max(100).required(),
    ec_ms_cm: Joi.number().min(0).max(10).required(),
    co2_ppm: Joi.number().min(300).max(2000).required()
  }).required(),
  battery: Joi.number().min(0).max(100).required(),
  firmware_version: Joi.string().required()
});

class MQTTService {
  constructor() {
    this.client = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 5000;
  }

  async initialize() {
    try {
      const options = {
        host: process.env.MQTT_BROKER || 'mqtt',
        port: process.env.MQTT_PORT || 1883,
        clientId: `green_engine_backend_${Date.now()}`,
        clean: true,
        reconnectPeriod: this.reconnectDelay,
        connectTimeout: 30000,
        username: process.env.MQTT_USERNAME,
        password: process.env.MQTT_PASSWORD,
        rejectUnauthorized: process.env.MQTT_TLS_VERIFY === 'true'
      };

      // TLS configuration for production
      if (process.env.MQTT_TLS_VERIFY === 'true') {
        options.port = process.env.MQTT_TLS_PORT || 8883;
        options.protocol = 'mqtts';
        options.ca = process.env.MQTT_CA_CERT;
        options.cert = process.env.MQTT_CLIENT_CERT;
        options.key = process.env.MQTT_CLIENT_KEY;
      }

      this.client = mqtt.connect(options);
      this.setupEventHandlers();
      
      winston.info('MQTT service initialized');
    } catch (error) {
      winston.error('Failed to initialize MQTT service:', error);
      throw error;
    }
  }

  setupEventHandlers() {
    this.client.on('connect', () => {
      this.isConnected = true;
      this.reconnectAttempts = 0;
      winston.info('Connected to MQTT broker');
      
      // Subscribe to telemetry topics
      this.client.subscribe('greenengine/+/telemetry', { qos: 1 });
      this.client.subscribe('greenengine/+/status', { qos: 1 });
      this.client.subscribe('greenengine/+/error', { qos: 1 });
      
      winston.info('Subscribed to MQTT topics');
    });

    this.client.on('message', async (topic, message) => {
      try {
        await this.handleMessage(topic, message);
      } catch (error) {
        winston.error('Error handling MQTT message:', error);
      }
    });

    this.client.on('error', (error) => {
      winston.error('MQTT error:', error);
      this.isConnected = false;
    });

    this.client.on('close', () => {
      this.isConnected = false;
      winston.warn('MQTT connection closed');
    });

    this.client.on('reconnect', () => {
      this.reconnectAttempts++;
      winston.info(`MQTT reconnecting... Attempt ${this.reconnectAttempts}`);
      
      if (this.reconnectAttempts > this.maxReconnectAttempts) {
        winston.error('Max MQTT reconnection attempts reached');
        process.exit(1);
      }
    });
  }

  async handleMessage(topic, message) {
    try {
      const payload = JSON.parse(message.toString());
      const topicParts = topic.split('/');
      const deviceId = topicParts[1];
      const messageType = topicParts[2];

      winston.debug(`Received ${messageType} from device ${deviceId}`);

      switch (messageType) {
        case 'telemetry':
          await this.handleTelemetry(deviceId, payload);
          break;
        case 'status':
          await this.handleStatus(deviceId, payload);
          break;
        case 'error':
          await this.handleError(deviceId, payload);
          break;
        default:
          winston.warn(`Unknown message type: ${messageType}`);
      }
    } catch (error) {
      winston.error('Failed to parse MQTT message:', error);
      // Send to dead letter queue for investigation
      await this.sendToDeadLetterQueue(topic, message, error);
    }
  }

  async handleTelemetry(deviceId, payload) {
    try {
      // Validate telemetry data
      const { error, value } = telemetrySchema.validate(payload);
      if (error) {
        winston.warn(`Invalid telemetry schema for device ${deviceId}:`, error.details);
        return;
      }

      // Check for duplicate readings
      const existing = await pool.query(
        'SELECT id FROM sensor_readings WHERE device_id = $1 AND t = $2',
        [deviceId, value.timestamp]
      );

      if (existing.rows.length > 0) {
        winston.warn(`Duplicate reading detected for device ${deviceId} at ${value.timestamp}`);
        return;
      }

      // Insert into database
      const result = await pool.query(`
        INSERT INTO sensor_readings(
          device_id, t, temperature, humidity, par, 
          soil_moisture, ec, co2, raw, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
        RETURNING id
      `, [
        deviceId, value.timestamp, 
        value.readings.temperature_c, 
        value.readings.humidity_pct,
        value.readings.par_umol_m2_s,
        value.readings.soil_moisture_pct,
        value.readings.ec_ms_cm,
        value.readings.co2_ppm,
        JSON.stringify(payload)
      ]);

      winston.info(`Telemetry stored for device ${deviceId}, ID: ${result.rows[0].id}`);

      // Cache latest reading in Redis
      await redisClient.setex(
        `device:${deviceId}:latest`,
        300, // 5 minutes TTL
        JSON.stringify(value)
      );

      // Broadcast to WebSocket clients
      broadcastSensorUpdate(deviceId, value);

      // Check for alerts
      await this.checkAlerts(deviceId, value);

    } catch (error) {
      winston.error(`Failed to handle telemetry for device ${deviceId}:`, error);
      throw error;
    }
  }

  async handleStatus(deviceId, payload) {
    try {
      await pool.query(`
        UPDATE devices 
        SET last_seen = NOW(), status = $1, battery = $2, firmware_version = $3
        WHERE device_id = $4
      `, [payload.status, payload.battery, payload.firmware_version, deviceId]);

      winston.info(`Status updated for device ${deviceId}: ${payload.status}`);
    } catch (error) {
      winston.error(`Failed to update status for device ${deviceId}:`, error);
    }
  }

  async handleError(deviceId, payload) {
    try {
      await pool.query(`
        INSERT INTO device_errors (device_id, error_type, message, raw_data, created_at)
        VALUES ($1, $2, $3, $4, NOW())
      `, [deviceId, payload.error_type, payload.message, JSON.stringify(payload)]);

      winston.error(`Device error for ${deviceId}: ${payload.error_type} - ${payload.message}`);
    } catch (error) {
      winston.error(`Failed to log error for device ${deviceId}:`, error);
    }
  }

  async checkAlerts(deviceId, readings) {
    try {
      // Get alert rules for this device
      const rules = await pool.query(`
        SELECT * FROM alert_rules 
        WHERE device_id = $1 AND is_active = true
      `, [deviceId]);

      for (const rule of rules.rows) {
        const shouldTrigger = this.evaluateRule(rule.condition, readings);
        
        if (shouldTrigger) {
          await this.triggerAlert(deviceId, rule, readings);
        }
      }
    } catch (error) {
      winston.error(`Failed to check alerts for device ${deviceId}:`, error);
    }
  }

  evaluateRule(condition, readings) {
    try {
      // Safe rule evaluation using predefined conditions
      const conditions = {
        'temp_high': readings.readings.temperature_c > 25.0,
        'temp_low': readings.readings.temperature_c < 18.0,
        'humidity_high': readings.readings.humidity_pct > 80.0,
        'humidity_low': readings.readings.humidity_pct < 60.0,
        'soil_dry': readings.readings.soil_moisture_pct < 20.0,
        'soil_wet': readings.readings.soil_moisture_pct > 80.0,
        'light_low': readings.readings.par_umol_m2_s < 300.0,
        'co2_high': readings.readings.co2_ppm > 1000.0
      };

      return conditions[condition] || false;
    } catch (error) {
      winston.error('Rule evaluation error:', error);
      return false;
    }
  }

  async triggerAlert(deviceId, rule, readings) {
    try {
      // Insert alert
      const alertResult = await pool.query(`
        INSERT INTO alerts (device_id, rule_id, level, message, raw_data, created_at)
        VALUES ($1, $2, $3, $4, $5, NOW())
        RETURNING id
      `, [deviceId, rule.id, rule.level, rule.message, JSON.stringify(readings)]);

      winston.warn(`Alert triggered: ${rule.name} for device ${deviceId}`);

      // Execute actions
      if (rule.actions && Array.isArray(rule.actions)) {
        for (const action of rule.actions) {
          await this.executeAction(action, deviceId, readings);
        }
      }

      // Broadcast alert to WebSocket clients
      // This would be implemented in the websocket service

    } catch (error) {
      winston.error(`Failed to trigger alert for device ${deviceId}:`, error);
    }
  }

  async executeAction(action, deviceId, readings) {
    try {
      switch (action.type) {
        case 'command':
          await this.sendCommand(deviceId, action.payload);
          break;
        case 'notify':
          await this.sendNotification(action.targets, deviceId, action.message);
          break;
        default:
          winston.warn(`Unknown action type: ${action.type}`);
      }
    } catch (error) {
      winston.error(`Failed to execute action ${action.type}:`, error);
    }
  }

  async sendCommand(deviceId, command) {
    try {
      const topic = `greenengine/${deviceId}/cmd`;
      const message = JSON.stringify({
        ...command,
        timestamp: new Date().toISOString(),
        command_id: `cmd_${Date.now()}`
      });

      this.client.publish(topic, message, { qos: 1 }, (err) => {
        if (err) {
          winston.error(`Failed to send command to ${deviceId}:`, err);
        } else {
          winston.info(`Command sent to ${deviceId}: ${command.action}`);
        }
      });

      // Log command in database
      await pool.query(`
        INSERT INTO actuator_commands (device_id, command, raw_data, created_at)
        VALUES ($1, $2, $3, NOW())
      `, [deviceId, command.action, JSON.stringify(command)]);

    } catch (error) {
      winston.error(`Failed to send command to ${deviceId}:`, error);
    }
  }

  async sendNotification(targets, deviceId, message) {
    // Implementation for sending notifications (email, SMS, etc.)
    winston.info(`Notification sent to ${targets.join(', ')}: ${message}`);
  }

  async sendToDeadLetterQueue(topic, message, error) {
    try {
      await pool.query(`
        INSERT INTO dead_letter_queue (topic, message, error, created_at)
        VALUES ($1, $2, $3, NOW())
      `, [topic, message.toString(), error.message]);
    } catch (err) {
      winston.error('Failed to send message to dead letter queue:', err);
    }
  }

  isHealthy() {
    return this.isConnected;
  }

  async disconnect() {
    if (this.client) {
      this.client.end();
      this.isConnected = false;
      winston.info('MQTT service disconnected');
    }
  }
}

const mqttService = new MQTTService();

module.exports = { mqttService, initializeMQTT: () => mqttService.initialize() };
