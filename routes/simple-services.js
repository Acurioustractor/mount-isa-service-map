const express = require('express');
const { supabase } = require('../config/supabase');
const router = express.Router();

// Get all services - simple version
router.get('/', async (req, res) => {
    try {
        const { limit = 500 } = req.query;
        
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
            .limit(parseInt(limit))
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

        console.log(`Returning ${formattedServices.length} services`);
        res.json(formattedServices);
        
    } catch (err) {
        console.error('Error fetching services:', err);
        res.status(500).json({ 
            error: 'Failed to fetch services',
            details: err.message 
        });
    }
});

// Get service count
router.get('/count', async (req, res) => {
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
});

module.exports = router;