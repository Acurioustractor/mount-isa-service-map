/**
 * Mount Isa Service Research using Firecrawl
 * Much more effective than getting blocked by search engines
 */

require('dotenv').config();
const { Pool } = require('pg');
const FirecrawlApp = require('@mendable/firecrawl-js').default;

class FirecrawlMountIsaResearcher {
    constructor() {
        // Initialize Firecrawl (you'll need to get an API key from firecrawl.dev)
        this.firecrawl = new FirecrawlApp({
            apiKey: process.env.FIRECRAWL_API_KEY || 'your-firecrawl-api-key'
        });

        this.db = new Pool({
            host: process.env.DB_HOST || 'localhost',
            database: process.env.DB_NAME || 'mount_isa_services',
            user: process.env.DB_USER || 'benknight',
            port: process.env.DB_PORT || '5432'
        });

        // Mount Isa focused websites to crawl
        this.targetSites = [
            {
                url: 'https://www.mountisa.qld.gov.au',
                name: 'Mount Isa City Council',
                focus: 'Official city services and community information'
            },
            {
                url: 'https://www.health.qld.gov.au/north-west',
                name: 'Queensland Health North West',
                focus: 'Health services in Mount Isa region'
            },
            {
                url: 'https://www.ndis.gov.au',
                name: 'NDIS',
                focus: 'Disability services (filter for Mount Isa)'
            },
            {
                url: 'https://www.salvationarmy.org.au',
                name: 'Salvation Army',
                focus: 'Community support services'
            },
            {
                url: 'https://www.redcross.org.au',
                name: 'Red Cross',
                focus: 'Emergency and community services'
            }
        ];
    }

    async crawlSiteForServices(site) {
        console.log(`🔍 Crawling ${site.name} for Mount Isa services...`);
        console.log(`   Focus: ${site.focus}`);

        try {
            // Use Firecrawl to crawl the site and extract structured data
            const crawlResponse = await this.firecrawl.crawlUrl(site.url, {
                includes: ['*mount*isa*', '*4825*'],  // Focus on Mount Isa pages
                excludes: ['*pdf*', '*jpg*', '*png*', '*zip*'],
                limit: 10,  // Limit pages per site
                onlyMainContent: true,
                formats: ['extract'],
                extract: {
                    prompt: `
                    Extract information about services in Mount Isa, Queensland (postcode 4825).
                    Look for:
                    - Service name
                    - Description
                    - Phone numbers (especially 07 47xx xxxx format)  
                    - Email addresses
                    - Physical addresses in Mount Isa
                    - Service types (health, community, disability, aged care, youth, family, emergency)
                    - Operating hours
                    - Eligibility criteria
                    
                    Return as JSON array with objects containing: name, description, phone, email, address, category, hours, eligibility
                    Only include services physically located in or serving Mount Isa.
                    `
                }
            });

            if (crawlResponse.success) {
                console.log(`   ✅ Successfully crawled ${crawlResponse.data.length} pages`);
                
                const extractedServices = [];
                
                // Process each crawled page
                for (const page of crawlResponse.data) {
                    if (page.extract && page.extract.length > 0) {
                        const services = Array.isArray(page.extract) ? 
                            page.extract : [page.extract];
                        
                        services.forEach(service => {
                            if (this.isValidMountIsaService(service)) {
                                extractedServices.push({
                                    ...service,
                                    source_url: page.metadata?.url || site.url,
                                    source_site: site.name,
                                    extraction_confidence: 0.8
                                });
                            }
                        });
                    }
                }

                console.log(`   📊 Extracted ${extractedServices.length} Mount Isa services`);
                return extractedServices;

            } else {
                console.log(`   ❌ Crawl failed: ${crawlResponse.error}`);
                return [];
            }

        } catch (error) {
            console.log(`   ❌ Error crawling ${site.name}: ${error.message}`);
            return [];
        }
    }

    isValidMountIsaService(service) {
        if (!service.name || !service.description) return false;
        
        const text = `${service.name} ${service.description} ${service.address || ''}`.toLowerCase();
        
        // Must mention Mount Isa or postcode 4825
        const mountIsaTerms = ['mount isa', 'mt isa', 'mountisa', '4825'];
        const hasMountIsa = mountIsaTerms.some(term => text.includes(term));
        
        // Must have at least one contact method
        const hasContact = service.phone || service.email || service.address;
        
        return hasMountIsa && hasContact;
    }

    async saveServiceToDatabase(service) {
        try {
            const client = await this.db.connect();
            
            const query = `
                INSERT INTO services (
                    name, description, phone, email, website, address,
                    suburb, postcode, state, data_source, confidence_score,
                    research_metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id;
            `;

            const metadata = {
                source_site: service.source_site,
                source_url: service.source_url,
                extraction_method: 'firecrawl_llm',
                crawl_date: new Date().toISOString()
            };

            const result = await client.query(query, [
                service.name,
                service.description,
                service.phone || null,
                service.email || null,
                service.source_url || null,
                service.address || null,
                'Mount Isa',
                '4825',
                'QLD',
                'firecrawl_research',
                service.extraction_confidence || 0.8,
                JSON.stringify(metadata)
            ]);
            
            const serviceId = result.rows[0].id;
            client.release();
            
            console.log(`   💾 Saved: ${service.name} (ID: ${serviceId})`);
            return serviceId;

        } catch (error) {
            console.log(`   ❌ DB Error for ${service.name}: ${error.message}`);
            return null;
        }
    }

    async runComprehensiveResearch() {
        console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║              🔥 FIRECRAWL MOUNT ISA SERVICE RESEARCH 🔥                      ║
║                                                                               ║
║  Using Firecrawl to comprehensively discover Mount Isa services              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        `);

        console.log('🚀 Starting comprehensive Mount Isa service discovery');
        console.log(`🎯 Targeting ${this.targetSites.length} key websites`);
        console.log('🤖 Using AI extraction to find service information');
        console.log();

        const allServices = [];
        let totalSaved = 0;

        // Crawl each target site
        for (const [index, site] of this.targetSites.entries()) {
            console.log(`🌐 [${index + 1}/${this.targetSites.length}] Processing: ${site.name}`);
            
            const services = await this.crawlSiteForServices(site);
            
            if (services.length > 0) {
                console.log(`   📋 Found ${services.length} services, saving to database...`);
                
                for (const service of services) {
                    const serviceId = await this.saveServiceToDatabase(service);
                    if (serviceId) {
                        totalSaved++;
                        allServices.push(service);
                    }
                }
            }

            console.log();
            
            // Rate limiting - be respectful
            if (index < this.targetSites.length - 1) {
                console.log('⏱️  Waiting 30 seconds before next site...');
                await new Promise(resolve => setTimeout(resolve, 30000));
            }
        }

        // Research summary
        console.log('='.repeat(70));
        console.log('📈 COMPREHENSIVE RESEARCH COMPLETE');
        console.log('='.repeat(70));
        console.log(`🔍 Total services discovered: ${allServices.length}`);
        console.log(`💾 Services saved to database: ${totalSaved}`);
        console.log(`🎯 Success rate: ${totalSaved > 0 ? ((totalSaved/allServices.length)*100).toFixed(1) : 0}%`);
        console.log();

        // Show service categories
        if (allServices.length > 0) {
            const categories = {};
            allServices.forEach(service => {
                const category = service.category || 'general';
                categories[category] = (categories[category] || 0) + 1;
            });

            console.log('📊 SERVICES BY CATEGORY:');
            Object.entries(categories).forEach(([category, count]) => {
                console.log(`   ${category}: ${count} services`);
            });
            console.log();

            console.log('🏆 TOP DISCOVERED SERVICES:');
            allServices.slice(0, 5).forEach((service, index) => {
                console.log(`   ${index + 1}. ${service.name}`);
                console.log(`      📞 ${service.phone || 'No phone'}`);
                console.log(`      ✉️  ${service.email || 'No email'}`);
                console.log(`      📍 ${service.address || 'No address'}`);
                console.log(`      🔗 Found on: ${service.source_site}`);
                console.log();
            });
        }

        console.log('🎉 Firecrawl research completed!');
        console.log('🌐 Start your server to view the discovered services');
        
        await this.db.end();
        return allServices;
    }
}

// Alternative: Manual research areas approach
async function suggestResearchAreas() {
    console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 MOUNT ISA RESEARCH FOCUS AREAS 🎯                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    `);

    const researchAreas = [
        {
            area: 'Government Services',
            sites: [
                'https://www.mountisa.qld.gov.au',
                'https://www.qld.gov.au',
                'https://www.australia.gov.au'
            ],
            focus: 'Official government services, permits, community programs'
        },
        {
            area: 'Health Services',
            sites: [
                'https://www.health.qld.gov.au/north-west',
                'https://www.healthdirect.gov.au',
                'https://www.beyondblue.org.au'
            ],
            focus: 'Hospitals, clinics, mental health, Indigenous health'
        },
        {
            area: 'Community Organizations',
            sites: [
                'https://www.salvationarmy.org.au',
                'https://www.redcross.org.au',
                'https://www.unitingcare.org.au'
            ],
            focus: 'Community support, emergency assistance, social services'
        },
        {
            area: 'Disability Services',
            sites: [
                'https://www.ndis.gov.au',
                'https://www.dss.gov.au',
                'https://www.qdn.org.au'
            ],
            focus: 'NDIS providers, disability support, accessibility services'
        },
        {
            area: 'Education & Youth',
            sites: [
                'https://www.eq.edu.au',
                'https://www.pcyc.org.au',
                'https://www.youthnetwork.com.au'
            ],
            focus: 'Schools, youth programs, training, development'
        }
    ];

    console.log('🎯 RECOMMENDED RESEARCH AREAS FOR MOUNT ISA:');
    console.log();

    researchAreas.forEach((area, index) => {
        console.log(`${index + 1}. ${area.area}`);
        console.log(`   Focus: ${area.focus}`);
        console.log(`   Key sites to crawl:`);
        area.sites.forEach(site => console.log(`     • ${site}`));
        console.log();
    });

    console.log('💡 FIRECRAWL APPROACH BENEFITS:');
    console.log('   ✅ No blocking by search engines');
    console.log('   ✅ AI-powered extraction finds hidden services');
    console.log('   ✅ Comprehensive site crawling');
    console.log('   ✅ Structured data extraction');
    console.log('   ✅ Rate-limited and respectful');
    console.log();
    
    console.log('🚀 TO USE FIRECRAWL:');
    console.log('   1. Get API key from firecrawl.dev');
    console.log('   2. Set FIRECRAWL_API_KEY environment variable');
    console.log('   3. Run: node firecrawl-research-runner.js');
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    
    if (args.includes('--suggest') || args.includes('-s')) {
        await suggestResearchAreas();
    } else if (process.env.FIRECRAWL_API_KEY && process.env.FIRECRAWL_API_KEY !== 'your-firecrawl-api-key') {
        const researcher = new FirecrawlMountIsaResearcher();
        await researcher.runComprehensiveResearch();
    } else {
        console.log('❌ Firecrawl API key required');
        console.log('💡 Run with --suggest to see research approach');
        console.log('🔑 Get API key from https://firecrawl.dev');
        await suggestResearchAreas();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = FirecrawlMountIsaResearcher;