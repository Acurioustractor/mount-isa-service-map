/**
 * Production Firecrawl Mount Isa Service Discovery
 * Working version that discovers and saves services to database
 */

require('dotenv').config();
const { Pool } = require('pg');
const FirecrawlApp = require('@mendable/firecrawl-js').default;

class ProductionMountIsaResearcher {
    constructor() {
        this.firecrawl = new FirecrawlApp({
            apiKey: process.env.FIRECRAWL_API_KEY
        });

        this.db = new Pool({
            host: process.env.DB_HOST || 'localhost',
            database: process.env.DB_NAME || 'mount_isa_services',
            user: process.env.DB_USER || 'benknight',
            port: process.env.DB_PORT || '5432'
        });

        // Key Mount Isa websites to scrape
        this.targetPages = [
            {
                url: 'https://www.mountisa.qld.gov.au',
                name: 'Mount Isa City Council',
                category: 'government'
            },
            {
                url: 'https://www.mountisa.qld.gov.au/community',
                name: 'Mount Isa Community Services',
                category: 'community'
            },
            {
                url: 'https://www.health.qld.gov.au/north-west/mount-isa',
                name: 'Mount Isa Health Services',
                category: 'health'
            }
        ];
    }

    async scrapePageForServices(page) {
        console.log(`🔍 Scraping: ${page.name}`);
        console.log(`   URL: ${page.url}`);

        try {
            const result = await this.firecrawl.scrapeUrl(page.url, {
                formats: ['extract'],
                extract: {
                    prompt: `
                    Extract information about services located in Mount Isa, Queensland (postcode 4825).
                    
                    Look for and extract:
                    - Service/facility name
                    - Brief description of what they offer
                    - Phone numbers (especially 07 47xx xxxx format)
                    - Email addresses  
                    - Physical addresses in Mount Isa
                    - Service category (health, community, government, recreation, etc.)
                    - Operating hours if mentioned
                    
                    Return as JSON array with objects containing:
                    {
                        "name": "service name",
                        "description": "what they do", 
                        "phone": "phone number",
                        "email": "email address",
                        "address": "physical address",
                        "category": "service type",
                        "hours": "operating hours"
                    }
                    
                    Only include services that are physically located in or directly serve Mount Isa.
                    Be specific with descriptions - don't use generic text.
                    `
                }
            });

            if (result.success && result.extract) {
                const services = Array.isArray(result.extract) ? result.extract : [result.extract];
                console.log(`   ✅ Found ${services.length} services`);
                
                return services.map(service => ({
                    ...service,
                    source_url: page.url,
                    source_site: page.name,
                    default_category: page.category
                }));
            } else {
                console.log(`   ⚠️  No services extracted`);
                return [];
            }

        } catch (error) {
            console.log(`   ❌ Error scraping ${page.name}: ${error.message}`);
            return [];
        }
    }

    async saveServiceToDatabase(service) {
        try {
            const client = await this.db.connect();
            
            // Clean and validate the service data
            const cleanService = {
                name: service.name || 'Unknown Service',
                description: service.description || 'Service in Mount Isa',
                phone: this.cleanPhoneNumber(service.phone),
                email: this.cleanEmail(service.email),
                website: service.source_url,
                address: service.address || null,
                category: service.category || service.default_category || 'general',
                hours: service.hours || null
            };

            // Skip if no meaningful info
            if (!cleanService.name || cleanService.name === 'Unknown Service') {
                return null;
            }

            const query = `
                INSERT INTO services (
                    name, description, phone, email, website, address,
                    suburb, postcode, state, data_source, confidence_score,
                    research_metadata, discovery_date
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id;
            `;

            const metadata = {
                source_site: service.source_site,
                source_url: service.source_url,
                extraction_method: 'firecrawl_production',
                scraped_at: new Date().toISOString(),
                hours: cleanService.hours
            };

            const result = await client.query(query, [
                cleanService.name,
                cleanService.description,
                cleanService.phone,
                cleanService.email,
                cleanService.website,
                cleanService.address,
                'Mount Isa',
                '4825',
                'QLD',
                'firecrawl_research',
                0.85, // High confidence for Firecrawl extraction
                JSON.stringify(metadata),
                new Date()
            ]);
            
            const serviceId = result.rows[0].id;
            client.release();
            
            console.log(`   💾 Saved: ${cleanService.name} (ID: ${serviceId})`);
            return serviceId;

        } catch (error) {
            if (error.code === '23505') { // Duplicate key
                console.log(`   ⚠️  Duplicate: ${service.name || 'Unknown'} (skipped)`);
            } else {
                console.log(`   ❌ DB Error: ${error.message}`);
            }
            return null;
        }
    }

    cleanPhoneNumber(phone) {
        if (!phone || typeof phone !== 'string') return null;
        
        // Extract Australian phone numbers
        const phoneMatch = phone.match(/(\(07\)|\+61\s*7|07)\s*\d{4}\s*\d{4}/);
        return phoneMatch ? phoneMatch[0].trim() : null;
    }

    cleanEmail(email) {
        if (!email || typeof email !== 'string') return null;
        
        const emailMatch = email.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/);
        return emailMatch ? emailMatch[0] : null;
    }

    async runProduction() {
        console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║              🔥 PRODUCTION FIRECRAWL SERVICE DISCOVERY 🔥                    ║
║                                                                               ║
║  Discovering Mount Isa services and saving to your database                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        `);

        console.log('🚀 Starting production service discovery');
        console.log(`🎯 Scraping ${this.targetPages.length} key pages`);
        console.log('🤖 Using AI extraction for accurate results');
        console.log();

        let totalFound = 0;
        let totalSaved = 0;

        for (const [index, page] of this.targetPages.entries()) {
            console.log(`🌐 [${index + 1}/${this.targetPages.length}] Processing: ${page.name}`);
            
            const services = await this.scrapePageForServices(page);
            totalFound += services.length;

            if (services.length > 0) {
                console.log(`   📋 Processing ${services.length} services...`);
                
                for (const service of services) {
                    const serviceId = await this.saveServiceToDatabase(service);
                    if (serviceId) {
                        totalSaved++;
                    }
                }
            }

            console.log();
            
            // Rate limiting between pages
            if (index < this.targetPages.length - 1) {
                console.log('⏱️  Waiting 10 seconds...');
                await new Promise(resolve => setTimeout(resolve, 10000));
            }
        }

        // Final summary
        console.log('='.repeat(70));
        console.log('📈 PRODUCTION DISCOVERY COMPLETE');
        console.log('='.repeat(70));
        console.log(`🔍 Services found: ${totalFound}`);
        console.log(`💾 Services saved: ${totalSaved}`);
        console.log(`🎯 Success rate: ${totalFound > 0 ? ((totalSaved/totalFound)*100).toFixed(1) : 0}%`);
        console.log();

        // Show what was saved
        if (totalSaved > 0) {
            console.log('✅ Check your database for the new services!');
            console.log('🌐 Start your app: npm start');
            console.log('📱 View at: http://localhost:3000');
        }

        await this.db.end();
        return { found: totalFound, saved: totalSaved };
    }
}

// Run the production discovery
async function main() {
    try {
        const researcher = new ProductionMountIsaResearcher();
        await researcher.runProduction();
    } catch (error) {
        console.error('❌ Production discovery failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = ProductionMountIsaResearcher;