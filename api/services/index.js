import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET");
  res.setHeader("Content-Type", "application/json");
  
  try {
    const { data: services, error } = await supabase
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
        is_active,
        service_categories(name)
      `)
      .eq('is_active', true)
      .limit(500)
      .order('name');

    if (error) {
      console.error('Supabase error:', error);
      throw error;
    }

    // Format the results
    const formattedServices = (services || []).map(service => ({
      ...service,
      category: service.service_categories?.name || 'Community Support'
    }));

    res.json(formattedServices);
    
  } catch (err) {
    console.error('Error fetching services:', err);
    res.status(500).json({ 
      error: 'Failed to fetch services',
      details: err.message 
    });
  }
}