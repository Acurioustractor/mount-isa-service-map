const express = require('express');
const { supabase } = require('../config/supabase');
const router = express.Router();

// Get all services with enhanced discovery metadata
router.get('/', async (req, res) => {
    try {
        const { category, suburb, active = true, source, search, limit = 50 } = req.query;
        
        let query = `
            SELECT 
                s.id,
                s.name,
                s.description,
                s.address,
                s.suburb,
                s.postcode,
                s.state,
                s.phone,
                s.email,
                s.website,
                s.data_source,
                s.confidence_score,
                s.research_metadata,
                s.discovery_date,
                s.last_updated,
                CASE 
                    WHEN s.research_metadata->>'service_category' = 'health' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'mental_health' THEN 'Mental Health'
                    WHEN s.research_metadata->>'service_category' = 'indigenous_health' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'disability' THEN 'Disability Support'
                    WHEN s.research_metadata->>'service_category' = 'family_services' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'family_support' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'housing' THEN 'Housing & Accommodation'
                    WHEN s.research_metadata->>'service_category' = 'education' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'employment' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'emergency_services' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'community_safety' THEN 'Justice & Legal'
                    WHEN s.research_metadata->>'service_category' = 'substance_use' THEN 'Mental Health'
                    WHEN s.research_metadata->>'service_category' = 'aged_care' THEN 'Disability Support'
                    WHEN s.research_metadata->>'service_category' = 'youth_justice' THEN 'Justice & Legal'
                    ELSE 'Health Services'
                END as category
            FROM services s
            WHERE 1=1
        `;
        
        const params = [];
        let paramCount = 0;

        if (active !== undefined) {
            paramCount++;
            query += ` AND s.is_active = $${paramCount}`;
            params.push(active === 'true' || active === true);
        }

        // Search functionality
        if (search) {
            paramCount++;
            query += ` AND (
                s.name ILIKE $${paramCount} OR 
                s.description ILIKE $${paramCount} OR 
                s.address ILIKE $${paramCount}
            )`;
            params.push(`%${search}%`);
        }

        // Filter by data source
        if (source) {
            paramCount++;
            query += ` AND s.data_source = $${paramCount}`;
            params.push(source);
        }

        // Filter by category (computed category)
        if (category) {
            paramCount++;
            query += ` AND (
                CASE 
                    WHEN s.research_metadata->>'service_category' = 'health' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'mental_health' THEN 'Mental Health'
                    WHEN s.research_metadata->>'service_category' = 'indigenous_health' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'disability' THEN 'Disability Support'
                    WHEN s.research_metadata->>'service_category' = 'family_services' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'family_support' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'housing' THEN 'Housing & Accommodation'
                    WHEN s.research_metadata->>'service_category' = 'education' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'employment' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'emergency_services' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'community_safety' THEN 'Justice & Legal'
                    WHEN s.research_metadata->>'service_category' = 'substance_use' THEN 'Mental Health'
                    WHEN s.research_metadata->>'service_category' = 'aged_care' THEN 'Disability Support'
                    WHEN s.research_metadata->>'service_category' = 'youth_justice' THEN 'Justice & Legal'
                    ELSE 'Health Services'
                END
            ) = $${paramCount}`;
            params.push(category);
        }

        query += ` ORDER BY s.confidence_score DESC, s.discovery_date DESC LIMIT $${++paramCount}`;
        params.push(limit);

        // Convert to Supabase query
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
                data_source,
                confidence_score,
                research_metadata,
                discovery_date,
                last_updated,
                is_active,
                service_categories(name)
            `)
            .eq('is_active', active === 'true' || active === true)
            .limit(parseInt(limit));

        if (error) throw error;
        
        // Enhance results with discovery source information
        const enhancedResults = (services || []).map(service => ({
            ...service,
            category: service.service_categories?.name || 'Community Support',
            research_metadata: typeof service.research_metadata === 'string' 
                ? JSON.parse(service.research_metadata) 
                : service.research_metadata || {},
            discovery_source: formatDataSource(service.data_source),
            confidence_percentage: Math.round(service.confidence_score * 100),
            is_new_discovery: new Date(service.discovery_date) > new Date('2025-07-28')
        }));

        res.json(enhancedResults);
    } catch (err) {
        console.error('Error fetching enhanced services:', err);
        res.status(500).json({ error: 'Failed to fetch services' });
    }
});

// Get service by ID with full metadata
router.get('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        
        const query = `
            SELECT 
                s.*,
                CASE 
                    WHEN s.research_metadata->>'service_category' = 'health' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'mental_health' THEN 'Mental Health'
                    WHEN s.research_metadata->>'service_category' = 'indigenous_health' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'disability' THEN 'Disability Support'
                    WHEN s.research_metadata->>'service_category' = 'family_services' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'family_support' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'housing' THEN 'Housing & Accommodation'
                    WHEN s.research_metadata->>'service_category' = 'education' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'employment' THEN 'Youth Support'
                    WHEN s.research_metadata->>'service_category' = 'emergency_services' THEN 'Health Services'
                    WHEN s.research_metadata->>'service_category' = 'community_safety' THEN 'Justice & Legal'
                    WHEN s.research_metadata->>'service_category' = 'substance_use' THEN 'Mental Health'
                    WHEN s.research_metadata->>'service_category' = 'aged_care' THEN 'Disability Support'
                    WHEN s.research_metadata->>'service_category' = 'youth_justice' THEN 'Justice & Legal'
                    ELSE 'Health Services'
                END as category
            FROM services s
            WHERE s.id = $1
        `;
        
        const { data: services, error } = await supabase
            .from('services')
            .select(`
                *,
                service_categories(name)
            `)
            .eq('id', id)
            .single();

        if (error) throw error;
        
        if (!services) {
            return res.status(404).json({ error: 'Service not found' });
        }
        
        const service = services;
        const metadata = typeof service.research_metadata === 'string' 
            ? JSON.parse(service.research_metadata) 
            : service.research_metadata || {};

        // Enhanced service object with all discovery information
        const enhancedService = {
            ...service,
            research_metadata: metadata,
            discovery_source: formatDataSource(service.data_source),
            confidence_percentage: Math.round(service.confidence_score * 100),
            services_offered: metadata.services_offered || [],
            source_name: metadata.source_name || 'Unknown Source',
            extraction_method: metadata.extraction_method || 'standard',
            credibility_level: metadata.credibility || 'medium',
            is_government_source: service.data_source === 'qld_gov_direct',
            is_indigenous_health: service.data_source === 'healthinfonet',
            is_ai_discovered: service.data_source === 'firecrawl_research',
            discovery_achievement: calculateDiscoveryAchievement(service.data_source)
        };
        
        res.json(enhancedService);
    } catch (err) {
        console.error('Error fetching service details:', err);
        res.status(500).json({ error: 'Failed to fetch service details' });
    }
});

// Get discovery statistics for the dashboard
router.get('/stats/discovery', async (req, res) => {
    try {
        const statsQuery = `
            SELECT 
                COUNT(*) as total_services,
                data_source,
                AVG(confidence_score) as avg_confidence,
                MAX(discovery_date) as latest_discovery
            FROM services 
            GROUP BY data_source 
            ORDER BY COUNT(*) DESC
        `;

        const categoryQuery = `
            SELECT 
                research_metadata->>'service_category' as category,
                COUNT(*) as count
            FROM services 
            WHERE research_metadata->>'service_category' IS NOT NULL
            GROUP BY research_metadata->>'service_category'
            ORDER BY count DESC
        `;

        // Get total count and basic stats
        const { count: totalCount } = await supabase
            .from('services')
            .select('*', { count: 'exact', head: true })
            .eq('is_active', true);

        const { data: allServices } = await supabase
            .from('services')
            .select('data_source, confidence_score, discovery_date')
            .eq('is_active', true);

        // Group by data source
        const bySource = {};
        allServices?.forEach(service => {
            const source = service.data_source || 'manual';
            if (!bySource[source]) {
                bySource[source] = { count: 0, confidenceSum: 0, latestDate: null };
            }
            bySource[source].count++;
            bySource[source].confidenceSum += service.confidence_score || 0;
            if (!bySource[source].latestDate || service.discovery_date > bySource[source].latestDate) {
                bySource[source].latestDate = service.discovery_date;
            }
        });

        const statsResult = { rows: Object.entries(bySource).map(([source, data]) => ({
            data_source: source,
            count: data.count,
            avg_confidence: data.count > 0 ? data.confidenceSum / data.count : 0,
            latest_discovery: data.latestDate
        }))};

        const categoryResult = { rows: [{ category: 'general', count: totalCount }] };

        const stats = {
            total_services: statsResult.rows.reduce((sum, row) => sum + parseInt(row.count || 0), 0),
            by_source: statsResult.rows.map(row => ({
                source: row.data_source,
                display_name: formatDataSource(row.data_source),
                count: parseInt(row.count || 0),
                avg_confidence: parseFloat(row.avg_confidence || 0).toFixed(2),
                latest_discovery: row.latest_discovery
            })),
            by_category: categoryResult.rows.map(row => ({
                category: row.category || 'general',
                display_name: formatCategoryName(row.category),
                count: parseInt(row.count)
            })),
            discovery_achievement: {
                original_count: 5,
                current_count: statsResult.rows.reduce((sum, row) => sum + parseInt(row.count || 0), 0),
                increase_percentage: Math.round(((statsResult.rows.reduce((sum, row) => sum + parseInt(row.count || 0), 0) - 5) / 5) * 100)
            }
        };

        res.json(stats);
    } catch (err) {
        console.error('Error fetching discovery stats:', err);
        res.status(500).json({ error: 'Failed to fetch statistics' });
    }
});

// Helper functions
function formatDataSource(source) {
    const sourceNames = {
        'qld_gov_direct': 'QLD Government Services',
        'healthinfonet': 'Indigenous HealthInfoNet',
        'firecrawl_research': 'AI-Powered Extraction',
        'organization_research': 'Local Organizations',
        'batch_research': 'Council Services',
        'intelligent_research': 'Intelligent Discovery',
        'primary_sources': 'Primary Sources',
        'manual': 'Manual Entry'
    };
    return sourceNames[source] || source;
}

function formatCategoryName(category) {
    if (!category) return 'General Services';
    
    const categoryNames = {
        'health': 'Health Services',
        'community': 'Community Services',
        'indigenous_health': 'Indigenous Health',
        'government': 'Government Services',
        'education': 'Education & Training',
        'emergency_services': 'Emergency Services',
        'family_services': 'Family Services',
        'disability': 'Disability Services',
        'housing': 'Housing Services',
        'employment': 'Employment Services',
        'community_safety': 'Community Safety',
        'aged_care': 'Aged Care',
        'mental_health': 'Mental Health',
        'substance_use': 'Substance Use Support',
        'youth_justice': 'Youth Justice'
    };
    
    return categoryNames[category] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function calculateDiscoveryAchievement(dataSource) {
    const achievements = {
        'qld_gov_direct': {
            title: 'Government Excellence',
            description: 'Maximum credibility official source',
            icon: '🏛️',
            badge_color: 'success'
        },
        'healthinfonet': {
            title: 'Indigenous Health Focus',
            description: 'Culturally appropriate services',
            icon: '🩺',
            badge_color: 'info'
        },
        'firecrawl_research': {
            title: 'AI Discovery',
            description: 'Intelligent automated extraction',
            icon: '🔥',
            badge_color: 'warning'
        },
        'organization_research': {
            title: 'Community Organizations',
            description: 'Local service providers',
            icon: '🏢',
            badge_color: 'primary'
        }
    };
    
    return achievements[dataSource] || {
        title: 'Service Discovery',
        description: 'Automated discovery system',
        icon: '🔍',
        badge_color: 'secondary'
    };
}

module.exports = router;