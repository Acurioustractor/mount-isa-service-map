import { createClient } from '@supabase/supabase-js';

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET");
  res.setHeader("Content-Type", "application/json");
  
  try {
    // Debug environment variables first
    console.log('Environment check:', {
      hasUrl: !!process.env.SUPABASE_URL,
      hasKey: !!process.env.SUPABASE_ANON_KEY,
      url: process.env.SUPABASE_URL,
      keyLength: process.env.SUPABASE_ANON_KEY ? process.env.SUPABASE_ANON_KEY.length : 0
    });

    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
      throw new Error('Missing Supabase environment variables');
    }

    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_ANON_KEY
    );

    console.log('Supabase client created, fetching services...');

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

    console.log('Supabase response:', { 
      error: error, 
      serviceCount: services ? services.length : 0 
    });

    if (error) {
      console.error('Supabase error:', error);
      throw error;
    }

    if (!services || services.length === 0) {
      throw new Error('No services returned from database');
    }

    // Format the results
    const formattedServices = services.map(service => ({
      ...service,
      category: service.service_categories?.name || 'Community Support'
    }));

    console.log(`Successfully returning ${formattedServices.length} services`);
    res.json(formattedServices);
    
  } catch (err) {
    console.error('API Error:', err);
    res.status(500).json({ 
      error: 'Failed to fetch services from Supabase',
      details: err.message,
      hasUrl: !!process.env.SUPABASE_URL,
      hasKey: !!process.env.SUPABASE_ANON_KEY
    });
  }
}