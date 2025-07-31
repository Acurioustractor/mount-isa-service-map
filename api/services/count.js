import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET");
  res.setHeader("Content-Type", "application/json");
  
  try {
    const { count, error } = await supabase
      .from('services')
      .select('*', { count: 'exact', head: true })
      .eq('is_active', true);

    if (error) throw error;

    res.json({ count: count || 0 });
  } catch (err) {
    console.error('Error getting service count:', err);
    res.status(500).json({ error: 'Failed to get service count' });
  }
}