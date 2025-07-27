const express = require('express');
const db = require('../config/db');
const router = express.Router();

// Middleware to check if user is admin (simplified for now)
const isAdmin = (req, res, next) => {
  // In a real implementation, this would check a JWT token or session
  // For now, we'll just check a header
  const authHeader = req.headers['authorization'];
  if (authHeader === 'Bearer admin-token') {
    next();
  } else {
    res.status(403).json({ error: 'Access denied. Admin privileges required.' });
  }
};

// Apply admin middleware to all routes in this router
router.use(isAdmin);

// Get all services (admin view with more details)
router.get('/services', async (req, res) => {
  try {
    const { active, category } = req.query;
    
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
        s.is_active,
        s.last_updated,
        COUNT(sl.id) as location_count,
        COUNT(sc.id) as contact_count
      FROM services s
      LEFT JOIN service_categories c ON s.category_id = c.id
      LEFT JOIN service_locations sl ON s.id = sl.service_id
      LEFT JOIN service_contacts sc ON s.id = sc.service_id
      WHERE 1=1
    `;
    
    const params = [];
    
    if (active !== undefined) {
      params.push(active === 'true' || active === true);
      query += ` AND s.is_active = $${params.length}`;
    }
    
    if (category) {
      params.push(category);
      query += ` AND c.name = $${params.length}`;
    }
    
    query += ' GROUP BY s.id, c.name ORDER BY s.name';
    
    const result = await db.query(query, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch services' });
  }
});

// Create a new service
router.post('/services', async (req, res) => {
  try {
    const serviceData = req.body;
    
    const query = `
      INSERT INTO services (
        name, description, category_id, address, suburb, state, postcode,
        latitude, longitude, phone, email, website, facebook, twitter, instagram,
        eligibility_criteria, service_hours, availability, cost, referral_required
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
      RETURNING id, name
    `;
    
    const params = [
      serviceData.name,
      serviceData.description,
      serviceData.category_id,
      serviceData.address,
      serviceData.suburb,
      serviceData.state || 'QLD',
      serviceData.postcode,
      serviceData.latitude,
      serviceData.longitude,
      serviceData.phone,
      serviceData.email,
      serviceData.website,
      serviceData.facebook,
      serviceData.twitter,
      serviceData.instagram,
      serviceData.eligibility_criteria,
      serviceData.service_hours,
      serviceData.availability,
      serviceData.cost,
      serviceData.referral_required || false
    ];
    
    const result = await db.query(query, params);
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to create service' });
  }
});

// Update a service
router.put('/services/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const serviceData = req.body;
    
    const query = `
      UPDATE services SET
        name = $1,
        description = $2,
        category_id = $3,
        address = $4,
        suburb = $5,
        state = $6,
        postcode = $7,
        latitude = $8,
        longitude = $9,
        phone = $10,
        email = $11,
        website = $12,
        facebook = $13,
        twitter = $14,
        instagram = $15,
        eligibility_criteria = $16,
        service_hours = $17,
        availability = $18,
        cost = $19,
        referral_required = $20,
        is_active = $21,
        updated_at = CURRENT_TIMESTAMP
      WHERE id = $22
      RETURNING id, name
    `;
    
    const params = [
      serviceData.name,
      serviceData.description,
      serviceData.category_id,
      serviceData.address,
      serviceData.suburb,
      serviceData.state || 'QLD',
      serviceData.postcode,
      serviceData.latitude,
      serviceData.longitude,
      serviceData.phone,
      serviceData.email,
      serviceData.website,
      serviceData.facebook,
      serviceData.twitter,
      serviceData.instagram,
      serviceData.eligibility_criteria,
      serviceData.service_hours,
      serviceData.availability,
      serviceData.cost,
      serviceData.referral_required || false,
      serviceData.is_active !== undefined ? serviceData.is_active : true,
      id
    ];
    
    const result = await db.query(query, params);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Service not found' });
    }
    
    res.json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to update service' });
  }
});

// Delete a service (soft delete)
router.delete('/services/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const query = `
      UPDATE services 
      SET is_active = false, updated_at = CURRENT_TIMESTAMP
      WHERE id = $1
      RETURNING id, name
    `;
    
    const result = await db.query(query, [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Service not found' });
    }
    
    res.json({ message: 'Service deactivated successfully', service: result.rows[0] });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to delete service' });
  }
});

// Get audit logs
router.get('/audit-logs', async (req, res) => {
  try {
    const { limit = 50, offset = 0 } = req.query;
    
    const query = `
      SELECT 
        al.id,
        al.table_name,
        al.record_id,
        al.action,
        al.old_values,
        al.new_values,
        au.username,
        al.created_at
      FROM audit_logs al
      LEFT JOIN admin_users au ON al.user_id = au.id
      ORDER BY al.created_at DESC
      LIMIT $1 OFFSET $2
    `;
    
    const result = await db.query(query, [parseInt(limit), parseInt(offset)]);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch audit logs' });
  }
});

// Get data sources
router.get('/data-sources', async (req, res) => {
  try {
    const query = `
      SELECT 
        id,
        name,
        description,
        url,
        is_active,
        created_at
      FROM data_sources
      ORDER BY name
    `;
    
    const result = await db.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch data sources' });
  }
});

module.exports = router;
