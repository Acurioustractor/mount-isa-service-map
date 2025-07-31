import { createClient } from '@supabase/supabase-js';

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET");
  res.setHeader("Content-Type", "application/json");
  
  try {
    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
      throw new Error('Missing Supabase environment variables');
    }

    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_ANON_KEY
    );

    const { count, error } = await supabase
      .from('services')
      .select('*', { count: 'exact', head: true })
      .eq('is_active', true);

    if (error) {
      console.error('Supabase count error:', error);
      throw error;
    }

    console.log(`Service count from Supabase: ${count}`);
    res.json({ count: count || 0 });
    
  } catch (err) {
    console.error('Count API Error:', err);
    res.status(500).json({ 
      error: 'Failed to get service count from Supabase',
      details: err.message 
    });
  }
}