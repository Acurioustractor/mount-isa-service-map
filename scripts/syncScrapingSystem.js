#!/usr/bin/env node

/**
 * Data Synchronization Script for Scraping System Integration
 * 
 * This script helps synchronize data between the Mount Isa Service Map
 * and the Python-based scraping system.
 */

const axios = require('axios');
const db = require('../config/db');

// Configuration
const SCRAPING_API_BASE = process.env.SCRAPING_API_URL || 'http://localhost:8000/api/v1';
const SYNC_BATCH_SIZE = 50;

/**
 * Main synchronization function
 */
async function main() {
    console.log('Starting scraping system synchronization...');
    
    try {
        // Check scraping system health
        await checkScrapingSystemHealth();
        
        // Sync services that need validation
        await syncPendingValidations();
        
        // Sync discovered services
        await syncDiscoveredServices();
        
        // Update agent monitoring data
        await updateAgentMonitoring();
        
        console.log('Synchronization completed successfully!');
    } catch (error) {
        console.error('Synchronization failed:', error.message);
        process.exit(1);
    }
}

/**
 * Check if the scraping system is healthy and accessible
 */
async function checkScrapingSystemHealth() {
    console.log('Checking scraping system health...');
    
    try {
        const response = await axios.get(`${SCRAPING_API_BASE}/agents/health/check`, {
            timeout: 10000
        });
        
        if (response.data.status === 'healthy') {
            console.log('✓ Scraping system is healthy');
        } else {
            console.warn('⚠ Scraping system reports degraded health:', response.data);
        }
    } catch (error) {
        throw new Error(`Scraping system health check failed: ${error.message}`);
    }
}

/**
 * Sync services that need validation
 */
async function syncPendingValidations() {
    console.log('Syncing pending validations...');
    
    try {
        // Get services that need validation from main database
        const pendingQuery = `
            SELECT s.id, s.name, s.description, s.phone, s.email, s.website,
                   s.address, s.suburb, s.postcode, s.state, c.name as category,
                   s.service_hours, s.updated_at
            FROM services s
            LEFT JOIN service_categories c ON s.category_id = c.id
            WHERE s.needs_validation = true 
               OR s.validation_score IS NULL 
               OR s.last_validated < NOW() - INTERVAL '30 days'
            ORDER BY s.updated_at DESC
            LIMIT $1
        `;
        
        const result = await db.query(pendingQuery, [SYNC_BATCH_SIZE]);
        
        if (result.rows.length === 0) {
            console.log('✓ No services need validation');
            return;
        }
        
        console.log(`Found ${result.rows.length} services needing validation`);
        
        // Submit validation requests for each service
        for (const service of result.rows) {
            try {
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
                    source_url: `${process.env.BASE_URL || 'http://localhost:3000'}/api/services/${service.id}`
                };
                
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
                }, { timeout: 30000 });
                
                // Store validation reference
                await storeValidationReference(service.id, validationResponse.data.task_id);
                
                console.log(`✓ Submitted validation for: ${service.name}`);
                
                // Add small delay to avoid overwhelming the system
                await sleep(100);
                
            } catch (error) {
                console.error(`✗ Failed to validate ${service.name}:`, error.message);
            }
        }
        
    } catch (error) {
        console.error('Failed to sync pending validations:', error.message);
    }
}

/**
 * Sync discovered services from the scraping system
 */
async function syncDiscoveredServices() {
    console.log('Syncing discovered services...');
    
    try {
        // Get recent discoveries from the scraping system
        const discoveryResponse = await axios.get(`${SCRAPING_API_BASE}/discovery/recent?limit=${SYNC_BATCH_SIZE}`, {
            timeout: 10000
        });
        
        const discoveredServices = discoveryResponse.data.recent_discoveries || [];
        
        if (discoveredServices.length === 0) {
            console.log('✓ No new discovered services');
            return;
        }
        
        console.log(`Found ${discoveredServices.length} discovered services`);
        
        // Process each discovered service
        for (const service of discoveredServices) {
            try {
                // Check if this service already exists in our system
                const existingService = await findExistingService(service);
                
                if (existingService) {
                    // Update existing service with new information
                    await updateExistingService(existingService.id, service);
                    console.log(`✓ Updated existing service: ${service.name}`);
                } else {
                    // Store as a new discovered service pending review
                    await storeDiscoveredService(service);
                    console.log(`✓ Added discovered service for review: ${service.name}`);
                }
                
            } catch (error) {
                console.error(`✗ Failed to process ${service.name}:`, error.message);
            }
        }
        
    } catch (error) {
        console.error('Failed to sync discovered services:', error.message);
    }
}

/**
 * Update agent monitoring data
 */
async function updateAgentMonitoring() {
    console.log('Updating agent monitoring data...');
    
    try {
        // Get agent performance stats
        const agentStatsResponse = await axios.get(`${SCRAPING_API_BASE}/agents/stats/performance`, {
            timeout: 10000
        });
        
        const stats = agentStatsResponse.data;
        
        // Store monitoring data
        const monitoringQuery = `
            INSERT INTO agent_monitoring (
                agent_id, agent_type, status, tasks_completed, tasks_failed, recorded_at
            ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        `;
        
        await db.query(monitoringQuery, [
            'system_aggregate',
            'system',
            stats.active_agents > 0 ? 'active' : 'inactive',
            stats.total_tasks_completed || 0,
            stats.total_tasks_failed || 0
        ]);
        
        console.log(`✓ Updated monitoring data - ${stats.active_agents} active agents`);
        
    } catch (error) {
        console.error('Failed to update agent monitoring:', error.message);
    }
}

/**
 * Helper function to find existing service
 */
async function findExistingService(discoveredService) {
    const searchQuery = `
        SELECT id, name FROM services
        WHERE (name ILIKE $1 AND phone = $2) 
           OR (name ILIKE $1 AND email = $3)
           OR (phone = $2 AND phone IS NOT NULL)
           OR (email = $3 AND email IS NOT NULL)
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
 * Helper function to update existing service
 */
async function updateExistingService(serviceId, discoveredService) {
    const updateQuery = `
        UPDATE services SET
            description = COALESCE(NULLIF($1, ''), description),
            phone = COALESCE(NULLIF($2, ''), phone),
            email = COALESCE(NULLIF($3, ''), email),
            website = COALESCE(NULLIF($4, ''), website),
            address = COALESCE(NULLIF($5, ''), address),
            service_hours = COALESCE(NULLIF($6, ''), service_hours),
            confidence_score = GREATEST(COALESCE(confidence_score, 0), $7),
            updated_at = CURRENT_TIMESTAMP,
            needs_validation = true
        WHERE id = $8
    `;
    
    await db.query(updateQuery, [
        discoveredService.description,
        discoveredService.phone,
        discoveredService.email,
        discoveredService.website,
        discoveredService.address,
        discoveredService.operating_hours,
        discoveredService.confidence_score || 0.5,
        serviceId
    ]);
}

/**
 * Helper function to store discovered service
 */
async function storeDiscoveredService(service) {
    const insertQuery = `
        INSERT INTO discovered_services (
            name, description, category, phone, email, website,
            address, suburb, postcode, state, operating_hours,
            source_url, extraction_method, confidence_score, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        RETURNING id
    `;
    
    const params = [
        service.name,
        service.description,
        service.category,
        service.phone,
        service.email,
        service.website,
        service.address,
        service.suburb || 'Mount Isa',
        service.postcode || '4825',
        service.state || 'QLD',
        service.operating_hours,
        service.source_url,
        service.extraction_method || 'automated',
        service.confidence_score || 0.5,
        'pending'
    ];
    
    const result = await db.query(insertQuery, params);
    return result.rows[0].id;
}

/**
 * Helper function to store validation reference
 */
async function storeValidationReference(serviceId, taskId) {
    const insertQuery = `
        INSERT INTO service_validations (service_id, task_id, status)
        VALUES ($1, $2, 'pending')
        ON CONFLICT (service_id, task_id) DO NOTHING
    `;
    
    await db.query(insertQuery, [serviceId, taskId]);
}

/**
 * Helper function to add delay
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Run the script if called directly
if (require.main === module) {
    main().catch(error => {
        console.error('Script failed:', error);
        process.exit(1);
    });
}

module.exports = {
    main,
    checkScrapingSystemHealth,
    syncPendingValidations,
    syncDiscoveredServices,
    updateAgentMonitoring
};