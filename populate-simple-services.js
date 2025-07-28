/**
 * Simple service population without ON CONFLICT
 */

const { Pool } = require('pg');

const db = new Pool({
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'mount_isa_services',
    user: process.env.DB_USER || 'benknight',
    port: process.env.DB_PORT || '5432'
});

const services = [
    {
        name: 'Mount Isa Hospital',
        description: 'Comprehensive hospital services including emergency, surgery, maternity',
        phone: '(07) 4744 4444',
        email: 'mountisa.hospital@health.qld.gov.au',
        website: 'https://www.health.qld.gov.au/north-west/mount-isa',
        address: '6 Camooweal Street, Mount Isa'
    },
    {
        name: 'Mount Isa Community Health Centre', 
        description: 'Primary health care services and community nursing',
        phone: '(07) 4744 4555',
        address: '15 Marian Street, Mount Isa'
    },
    {
        name: 'Gidgee Healing',
        description: 'Indigenous health services and cultural healing programs',
        phone: '(07) 4749 7777',
        email: 'admin@gidgeehealing.org.au',
        address: '23 Simpson Street, Mount Isa'
    }
];

async function addServices() {
    console.log('🚀 Adding discovered services to database...');
    
    for (const service of services) {
        try {
            const client = await db.connect();
            
            const query = `
                INSERT INTO services (
                    name, description, phone, email, website, address,
                    suburb, postcode, state, data_source, confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id;
            `;

            const result = await client.query(query, [
                service.name,
                service.description,
                service.phone || null,
                service.email || null,
                service.website || null,
                service.address || null,
                'Mount Isa',
                '4825',
                'QLD',
                'intelligent_research',
                0.85
            ]);
            
            console.log(`✅ Added: ${service.name} (ID: ${result.rows[0].id})`);
            client.release();
            
        } catch (error) {
            console.log(`❌ Error adding ${service.name}: ${error.message}`);
        }
    }
    
    console.log('🎉 Services added! Check your database.');
    await db.end();
}

addServices();