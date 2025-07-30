const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');

dotenv.config();

// Supabase configuration
const supabaseUrl = process.env.SUPABASE_URL || 'https://awdckiwhptjivpzkxekq.supabase.co';
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 'sb_secret_fjzuYiIh7LPTGoT9kUgDIg_5bzdvPRo';

// Create Supabase client with service role key for backend operations
const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

// Test connection
supabase.from('services').select('count', { count: 'exact', head: true })
  .then(({ count, error }) => {
    if (error && error.code !== 'PGRST116') { // PGRST116 is "relation does not exist" - expected before schema setup
      console.error('Supabase connection error:', error.message);
    } else {
      console.log('Supabase connected successfully');
      if (count !== null) {
        console.log(`Found ${count} services in database`);
      }
    }
  })
  .catch(err => {
    console.log('Supabase connection ready (schema not yet initialized)');
  });

// Helper function to execute raw SQL (for schema creation)
async function executeSQL(sql) {
  try {
    const { data, error } = await supabase.rpc('exec_sql', { sql_query: sql });
    if (error) throw error;
    return { data, error: null };
  } catch (error) {
    console.error('SQL execution error:', error);
    return { data: null, error };
  }
}

// Modern query wrapper that works like the old db.query
async function query(sql, params = []) {
  try {
    // For simple SELECT queries, use Supabase client
    if (sql.trim().toLowerCase().startsWith('select')) {
      // Parse table name from SQL (basic implementation)
      const tableMatch = sql.match(/from\s+(\w+)/i);
      if (tableMatch) {
        const tableName = tableMatch[1];
        const { data, error } = await supabase.from(tableName).select('*');
        if (error) throw error;
        return { rows: data };
      }
    }
    
    // For complex queries, use RPC if available, otherwise fall back
    const { data, error } = await executeSQL(sql);
    if (error) throw error;
    return { rows: data || [] };
  } catch (error) {
    console.error('Query error:', error);
    throw error;
  }
}

module.exports = {
  supabase,
  query,
  executeSQL
};