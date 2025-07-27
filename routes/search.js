const express = require('express');
const db = require('../config/db');
const router = express.Router();

// Search services by keyword
router.get('/', async (req, res) => {
  try {
    const { q, category, suburb } = req.query;
    
    if (!q) {
      return res.status(400).json({ error: 'Search query parameter "q" is required' });
    }
    
    let query = `
      SELECT 
        s.id,
        s.name,
        s.description,
        s.address,
        s.suburb,
        s.phone,
        s.email,
        s.website,
        c.name as category,
        s.last_updated,
        -- Calculate relevance score
        ts_rank(to_tsvector('english', s.name || ' ' || COALESCE(s.description, '')), 
                plainto_tsquery('english', $1)) as relevance
      FROM services s
      LEFT JOIN service_categories c ON s.category_id = c.id
      WHERE s.is_active = true
        AND to_tsvector('english', s.name || ' ' || COALESCE(s.description, '')) 
            @@ plainto_tsquery('english', $1)
    `;
    
    const params = [q];
    
    if (category) {
      params.push(category);
      query += ` AND c.name = $${params.length}`;
    }
    
    if (suburb) {
      params.push(suburb);
      query += ` AND s.suburb = $${params.length}`;
    }
    
    query += ' ORDER BY relevance DESC, s.name';
    
    const result = await db.query(query, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to search services' });
  }
});

// Advanced search with filters
router.post('/advanced', async (req, res) => {
  try {
    const {
      keywords,
      category_id,
      suburbs,
      service_types,
      has_availability,
      is_wheelchair_accessible
    } = req.body;
    
    let query = `
      SELECT 
        s.id,
        s.name,
        s.description,
        s.address,
        s.suburb,
        s.phone,
        s.email,
        s.website,
        c.name as category,
        s.last_updated
      FROM services s
      LEFT JOIN service_categories c ON s.category_id = c.id
      WHERE s.is_active = true
    `;
    
    const params = [];
    
    if (keywords) {
      params.push(keywords);
      query += ` AND (s.name ILIKE $${params.length} OR s.description ILIKE $${params.length})`;
    }
    
    if (category_id) {
      params.push(category_id);
      query += ` AND s.category_id = $${params.length}`;
    }
    
    if (suburbs && suburbs.length > 0) {
      params.push(suburbs);
      query += ` AND s.suburb = ANY($${params.length})`;
    }
    
    // Note: These fields would need to be added to the schema
    // if (has_availability !== undefined) {
    //   params.push(has_availability);
    //   query += ` AND s.has_availability = $${params.length}`;
    // }
    
    query += ' ORDER BY s.name';
    
    const result = await db.query(query, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to perform advanced search' });
  }
});

module.exports = router;
