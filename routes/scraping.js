const express = require('express');
const axios = require('axios');
const db = require('../config/db');
const router = express.Router();

// Configuration for Python scraping system
const SCRAPING_API_BASE = process.env.SCRAPING_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get scraping system status and agent information
 */
router.get('/status', async (req, res) => {
  try {
    // Get agent performance stats
    const agentStatsResponse = await axios.get(`${SCRAPING_API_BASE}/agents/stats/performance`);
    
    // Get queue status
    const queueStatusResponse = await axios.get(`${SCRAPING_API_BASE}/agents/queue/status`);
    
    // Get discovery stats
    const discoveryStatsResponse = await axios.get(`${SCRAPING_API_BASE}/discovery/stats/performance`);
    
    // Get validation stats
    const validationStatsResponse = await axios.get(`${SCRAPING_API_BASE}/validation/stats/performance`);
    
    res.json({
      status: 'operational',
      agents: agentStatsResponse.data,
      queues: queueStatusResponse.data,
      discovery: discoveryStatsResponse.data,
      validation: validationStatsResponse.data,
      last_updated: new Date().toISOString()
    });
  } catch (error) {
    console.error('Failed to get scraping system status:', error.message);
    res.status(500).json({ 
      error: 'Failed to connect to scraping system',
      status: 'unavailable'
    });
  }
});

/**
 * Trigger discovery for a specific URL
 */
router.post('/discover', async (req, res) => {
  try {
    const { url, max_depth = 2 } = req.body;
    
    if (!url) {
      return res.status(400).json({ error: 'URL is required' });
    }
    
    // Submit discovery request to Python system
    const discoveryResponse = await axios.post(`${SCRAPING_API_BASE}/discovery/url`, {
      url: url,
      max_depth: max_depth,
      options: {
        follow_links: true,
        extract_contact: true,
        extract_location: true,
        min_confidence: 0.4
      }
    });
    
    res.json({
      message: 'Discovery task submitted',
      task_id: discoveryResponse.data.task_id,
      url: url,
      status: discoveryResponse.data.status
    });
  } catch (error) {
    console.error('Failed to submit discovery task:', error.message);
    res.status(500).json({ error: 'Failed to submit discovery task' });
  }
});

/**
 * Get discovery results and integrate discovered services
 */
router.get('/discover/:task_id', async (req, res) => {
  try {
    const { task_id } = req.params;
    
    // Get discovery result from Python system
    const discoveryResponse = await axios.get(`${SCRAPING_API_BASE}/discovery/url/${task_id}`);
    
    if (discoveryResponse.data.status === 'completed' && discoveryResponse.data.services) {
      // Process discovered services and add to main database
      const integratedServices = await integrateDiscoveredServices(discoveryResponse.data.services);
      
      return res.json({
        status: 'completed',
        task_id: task_id,
        services_found: discoveryResponse.data.services_found,
        services_integrated: integratedServices.length,
        services: integratedServices,
        processing_time: discoveryResponse.data.processing_time
      });
    }
    
    res.json(discoveryResponse.data);
  } catch (error) {
    console.error('Failed to get discovery result:', error.message);
    res.status(500).json({ error: 'Failed to get discovery result' });
  }
});

/**
 * Batch discovery for multiple URLs
 */
router.post('/discover/batch', async (req, res) => {
  try {
    const { urls, max_depth = 2 } = req.body;
    
    if (!Array.isArray(urls) || urls.length === 0) {
      return res.status(400).json({ error: 'URLs array is required' });
    }
    
    if (urls.length > 20) {
      return res.status(400).json({ error: 'Maximum 20 URLs allowed per batch' });
    }
    
    // Submit batch discovery to Python system
    const batchResponse = await axios.post(`${SCRAPING_API_BASE}/discovery/batch`, {
      urls: urls,
      max_depth: max_depth,
      options: {
        follow_links: true,
        extract_contact: true,
        extract_location: true,
        min_confidence: 0.4
      }
    });
    
    res.json({
      message: 'Batch discovery submitted',
      batch_id: batchResponse.data.batch_id,
      task_ids: batchResponse.data.task_ids,
      total_urls: batchResponse.data.total_urls
    });
  } catch (error) {
    console.error('Failed to submit batch discovery:', error.message);
    res.status(500).json({ error: 'Failed to submit batch discovery' });
  }
});

/**
 * Validate existing service data
 */
router.post('/validate/:service_id', async (req, res) => {
  try {
    const { service_id } = req.params;
    
    // Get service data from main database
    const serviceQuery = `
      SELECT s.*, c.name as category
      FROM services s
      LEFT JOIN service_categories c ON s.category_id = c.id
      WHERE s.id = $1
    `;
    
    const serviceResult = await db.query(serviceQuery, [service_id]);
    
    if (serviceResult.rows.length === 0) {
      return res.status(404).json({ error: 'Service not found' });
    }
    
    const service = serviceResult.rows[0];
    
    // Convert to format expected by validation system
    const serviceData = {
      name: service.name,
      description: service.description,
      phone: service.phone,
      email: service.email,
      website: service.website,
      address: service.address,
      suburb: service.suburb,
      postcode: service.postcode,
      state: service.state,
      category: service.category,
      operating_hours: service.service_hours,
      source_url: `${process.env.BASE_URL}/api/services/${service_id}`
    };
    
    // Submit validation request to Python system
    const validationResponse = await axios.post(`${SCRAPING_API_BASE}/validation/service`, {
      service_data: serviceData,
      options: {
        include_warnings: true,
        strict_mode: false,
        validate_urls: true,
        validate_phones: true,
        validate_emails: true,
        validate_addresses: true
      }
    });
    
    // Store validation result reference
    await storeValidationReference(service_id, validationResponse.data.task_id);
    
    res.json({
      message: 'Validation task submitted',
      service_id: service_id,
      task_id: validationResponse.data.task_id,
      status: validationResponse.data.status
    });
  } catch (error) {
    console.error('Failed to validate service:', error.message);
    res.status(500).json({ error: 'Failed to submit validation' });
  }
});

/**
 * Get validation results for a service
 */
router.get('/validate/:service_id/:task_id', async (req, res) => {
  try {
    const { service_id, task_id } = req.params;
    
    // Get validation result from Python system
    const validationResponse = await axios.get(`${SCRAPING_API_BASE}/validation/service/${task_id}`);
    
    if (validationResponse.data.status === 'completed' && validationResponse.data.summary) {
      // Update service validation status in main database
      await updateServiceValidationStatus(service_id, validationResponse.data.summary);
    }
    
    res.json({
      service_id: service_id,
      task_id: task_id,
      validation_result: validationResponse.data
    });
  } catch (error) {
    console.error('Failed to get validation result:', error.message);
    res.status(500).json({ error: 'Failed to get validation result' });
  }
});

/**
 * Get discovered services that need manual review
 */
router.get('/discovered/pending', async (req, res) => {
  try {
    const { limit = 20 } = req.query;
    
    // Get recent discoveries from Python system
    const discoveredResponse = await axios.get(`${SCRAPING_API_BASE}/discovery/recent?limit=${limit}`);
    
    // Get services from main database that need validation
    const pendingQuery = `
      SELECT s.*, c.name as category,
             sds.source_url, sds.last_scraped
      FROM services s
      LEFT JOIN service_categories c ON s.category_id = c.id
      LEFT JOIN service_data_sources sds ON s.id = sds.service_id
      WHERE s.updated_at > NOW() - INTERVAL '7 days'
        AND (s.validation_score IS NULL OR s.validation_score < 0.7)
      ORDER BY s.updated_at DESC
      LIMIT $1
    `;
    
    const pendingResult = await db.query(pendingQuery, [limit]);
    
    res.json({
      discovered_services: discoveredResponse.data.recent_discoveries || [],
      pending_validation: pendingResult.rows,
      total_pending: pendingResult.rows.length
    });
  } catch (error) {
    console.error('Failed to get pending services:', error.message);
    res.status(500).json({ error: 'Failed to get pending services' });
  }
});

/**
 * Approve discovered service for integration
 */
router.post('/approve/:discovered_service_id', async (req, res) => {
  try {
    const { discovered_service_id } = req.params;
    const { approved_data, reviewer_notes } = req.body;
    
    // Create service in main database with approved data
    const integratedService = await createServiceFromDiscovered(approved_data, reviewer_notes);
    
    res.json({
      message: 'Service approved and integrated',
      service_id: integratedService.id,
      discovered_service_id: discovered_service_id
    });
  } catch (error) {
    console.error('Failed to approve service:', error.message);
    res.status(500).json({ error: 'Failed to approve service' });
  }
});

/**
 * Get scraping system health and metrics
 */
router.get('/health', async (req, res) => {
  try {
    // Check system health
    const healthResponse = await axios.get(`${SCRAPING_API_BASE}/agents/health/check`);
    
    res.json({
      scraping_system: healthResponse.data,
      integration_status: 'operational',
      last_sync: new Date().toISOString()
    });
  } catch (error) {
    console.error('Scraping system health check failed:', error.message);
    res.status(503).json({ 
      scraping_system: { status: 'unavailable' },
      integration_status: 'degraded',
      error: 'Cannot connect to scraping system'
    });
  }
});

/**
 * Helper function to integrate discovered services into main database
 */
async function integrateDiscoveredServices(discoveredServices) {
  const integratedServices = [];
  
  for (const service of discoveredServices) {
    try {
      // Map service category
      const categoryId = await getCategoryId(service.category);
      
      // Check if service already exists
      const existingService = await findExistingService(service);
      
      if (existingService) {
        // Update existing service with new information
        await updateExistingService(existingService.id, service);
        integratedServices.push({ ...existingService, status: 'updated' });
      } else {
        // Create new service
        const newService = await createNewService(service, categoryId);
        integratedServices.push({ ...newService, status: 'created' });
      }
    } catch (error) {
      console.error('Failed to integrate service:', service.name, error.message);
    }
  }
  
  return integratedServices;
}

/**
 * Helper function to get or create category ID
 */
async function getCategoryId(categoryName) {
  if (!categoryName) return null;
  
  // Try to find existing category
  const categoryQuery = 'SELECT id FROM service_categories WHERE name ILIKE $1';
  const categoryResult = await db.query(categoryQuery, [categoryName]);
  
  if (categoryResult.rows.length > 0) {
    return categoryResult.rows[0].id;
  }
  
  // Create new category if not found
  const createCategoryQuery = `
    INSERT INTO service_categories (name, description)
    VALUES ($1, $2)
    RETURNING id
  `;
  
  const newCategoryResult = await db.query(createCategoryQuery, [
    categoryName,
    `Services in the ${categoryName} category`
  ]);
  
  return newCategoryResult.rows[0].id;
}

/**
 * Helper function to find existing service
 */
async function findExistingService(discoveredService) {
  const searchQuery = `
    SELECT * FROM services
    WHERE (name ILIKE $1 OR phone = $2 OR email = $3)
    AND is_active = true
    LIMIT 1
  `;
  
  const result = await db.query(searchQuery, [
    `%${discoveredService.name}%`,
    discoveredService.phone,
    discoveredService.email
  ]);
  
  return result.rows[0] || null;
}

/**
 * Helper function to create new service
 */
async function createNewService(service, categoryId) {
  const insertQuery = `
    INSERT INTO services (
      name, description, category_id, address, suburb, state, postcode,
      phone, email, website, is_active, validation_score, 
      extraction_method, confidence_score
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    RETURNING *
  `;
  
  const params = [
    service.name,
    service.description,
    categoryId,
    service.address,
    service.suburb || 'Mount Isa',
    service.state || 'QLD',
    service.postcode || '4825',
    service.phone,
    service.email,
    service.website,
    true, // is_active
    service.confidence_score,
    service.extraction_method,
    service.confidence_score
  ];
  
  const result = await db.query(insertQuery, params);
  
  // Also create data source record
  await createDataSourceRecord(result.rows[0].id, service.source_url);
  
  return result.rows[0];
}

/**
 * Helper function to update existing service
 */
async function updateExistingService(serviceId, discoveredService) {
  const updateQuery = `
    UPDATE services SET
      description = COALESCE($1, description),
      phone = COALESCE($2, phone),
      email = COALESCE($3, email),
      website = COALESCE($4, website),
      address = COALESCE($5, address),
      updated_at = CURRENT_TIMESTAMP
    WHERE id = $6
  `;
  
  await db.query(updateQuery, [
    discoveredService.description,
    discoveredService.phone,
    discoveredService.email,
    discoveredService.website,
    discoveredService.address,
    serviceId
  ]);
}

/**
 * Helper function to create data source record
 */
async function createDataSourceRecord(serviceId, sourceUrl) {
  const insertQuery = `
    INSERT INTO service_data_sources (service_id, source_url, last_scraped)
    VALUES ($1, $2, CURRENT_TIMESTAMP)
    ON CONFLICT (service_id, source_url) DO UPDATE SET
      last_scraped = CURRENT_TIMESTAMP
  `;
  
  await db.query(insertQuery, [serviceId, sourceUrl]);
}

/**
 * Helper function to store validation reference
 */
async function storeValidationReference(serviceId, taskId) {
  const insertQuery = `
    INSERT INTO service_validations (service_id, task_id, created_at)
    VALUES ($1, $2, CURRENT_TIMESTAMP)
  `;
  
  await db.query(insertQuery, [serviceId, taskId]);
}

/**
 * Helper function to update service validation status
 */
async function updateServiceValidationStatus(serviceId, validationSummary) {
  const updateQuery = `
    UPDATE services SET
      validation_score = $1,
      validation_notes = $2,
      last_validated = CURRENT_TIMESTAMP
    WHERE id = $3
  `;
  
  const notes = JSON.stringify({
    overall_score: validationSummary.overall_score,
    total_checks: validationSummary.total_checks,
    passed: validationSummary.passed,
    failed: validationSummary.failed,
    warnings: validationSummary.warnings,
    critical_issues: validationSummary.critical_issues.length,
    recommendations: validationSummary.recommendations
  });
  
  await db.query(updateQuery, [
    validationSummary.overall_score,
    notes,
    serviceId
  ]);
}

/**
 * Helper function to create service from approved discovered data
 */
async function createServiceFromDiscovered(approvedData, reviewerNotes) {
  const categoryId = await getCategoryId(approvedData.category);
  
  const insertQuery = `
    INSERT INTO services (
      name, description, category_id, address, suburb, state, postcode,
      phone, email, website, service_hours, is_active, 
      reviewer_notes, approved_at
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, CURRENT_TIMESTAMP)
    RETURNING *
  `;
  
  const params = [
    approvedData.name,
    approvedData.description,
    categoryId,
    approvedData.address,
    approvedData.suburb || 'Mount Isa',
    approvedData.state || 'QLD',
    approvedData.postcode || '4825',
    approvedData.phone,
    approvedData.email,
    approvedData.website,
    approvedData.operating_hours,
    true,
    reviewerNotes
  ];
  
  const result = await db.query(insertQuery, params);
  return result.rows[0];
}

module.exports = router;