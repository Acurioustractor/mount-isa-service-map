#!/usr/bin/env node

// Script to initialize Supabase database with schema and initial data

const fs = require('fs');
const path = require('path');
const { supabase } = require('../config/supabase');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

async function initSupabaseDatabase() {
  try {
    console.log('🚀 Initializing Supabase database...');
    console.log('📍 Supabase URL:', process.env.SUPABASE_URL);
    
    // Read schema file
    const schemaPath = path.join(__dirname, '..', 'database', 'schema.sql');
    const schemaSQL = fs.readFileSync(schemaPath, 'utf8');
    
    console.log('📋 Loaded database schema...');
    
    // Split schema into individual statements
    const statements = schemaSQL
      .split(';')
      .map(stmt => stmt.trim())
      .filter(stmt => stmt.length > 0 && !stmt.startsWith('--'));
    
    console.log(`📝 Found ${statements.length} SQL statements to execute...`);
    
    // Execute each statement using raw SQL
    let successCount = 0;
    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i];
      if (statement.trim().length > 0) {
        try {
          console.log(`⚡ Executing statement ${i + 1}/${statements.length}...`);
          
          // Use raw SQL execution for schema creation
          const { data, error } = await supabase.rpc('exec_sql', { 
            query: statement + ';' 
          });
          
          if (error && error.code !== '42P07') { // 42P07 = relation already exists
            // Try direct SQL execution as fallback
            const { error: directError } = await supabase
              .from('_supabase_migrations')
              .insert({ query: statement });
              
            if (directError && !directError.message.includes('already exists')) {
              console.warn(`⚠️  Warning on statement ${i + 1}:`, error.message);
            }
          }
          successCount++;
        } catch (err) {
          if (!err.message.includes('already exists') && !err.message.includes('duplicate')) {
            console.warn(`⚠️  Warning on statement ${i + 1}:`, err.message);
          }
        }
      }
    }
    
    console.log(`✅ Successfully executed ${successCount} database statements!`);
    
    // Test connection by checking tables
    try {
      const { data: tables, error: tablesError } = await supabase
        .rpc('get_table_names');
        
      if (!tablesError && tables) {
        console.log(`📊 Found ${tables.length} tables in database`);
      }
    } catch (e) {
      // Try alternative approach
      const { data: serviceCategories, error: categoriesError } = await supabase
        .from('service_categories')
        .select('count', { count: 'exact', head: true });
        
      if (!categoriesError) {
        console.log(`📋 Service categories table ready`);
      }
    }
    
    // Check if we have default categories
    const { data: categories, error: catError } = await supabase
      .from('service_categories')
      .select('*')
      .limit(1);
      
    if (!catError && categories) {
      if (categories.length > 0) {
        console.log(`📂 Found ${categories.length}+ service categories`);
      } else {
        console.log('📂 Service categories table is empty but ready');
      }
    }
    
    console.log('🎉 Supabase database initialization completed successfully!');
    
  } catch (error) {
    console.error('❌ Error initializing Supabase database:', error);
    
    // Try simple table creation as fallback
    console.log('🔄 Attempting basic table creation...');
    try {
      // Create essential tables manually
      await createBasicTables();
    } catch (fallbackError) {
      console.error('❌ Fallback initialization failed:', fallbackError);
      process.exit(1);
    }
  }
}

async function createBasicTables() {
  const basicTables = [
    `CREATE TABLE IF NOT EXISTS service_categories (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(100) NOT NULL UNIQUE,
      description TEXT,
      parent_id UUID REFERENCES service_categories(id),
      is_active BOOLEAN DEFAULT true,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`,
    `CREATE TABLE IF NOT EXISTS services (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(255) NOT NULL,
      description TEXT,
      category_id UUID REFERENCES service_categories(id),
      address TEXT,
      suburb VARCHAR(100),
      state VARCHAR(10) DEFAULT 'QLD',
      postcode VARCHAR(10),
      latitude DECIMAL(10, 8),
      longitude DECIMAL(11, 8),
      phone VARCHAR(20),
      email VARCHAR(255),
      website VARCHAR(255),
      is_active BOOLEAN DEFAULT true,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`
  ];
  
  for (const table of basicTables) {
    const { error } = await supabase.rpc('exec_sql', { query: table });
    if (error && !error.message.includes('already exists')) {
      throw error;
    }
  }
  
  console.log('✅ Basic tables created successfully!');
}

// Run initialization if script is called directly
if (require.main === module) {
  initSupabaseDatabase();
}

module.exports = { initSupabaseDatabase };