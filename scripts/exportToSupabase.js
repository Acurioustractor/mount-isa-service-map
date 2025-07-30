#!/usr/bin/env node

// Script to export local services data and import to Supabase

const { Pool } = require('pg');
const { supabase } = require('../config/supabase');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Local PostgreSQL connection
const localPool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'mount_isa_services',
    user: process.env.DB_USER || 'benknight',
    password: process.env.DB_PASSWORD || '',
    port: process.env.DB_PORT || 5432,
});

async function exportToSupabase() {
    try {
        console.log('🚀 Starting export from local PostgreSQL to Supabase...');
        
        // 1. Export and import service categories
        console.log('📋 Exporting service categories...');
        const categoriesResult = await localPool.query('SELECT * FROM service_categories ORDER BY created_at');
        const localCategories = categoriesResult.rows;
        
        if (localCategories.length > 0) {
            console.log(`📤 Found ${localCategories.length} categories locally`);
            
            // Clear existing categories first (except defaults)
            const { error: clearError } = await supabase
                .from('service_categories')
                .delete()
                .neq('name', 'placeholder'); // Keep all for now
                
            // Insert categories
            const { data: insertedCategories, error: catError } = await supabase
                .from('service_categories')
                .upsert(localCategories.map(cat => ({
                    id: cat.id,
                    name: cat.name,
                    description: cat.description,
                    parent_id: cat.parent_id,
                    is_active: cat.is_active,
                    created_at: cat.created_at,
                    updated_at: cat.updated_at
                })), { onConflict: 'name' });
                
            if (catError) {
                console.warn('⚠️  Category import warning:', catError.message);
            } else {
                console.log('✅ Categories imported successfully');
            }
        }
        
        // 2. Export and import services
        console.log('🏢 Exporting services...');
        const servicesResult = await localPool.query(`
            SELECT 
                s.*,
                sc.name as category_name
            FROM services s
            LEFT JOIN service_categories sc ON s.category_id = sc.id
            WHERE s.is_active = true
            ORDER BY s.created_at
        `);
        const localServices = servicesResult.rows;
        
        console.log(`📤 Found ${localServices.length} services locally`);
        
        if (localServices.length > 0) {
            // Get Supabase category mappings
            const { data: supabaseCategories, error: catFetchError } = await supabase
                .from('service_categories')
                .select('*');
                
            if (catFetchError) {
                throw new Error('Failed to fetch Supabase categories: ' + catFetchError.message);
            }
            
            const categoryMap = {};
            supabaseCategories.forEach(cat => {
                categoryMap[cat.name] = cat.id;
            });
            
            // Prepare services for import
            const servicesToImport = localServices.map(service => ({
                id: service.id,
                name: service.name,
                description: service.description,
                category_id: service.category_name ? categoryMap[service.category_name] : null,
                address: service.address,
                suburb: service.suburb,
                state: service.state,
                postcode: service.postcode,
                latitude: service.latitude,
                longitude: service.longitude,
                phone: service.phone,
                email: service.email,
                website: service.website,
                is_active: service.is_active,
                created_at: service.created_at,
                updated_at: service.updated_at
            }));
            
            // Import services in batches
            const batchSize = 10;
            let importedCount = 0;
            
            for (let i = 0; i < servicesToImport.length; i += batchSize) {
                const batch = servicesToImport.slice(i, i + batchSize);
                
                const { data, error } = await supabase
                    .from('services')
                    .upsert(batch, { onConflict: 'id' });
                    
                if (error) {
                    console.warn(`⚠️  Batch ${Math.floor(i/batchSize) + 1} warning:`, error.message);
                } else {
                    importedCount += batch.length;
                    console.log(`✅ Imported batch ${Math.floor(i/batchSize) + 1}: ${batch.length} services`);
                }
            }
            
            console.log(`🎉 Successfully imported ${importedCount} services to Supabase!`);
        }
        
        // 3. Verify import
        console.log('🔍 Verifying import...');
        const { data: supabaseServices, error: verifyError } = await supabase
            .from('services')
            .select('count', { count: 'exact', head: true });
            
        if (!verifyError) {
            console.log(`📊 Supabase now contains ${supabaseServices.length || 'unknown'} services`);
        }
        
        // Test a sample query
        const { data: sampleServices, error: sampleError } = await supabase
            .from('services')
            .select(`
                id,
                name,
                suburb,
                service_categories!category_id(name)
            `)
            .limit(3);
            
        if (!sampleError && sampleServices) {
            console.log('📋 Sample services imported:');
            sampleServices.forEach(service => {
                console.log(`  • ${service.name} (${service.suburb}) - ${service.service_categories?.name || 'No category'}`);
            });
        }
        
        console.log('🎉 Export to Supabase completed successfully!');
        console.log('🌐 Your platform should now show live data at: https://mount-isa-service-map.vercel.app');
        
        await localPool.end();
        
    } catch (error) {
        console.error('❌ Error during export:', error);
        process.exit(1);
    }
}

// Run export if script is called directly
if (require.main === module) {
    exportToSupabase();
}

module.exports = { exportToSupabase };