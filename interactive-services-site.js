/**
 * INTERACTIVE MOUNT ISA SERVICES SITE
 * Complete web interface displaying all 44 discovered services with search and filtering
 */

const express = require('express');
const { Pool } = require('pg');
const path = require('path');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 9000;

// Database connection
const db = new Pool({
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'mount_isa_services',
    user: process.env.DB_USER || 'benknight',
    port: process.env.DB_PORT || '5432'
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Serve the main interactive site
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API endpoint to get all services with filtering and search
app.get('/api/services', async (req, res) => {
    try {
        const { search, source, category, limit = 50 } = req.query;
        
        let query = `
            SELECT 
                id,
                name,
                description,
                phone,
                email,
                website,
                address,
                suburb,
                postcode,
                state,
                data_source,
                confidence_score,
                research_metadata,
                discovery_date,
                last_updated
            FROM services 
            WHERE 1=1
        `;
        
        const params = [];
        let paramCount = 0;

        // Add search filter
        if (search) {
            paramCount++;
            query += ` AND (
                name ILIKE $${paramCount} OR 
                description ILIKE $${paramCount} OR 
                address ILIKE $${paramCount}
            )`;
            params.push(`%${search}%`);
        }

        // Add source filter
        if (source) {
            paramCount++;
            query += ` AND data_source = $${paramCount}`;
            params.push(source);
        }

        // Add category filter (from metadata)
        if (category) {
            paramCount++;
            query += ` AND research_metadata->>'service_category' = $${paramCount}`;
            params.push(category);
        }

        query += ` ORDER BY confidence_score DESC, discovery_date DESC LIMIT $${++paramCount}`;
        params.push(limit);

        const result = await db.query(query, params);
        
        res.json({
            success: true,
            total: result.rows.length,
            services: result.rows.map(service => ({
                ...service,
                research_metadata: typeof service.research_metadata === 'string' 
                    ? JSON.parse(service.research_metadata) 
                    : service.research_metadata
            }))
        });

    } catch (error) {
        console.error('Error fetching services:', error);
        res.status(500).json({ 
            success: false, 
            error: 'Failed to fetch services' 
        });
    }
});

// API endpoint to get service statistics
app.get('/api/stats', async (req, res) => {
    try {
        const totalQuery = 'SELECT COUNT(*) as total FROM services';
        const sourceStatsQuery = `
            SELECT 
                data_source,
                COUNT(*) as count,
                AVG(confidence_score) as avg_confidence
            FROM services 
            GROUP BY data_source 
            ORDER BY count DESC
        `;
        const categoryStatsQuery = `
            SELECT 
                research_metadata->>'service_category' as category,
                COUNT(*) as count
            FROM services 
            WHERE research_metadata->>'service_category' IS NOT NULL
            GROUP BY research_metadata->>'service_category'
            ORDER BY count DESC
        `;

        const [totalResult, sourceResult, categoryResult] = await Promise.all([
            db.query(totalQuery),
            db.query(sourceStatsQuery),
            db.query(categoryStatsQuery)
        ]);

        res.json({
            success: true,
            stats: {
                total_services: parseInt(totalResult.rows[0].total),
                by_source: sourceResult.rows.map(row => ({
                    source: row.data_source,
                    count: parseInt(row.count),
                    avg_confidence: parseFloat(row.avg_confidence).toFixed(2)
                })),
                by_category: categoryResult.rows.map(row => ({
                    category: row.category || 'general',
                    count: parseInt(row.count)
                }))
            }
        });

    } catch (error) {
        console.error('Error fetching stats:', error);
        res.status(500).json({ 
            success: false, 
            error: 'Failed to fetch statistics' 
        });
    }
});

// API endpoint to get a specific service
app.get('/api/services/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const query = 'SELECT * FROM services WHERE id = $1';
        const result = await db.query(query, [id]);

        if (result.rows.length === 0) {
            return res.status(404).json({ 
                success: false, 
                error: 'Service not found' 
            });
        }

        const service = result.rows[0];
        res.json({
            success: true,
            service: {
                ...service,
                research_metadata: typeof service.research_metadata === 'string' 
                    ? JSON.parse(service.research_metadata) 
                    : service.research_metadata
            }
        });

    } catch (error) {
        console.error('Error fetching service:', error);
        res.status(500).json({ 
            success: false, 
            error: 'Failed to fetch service' 
        });
    }
});

// API endpoint to get available filters
app.get('/api/filters', async (req, res) => {
    try {
        const sourcesQuery = 'SELECT DISTINCT data_source FROM services ORDER BY data_source';
        const categoriesQuery = `
            SELECT DISTINCT research_metadata->>'service_category' as category 
            FROM services 
            WHERE research_metadata->>'service_category' IS NOT NULL 
            ORDER BY category
        `;

        const [sourcesResult, categoriesResult] = await Promise.all([
            db.query(sourcesQuery),
            db.query(categoriesQuery)
        ]);

        res.json({
            success: true,
            filters: {
                sources: sourcesResult.rows.map(row => row.data_source),
                categories: categoriesResult.rows.map(row => row.category)
            }
        });

    } catch (error) {
        console.error('Error fetching filters:', error);
        res.status(500).json({ 
            success: false, 
            error: 'Failed to fetch filters' 
        });
    }
});

// Start the server
app.listen(port, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║              🌐 INTERACTIVE MOUNT ISA SERVICES SITE 🌐                      ║
║                                                                               ║
║  Displaying all 44 discovered services with interactive database             ║
╚═══════════════════════════════════════════════════════════════════════════════╝

🚀 Server running at: http://localhost:${port}
📊 Database connected: ${db.options.database}
🎯 Features available:
   • Search and filter 44 Mount Isa services
   • Browse by source (Government, HealthInfoNet, etc.)
   • Filter by category (Health, Community, Indigenous, etc.)
   • View detailed service information
   • Real-time statistics and analytics
   • Mobile-responsive interface

🌟 Ready to explore all discovered services!
    `);
});

module.exports = app;