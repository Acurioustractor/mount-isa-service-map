const { createClient } = require('@supabase/supabase-js');

module.exports = (req, res) => {
  try {
    const supabaseUrl = process.env.SUPABASE_URL || 'https://awdckiwhptjivpzkxekq.supabase.co';
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 'sb_secret_fjzuYiIh7LPTGoT9kUgDIg_5bzdvPRo';
    
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    // Test query
    supabase
      .from('services')
      .select('id, name')
      .limit(3)
      .then(({ data, error }) => {
        if (error) {
          res.status(500).json({ 
            error: 'Supabase query failed', 
            details: error.message,
            url: supabaseUrl 
          });
        } else {
          res.json({ 
            message: 'Supabase working!', 
            services_count: data?.length || 0,
            sample_services: data || [],
            url: supabaseUrl
          });
        }
      })
      .catch(err => {
        res.status(500).json({ 
          error: 'Supabase connection failed', 
          details: err.message 
        });
      });
      
  } catch (error) {
    res.status(500).json({ 
      error: 'Server error', 
      details: error.message 
    });
  }
};