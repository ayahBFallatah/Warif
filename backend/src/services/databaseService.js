const { Pool } = require('pg');
const winston = require('winston');

class DatabaseService {
  constructor() {
    this.pool = null;
    this.isConnected = false;
  }

  async initialize() {
    try {
      this.pool = new Pool({
        host: process.env.DB_HOST || 'postgres',
        port: process.env.DB_PORT || 5432,
        database: process.env.POSTGRES_DB || 'green_engine',
        user: process.env.POSTGRES_USER || 'green_user',
        password: process.env.DB_PASSWORD || 'password',
        max: 20, // Maximum number of clients in the pool
        idleTimeoutMillis: 30000, // Close idle clients after 30 seconds
        connectionTimeoutMillis: 2000, // Return an error after 2 seconds if connection could not be established
        maxUses: 7500, // Close (and replace) a connection after it has been used 7500 times
        ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
      });

      // Test connection
      const client = await this.pool.connect();
      await client.query('SELECT 1');
      client.release();

      this.isConnected = true;
      winston.info('Database connection established');

      // Initialize TimescaleDB extensions and tables
      await this.initializeTables();
      await this.createIndexes();
      await this.setupRetentionPolicies();

    } catch (error) {
      winston.error('Failed to initialize database:', error);
      throw error;
    }
  }

  async initializeTables() {
    try {
      // Enable TimescaleDB extension
      await this.pool.query('CREATE EXTENSION IF NOT EXISTS timescaledb');

      // Create devices table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS devices (
          device_id TEXT PRIMARY KEY,
          location_id TEXT NOT NULL,
          model TEXT,
          firmware_version TEXT,
          status TEXT DEFAULT 'offline',
          battery INTEGER,
          last_seen TIMESTAMPTZ,
          created_at TIMESTAMPTZ DEFAULT NOW(),
          updated_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      // Create sensor_readings hypertable
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS sensor_readings (
          id BIGSERIAL,
          device_id TEXT NOT NULL,
          t TIMESTAMPTZ NOT NULL,
          temperature DOUBLE PRECISION,
          humidity DOUBLE PRECISION,
          par DOUBLE PRECISION,
          soil_moisture DOUBLE PRECISION,
          ec DOUBLE PRECISION,
          co2 DOUBLE PRECISION,
          raw JSONB,
          created_at TIMESTAMPTZ DEFAULT NOW(),
          PRIMARY KEY (id, t)
        )
      `);

      // Convert to hypertable if not already
      await this.pool.query(`
        SELECT create_hypertable('sensor_readings', 't', if_not_exists => TRUE)
      `);

      // Create trays table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS trays (
          tray_id SERIAL PRIMARY KEY,
          tray_code TEXT UNIQUE NOT NULL,
          device_id TEXT REFERENCES devices(device_id),
          crop_type TEXT NOT NULL,
          planted_on DATE NOT NULL,
          expected_harvest DATE,
          status TEXT DEFAULT 'growing',
          notes TEXT,
          created_at TIMESTAMPTZ DEFAULT NOW(),
          updated_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      // Create tray_measurements table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS tray_measurements (
          id BIGSERIAL PRIMARY KEY,
          tray_id INTEGER REFERENCES trays(tray_id),
          measured_on TIMESTAMPTZ NOT NULL,
          height_mm DOUBLE PRECISION,
          biomass_g DOUBLE PRECISION,
          photo_url TEXT,
          notes TEXT,
          created_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      // Create alert_rules table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS alert_rules (
          id SERIAL PRIMARY KEY,
          device_id TEXT REFERENCES devices(device_id),
          name TEXT NOT NULL,
          description TEXT,
          condition TEXT NOT NULL,
          level TEXT DEFAULT 'warning',
          is_active BOOLEAN DEFAULT true,
          actions JSONB,
          created_at TIMESTAMPTZ DEFAULT NOW(),
          updated_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      // Create alerts table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS alerts (
          id BIGSERIAL PRIMARY KEY,
          device_id TEXT REFERENCES devices(device_id),
          rule_id INTEGER REFERENCES alert_rules(id),
          level TEXT NOT NULL,
          message TEXT NOT NULL,
          raw_data JSONB,
          is_resolved BOOLEAN DEFAULT false,
          resolved_at TIMESTAMPTZ,
          resolved_by TEXT,
          created_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      // Create actuator_commands table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS actuator_commands (
          id BIGSERIAL PRIMARY KEY,
          device_id TEXT REFERENCES devices(device_id),
          command TEXT NOT NULL,
          raw_data JSONB,
          status TEXT DEFAULT 'pending',
          executed_at TIMESTAMPTZ,
          response JSONB,
          created_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      // Create device_errors table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS device_errors (
          id BIGSERIAL PRIMARY KEY,
          device_id TEXT REFERENCES devices(device_id),
          error_type TEXT NOT NULL,
          message TEXT NOT NULL,
          raw_data JSONB,
          created_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      // Create dead_letter_queue table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS dead_letter_queue (
          id BIGSERIAL PRIMARY KEY,
          topic TEXT NOT NULL,
          message TEXT NOT NULL,
          error TEXT,
          retry_count INTEGER DEFAULT 0,
          processed_at TIMESTAMPTZ,
          created_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      // Create predictions table
      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS predictions (
          id BIGSERIAL PRIMARY KEY,
          tray_id INTEGER REFERENCES trays(tray_id),
          predicted_yield_g DOUBLE PRECISION NOT NULL,
          confidence_pct DOUBLE PRECISION,
          model_version TEXT,
          features JSONB,
          predicted_at TIMESTAMPTZ DEFAULT NOW(),
          created_at TIMESTAMPTZ DEFAULT NOW()
        )
      `);

      winston.info('Database tables initialized successfully');

    } catch (error) {
      winston.error('Failed to initialize tables:', error);
      throw error;
    }
  }

  async createIndexes() {
    try {
      // Performance indexes for sensor_readings
      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_sensor_readings_device_time 
        ON sensor_readings(device_id, t DESC)
      `);

      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_sensor_readings_temperature 
        ON sensor_readings(temperature) WHERE temperature IS NOT NULL
      `);

      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_sensor_readings_humidity 
        ON sensor_readings(humidity) WHERE humidity IS NOT NULL
      `);

      // Indexes for alerts
      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_alerts_device_level 
        ON alerts(device_id, level, created_at DESC)
      `);

      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_alerts_unresolved 
        ON alerts(created_at DESC) WHERE is_resolved = false
      `);

      // Indexes for trays
      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_trays_device_crop 
        ON trays(device_id, crop_type, status)
      `);

      winston.info('Database indexes created successfully');

    } catch (error) {
      winston.error('Failed to create indexes:', error);
      throw error;
    }
  }

  async setupRetentionPolicies() {
    try {
      // Data retention policy (90 days for sensor readings)
      await this.pool.query(`
        SELECT add_retention_policy('sensor_readings', INTERVAL '90 days')
      `);

      // Compression policy (compress data older than 7 days)
      await this.pool.query(`
        SELECT add_compression_policy('sensor_readings', INTERVAL '7 days')
      `);

      winston.info('Retention and compression policies configured');

    } catch (error) {
      winston.error('Failed to setup retention policies:', error);
      // Don't throw error as this is not critical for basic operation
    }
  }

  async getConnection() {
    if (!this.isConnected) {
      throw new Error('Database not connected');
    }
    return this.pool.connect();
  }

  async query(text, params) {
    if (!this.isConnected) {
      throw new Error('Database not connected');
    }
    return this.pool.query(text, params);
  }

  async transaction(callback) {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  isHealthy() {
    return this.isConnected;
  }

  async close() {
    if (this.pool) {
      await this.pool.end();
      this.isConnected = false;
      winston.info('Database connection closed');
    }
  }
}

const databaseService = new DatabaseService();

module.exports = { 
  databaseService, 
  initializeDatabase: () => databaseService.initialize(),
  pool: databaseService.pool
};
