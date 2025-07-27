#!/usr/bin/env node

// Script to initialize the database with schema and initial data

const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Database connection
const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'mount_isa_services',
  password: process.env.DB_PASSWORD || 'postgres',
  port: process.env.DB_PORT || 5432,
});

async function initDatabase() {
  try {
    console.log('Initializing database...');
    
    // Read schema file
    const schemaPath = path.join(__dirname, '..', 'database', 'schema.sql');
    const schemaSQL = fs.readFileSync(schemaPath, 'utf8');
    
    // Split schema into individual statements
    const statements = schemaSQL
      .split(';')
      .map(stmt => stmt.trim())
      .filter(stmt => stmt.length > 0);
    
    // Execute each statement
    for (const statement of statements) {
      if (statement.trim().length > 0) {
        console.log('Executing statement...');
        await pool.query(statement);
      }
    }
    
    console.log('Database initialized successfully!');
    
    // Test connection
    const result = await pool.query('SELECT COUNT(*) FROM service_categories');
    console.log(`Found ${result.rows[0].count} categories in database`);
    
    // Close connection
    await pool.end();
  } catch (error) {
    console.error('Error initializing database:', error);
    process.exit(1);
  }
}

// Run initialization if script is called directly
if (require.main === module) {
  initDatabase();
}

module.exports = { initDatabase };
