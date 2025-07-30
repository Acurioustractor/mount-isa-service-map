const express = require('express');
const { supabase } = require('../config/supabase');
const router = express.Router();

// Get all services with Supabase
router.get('/', async (req, res) => {
    try {
        const { category, suburb, active = true, source, search, limit = 50 } = req.query;
        
        // Build Supabase query
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
        
        if (category) {
            // Filter by category name through the relationship
            query = query.eq('service_categories.name', category);
        }
        
        // Apply limit
        if (limit) {
            query = query.limit(parseInt(limit));
        }
        
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
            confidence_score: 0.95, // Default confidence for imported data
            data_source: 'Mount Isa Community Database'
        }));
        
        res.json(transformedData);
    } catch (error) {
        console.error('Error fetching services:', error);
        res.status(500).json({ error: 'Internal server error', details: error.message });
    }
});

// Get single service by ID
router.get('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        
        const { data, error } = await supabase
            .from('services')
            .select(`
                *,
                service_categories!category_id(name, description)
            `)
            .eq('id', id)
            .single();
        
        if (error) {
            if (error.code === 'PGRST116') {
                return res.status(404).json({ error: 'Service not found' });
            }
            throw error;
        }
        
        // Transform data
        const transformedService = {
            ...data,
            category: data.service_categories?.name || 'Community Support',
            category_description: data.service_categories?.description,
            confidence_score: 0.95,
            data_source: 'Mount Isa Community Database'
        };
        
        res.json(transformedService);
    } catch (error) {
        console.error('Error fetching service:', error);
        res.status(500).json({ error: 'Internal server error', details: error.message });
    }
});

// Get service statistics
router.get('/stats/overview', async (req, res) => {
    try {
        // Get total services count
        const { data: services, error: servicesError } = await supabase
            .from('services')
            .select('id', { count: 'exact', head: true })
            .eq('is_active', true);
            
        // Get categories count
        const { data: categories, error: categoriesError } = await supabase
            .from('service_categories')
            .select('id', { count: 'exact', head: true })
            .eq('is_active', true);
        
        if (servicesError || categoriesError) {
            throw servicesError || categoriesError;
        }
        
        // Get services grouped by category
        const { data: categoryStats, error: categoryStatsError } = await supabase
            .from('services')
            .select(`
                service_categories!category_id(name),
                count
            `, { count: 'exact' })
            .eq('is_active', true);
        
        const stats = {
            total_services: services?.length || 0,
            total_categories: categories?.length || 0,
            services_by_category: categoryStats || []
        };
        
        res.json(stats);
    } catch (error) {
        console.error('Error fetching stats:', error);
        res.status(500).json({ error: 'Internal server error', details: error.message });
    }
});

module.exports = router;