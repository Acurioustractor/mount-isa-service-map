/**
 * Populate Mount Isa Services with Demo Data
 * Shows how the intelligent research system would populate the database
 */

const { Pool } = require('pg');

const db = new Pool({
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'mount_isa_services',
    user: process.env.DB_USER || 'benknight',
    port: process.env.DB_PORT || '5432'
});

// Sample services that would be discovered by the intelligent research system
const discoveredServices = [
    {
        name: 'Mount Isa Hospital',
        description: 'Comprehensive hospital services including emergency department, surgical services, maternity, and general medical care for Mount Isa and surrounding regions.',
        category: 'health',
        phone: '(07) 4744 4444',
        email: 'mountisa.hospital@health.qld.gov.au',
        website: 'https://www.health.qld.gov.au/north-west/mount-isa',
        address: '6 Camooweal Street, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.95,
        data_source: 'intelligent_research'
    },
    {
        name: 'Mount Isa Community Health Centre',
        description: 'Primary health care services including general practice, community nursing, mental health support, and health promotion programs.',
        category: 'health', 
        phone: '(07) 4744 4555',
        email: 'health.mountisa@qld.gov.au',
        website: 'https://www.health.qld.gov.au/north-west/mount-isa/community-health',
        address: '15 Marian Street, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.88,
        data_source: 'intelligent_research'
    },
    {
        name: 'Gidgee Healing',
        description: 'Indigenous health services providing culturally appropriate healthcare, healing programs, and community support for Aboriginal and Torres Strait Islander people.',
        category: 'health',
        phone: '(07) 4749 7777',
        email: 'admin@gidgeehealing.org.au',
        website: 'https://gidgeehealing.org.au',
        address: '23 Simpson Street, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.92,
        data_source: 'intelligent_research'
    },
    {
        name: 'Mount Isa NDIS Support Services',
        description: 'Disability support services including NDIS plan management, support coordination, and assistance with daily living activities.',
        category: 'disability',
        phone: '(07) 4743 2100',
        email: 'mountisa@ndissupport.org.au',
        website: 'https://www.ndis.gov.au/participants/local-area-coordinators/queensland',
        address: '45 West Street, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.85,
        data_source: 'intelligent_research'
    },
    {
        name: 'Mount Isa Neighbourhood Centre',
        description: 'Community hub providing social services, family support, emergency relief, community programs, and volunteer coordination.',
        category: 'community',
        phone: '(07) 4743 4888',
        email: 'info@minc.org.au',
        website: 'https://mountisaneighbourhoodcentre.org.au',
        address: '8 Miles Street, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.90,
        data_source: 'intelligent_research'
    },
    {
        name: 'Kalkadoon Community Centre',
        description: 'Indigenous community centre offering cultural programs, youth services, family support, and community development activities.',
        category: 'community',
        phone: '(07) 4749 1988',
        email: 'admin@kalkadoon.org.au',
        website: 'https://kalkadoon.org.au',
        address: '31 Isa Street, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.87,
        data_source: 'intelligent_research'
    },
    {
        name: 'Mount Isa Youth and Community Centre (PCYC)',
        description: 'Youth services including recreational activities, sport programs, holiday programs, and youth development initiatives.',
        category: 'youth',
        phone: '(07) 4743 5299',
        email: 'mountisa@pcyc.org.au',
        website: 'https://www.pcyc.org.au/mount-isa',
        address: '19 Nineteenth Avenue, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.89,
        data_source: 'intelligent_research'
    },
    {
        name: 'Mount Isa Aged Care Services',
        description: 'Comprehensive aged care including home care packages, respite care, social activities, and support for elderly residents.',
        category: 'aged_care',
        phone: '(07) 4744 3200',
        email: 'info@mountisaagedcare.com.au',
        website: 'https://www.myagedcare.gov.au',
        address: '12 Buckley Avenue, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.83,
        data_source: 'intelligent_research'
    },
    {
        name: 'Mount Isa Mental Health Service',
        description: 'Mental health support including counselling, crisis intervention, community mental health programs, and psychological services.',
        category: 'health',
        phone: '(07) 4744 4600',
        email: 'mentalhealth.mountisa@qld.gov.au',
        website: 'https://www.health.qld.gov.au/north-west/mount-isa/mental-health',
        address: '10 Camooweal Street, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.91,
        data_source: 'intelligent_research'
    },
    {
        name: 'Mount Isa Family Support Services',
        description: 'Family support including parenting programs, childcare information, family counselling, and early childhood development services.',
        category: 'family',
        phone: '(07) 4743 1800',
        email: 'families@mountisasupport.org.au',
        website: 'https://www.familysupport.org.au/mount-isa',
        address: '25 Grace Street, Mount Isa',
        suburb: 'Mount Isa',
        postcode: '4825',
        state: 'QLD',
        confidence_score: 0.86,
        data_source: 'intelligent_research'
    }
];

async function populateServices() {
    console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║        📊 MOUNT ISA SERVICE DATABASE POPULATION DEMO 📊                      ║
║                                                                               ║
║  Demonstrates how intelligent research would populate your database           ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    `);

    console.log('🚀 Populating database with discovered Mount Isa services...');
    console.log(`📊 Adding ${discoveredServices.length} services to database`);
    console.log();

    let savedCount = 0;

    for (const [index, service] of discoveredServices.entries()) {
        console.log(`💾 [${index + 1}/${discoveredServices.length}] Saving: ${service.name}`);

        try {
            const client = await db.connect();
            
            const query = `
                INSERT INTO services (
                    name, description, phone, email, website, address,
                    suburb, postcode, state, last_updated, data_source,
                    confidence_score, discovery_date
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
                ON CONFLICT (name, COALESCE(address, '')) DO UPDATE SET
                    description = EXCLUDED.description,
                    phone = COALESCE(EXCLUDED.phone, services.phone),
                    email = COALESCE(EXCLUDED.email, services.email),
                    website = COALESCE(EXCLUDED.website, services.website),
                    last_updated = EXCLUDED.last_updated,
                    confidence_score = EXCLUDED.confidence_score
                RETURNING id;
            `;

            const values = [
                service.name,
                service.description,
                service.phone,
                service.email,
                service.website,
                service.address,
                service.suburb,
                service.postcode,
                service.state,
                new Date(),
                service.data_source,
                service.confidence_score,
                new Date()
            ];

            const result = await client.query(query, values);
            const serviceId = result.rows[0].id;
            
            client.release();

            console.log(`   ✅ Saved with ID: ${serviceId}`);
            savedCount++;

        } catch (error) {
            console.log(`   ❌ Error: ${error.message}`);
        }
    }

    console.log();
    console.log('='.repeat(60));
    console.log('📈 DATABASE POPULATION COMPLETE');
    console.log('='.repeat(60));
    console.log(`💾 Services added to database: ${savedCount}`);
    console.log(`⭐ Average confidence score: ${(discoveredServices.reduce((sum, s) => sum + s.confidence_score, 0) / discoveredServices.length * 100).toFixed(1)}%`);
    console.log();

    // Show statistics by category
    const categories = {};
    discoveredServices.forEach(service => {
        categories[service.category] = (categories[service.category] || 0) + 1;
    });

    console.log('📊 SERVICES BY CATEGORY:');
    Object.entries(categories).forEach(([category, count]) => {
        console.log(`   ${category}: ${count} services`);
    });

    console.log();
    console.log('🎉 Demo population completed!');
    console.log('🌐 Start your server with: npm start');
    console.log('📱 View services at: http://localhost:3000');

    await db.end();
}

// Run if called directly
if (require.main === module) {
    populateServices().catch(console.error);
}

module.exports = { discoveredServices, populateServices };