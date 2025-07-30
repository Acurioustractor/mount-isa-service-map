const { createClient } = require('@supabase/supabase-js');

module.exports = async (req, res) => {
  try {
    const supabaseUrl = process.env.SUPABASE_URL || 'https://awdckiwhptjivpzkxekq.supabase.co';
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 'sb_secret_fjzuYiIh7LPTGoT9kUgDIg_5bzdvPRo';
    
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    const { category, suburb, active = true, search, limit = 50 } = req.query;
    
    // Build query
    let query = supabase
      .from('services')
      .select(`
        id,
        name,
        description,
        address,
        suburb,
        postcode,
        state,
        phone,
        email,
        website,
        created_at,
        updated_at,
        service_categories!category_id(name)
      `);
    
    // Apply filters
    if (active !== undefined) {
      query = query.eq('is_active', active === 'true' || active === true);
    }
    
    if (search) {
      query = query.or(`name.ilike.%${search}%,description.ilike.%${search}%,suburb.ilike.%${search}%`);
    }
    
    if (suburb) {
      query = query.ilike('suburb', `%${suburb}%`);
    }
    
    // Apply limit
    query = query.limit(parseInt(limit));
    
    // Order by updated_at
    query = query.order('updated_at', { ascending: false });
    
    const { data, error } = await query;
    
    if (error) {
      throw error;
    }
    
    // Transform data to match expected format
    const transformedData = data.map(service => ({
      ...service,
      category: service.service_categories?.name || 'Community Support',
      confidence_score: 0.95,
      data_source: 'Mount Isa Community Database'
    }));
    
    res.json(transformedData);
    
  } catch (error) {
    console.error('Error fetching services:', error);
    res.status(500).json({ 
      error: 'Internal server error', 
      details: error.message 
    });
  }
};