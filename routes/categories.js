const express = require('express');
const db = require('../config/db');
const router = express.Router();

// Get all categories
router.get('/', async (req, res) => {
  try {
    const query = `
      SELECT 
        id,
        name,
        description,
        is_active,
        created_at
      FROM service_categories
      WHERE is_active = true
      ORDER BY name
    `;
    
    const result = await db.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch categories' });
  }
});

// Get category by ID
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const query = `
      SELECT 
        id,
        name,
        description,
        is_active,
        created_at
      FROM service_categories
      WHERE id = $1 AND is_active = true
    `;
    
    const result = await db.query(query, [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Category not found' });
    }
    
    res.json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch category' });
  }
});

// Get services by category
router.get('/:id/services', async (req, res) => {
  try {
    const { id } = req.params;
    
    // First check if category exists
    const categoryQuery = 'SELECT id FROM service_categories WHERE id = $1 AND is_active = true';
    const categoryResult = await db.query(categoryQuery, [id]);
    
    if (categoryResult.rows.length === 0) {
      return res.status(404).json({ error: 'Category not found' });
    }
    
    // Get services in this category
    const servicesQuery = `
      SELECT 
        s.id,
        s.name,
        s.description,
        s.address,
        s.suburb,
        s.phone,
        s.email,
        s.website,
        s.last_updated
      FROM services s
      WHERE s.category_id = $1 AND s.is_active = true
      ORDER BY s.name
    `;
    
    const servicesResult = await db.query(servicesQuery, [id]);
    res.json(servicesResult.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch services for category' });
  }
});

module.exports = router;
