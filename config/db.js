const { Pool } = require('pg');
const dotenv = require('dotenv');

dotenv.config();

// PostgreSQL connection pool
const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'mount_isa_services',
  password: process.env.DB_PASSWORD || 'postgres',
  port: process.env.DB_PORT || 5432,
});

// Test database connection (non-blocking)
pool.connect((err, client, release) => {
  if (err) {
    console.error('Database connection error:', err.message);
    console.log('Application will continue without database');
  } else {
    console.log('Database connected successfully');
    release();
  }
});

module.exports = {
  query: async (text, params) => {
    try {
      return await pool.query(text, params);
    } catch (error) {
      console.error('Database query error:', error.message);
      throw error;
    }
  },
};
