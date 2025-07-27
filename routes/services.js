const express = require('express');
const db = require('../config/db');
const router = express.Router();

// Get all services with optional filtering
router.get('/', async (req, res) => {
  try {
    const { category, suburb, active = true } = req.query;
    
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
    
    if (suburb) {
      params.push(suburb);
      query += ` AND s.suburb = $${params.length}`;
    }
    
    query += ' ORDER BY s.name';
    
    const result = await db.query(query, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch services' });
  }
});

// Get service by ID
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const query = `
      SELECT 
        s.*,
        c.name as category,
        sl.address as location_address,
        sl.suburb as location_suburb,
        sc.name as contact_name,
        sc.title as contact_title,
        sc.phone as contact_phone,
        sc.email as contact_email
      FROM services s
      LEFT JOIN service_categories c ON s.category_id = c.id
      LEFT JOIN service_locations sl ON s.id = sl.service_id
      LEFT JOIN service_contacts sc ON s.id = sc.service_id
      WHERE s.id = $1 AND s.is_active = true
    `;
    
    const result = await db.query(query, [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Service not found' });
    }
    
    // Process the flattened results in a single pass using Maps for efficient deduplication
    const serviceData = result.rows[0];
    const locations = new Map();
    const contacts = new Map();
    
    result.rows.forEach(row => {
      if (row.location_address && !locations.has(row.location_address)) {
        locations.set(row.location_address, {
          address: row.location_address,
          suburb: row.location_suburb
        });
      }
      
      if (row.contact_name && !contacts.has(row.contact_name)) {
        contacts.set(row.contact_name, {
          name: row.contact_name,
          title: row.contact_title,
          phone: row.contact_phone,
          email: row.contact_email
        });
      }
    });
    
    const service = {
      ...serviceData,
      locations: Array.from(locations.values()),
      contacts: Array.from(contacts.values())
    };
    
    delete service.location_address;
    delete service.location_suburb;
    delete service.contact_name;
    delete service.contact_title;
    delete service.contact_phone;
    delete service.contact_email;
    
    res.json(service);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch service' });
  }
});

// Create a new service (admin only)
router.post('/', async (req, res) => {
  try {
    // This would require authentication in a full implementation
    const {
      name,
      description,
      category_id,
      address,
      suburb,
      state,
      postcode,
      latitude,
      longitude,
      phone,
      email,
      website,
      eligibility_criteria,
      service_hours,
      availability,
      cost,
      referral_required
    } = req.body;
    
    const query = `
      INSERT INTO services (
        name, description, category_id, address, suburb, state, postcode,
        latitude, longitude, phone, email, website, eligibility_criteria,
        service_hours, availability, cost, referral_required
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
      RETURNING id, name
    `;
    
    const params = [
      name, description, category_id, address, suburb, state, postcode,
      latitude, longitude, phone, email, website, eligibility_criteria,
      service_hours, availability, cost, referral_required
    ];
    
    const result = await db.query(query, params);
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to create service' });
  }
});

// Update a service (admin only)
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const {
      name,
      description,
      category_id,
      address,
      suburb,
      state,
      postcode,
      latitude,
      longitude,
      phone,
      email,
      website,
      eligibility_criteria,
      service_hours,
      availability,
      cost,
      referral_required,
      is_active
    } = req.body;
    
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
        eligibility_criteria = $13,
        service_hours = $14,
        availability = $15,
        cost = $16,
        referral_required = $17,
        is_active = $18,
        updated_at = CURRENT_TIMESTAMP
      WHERE id = $19
      RETURNING id, name
    `;
    
    const params = [
      name, description, category_id, address, suburb, state, postcode,
      latitude, longitude, phone, email, website, eligibility_criteria,
      service_hours, availability, cost, referral_required, is_active, id
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

module.exports = router;
