/**
 * COMPREHENSIVE Mount Isa Service Discovery
 * Scales up to discover hundreds of services across multiple domains
 */

require('dotenv').config();
const { Pool } = require('pg');
const FirecrawlApp = require('@mendable/firecrawl-js').default;

class ComprehensiveMountIsaResearcher {
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

        // COMPREHENSIVE list of websites to crawl for Mount Isa services
        this.researchTargets = [
            // Government & Official
            {
                url: 'https://www.mountisa.qld.gov.au',
                name: 'Mount Isa City Council',
                category: 'government',
                crawlLimit: 50,
                priority: 1
            },
            {
                url: 'https://www.qld.gov.au',
                name: 'Queensland Government',
                category: 'government', 
                crawlLimit: 30,
                priority: 2,
                includes: ['*mount*isa*', '*4825*']
            },
            
            // Health Services
            {
                url: 'https://www.health.qld.gov.au',
                name: 'Queensland Health',
                category: 'health',
                crawlLimit: 40,
                priority: 1,
                includes: ['*north*west*', '*mount*isa*', '*4825*']
            },
            {
                url: 'https://www.healthdirect.gov.au',
                name: 'Health Direct Australia',
                category: 'health',
                crawlLimit: 20,
                priority: 2,
                includes: ['*mount*isa*', '*4825*']
            },
            {
                url: 'https://www.beyondblue.org.au',
                name: 'Beyond Blue',
                category: 'mental_health',
                crawlLimit: 15,
                priority: 3,
                includes: ['*mount*isa*', '*queensland*']
            },
            
            // Community Organizations
            {
                url: 'https://www.salvationarmy.org.au',
                name: 'Salvation Army',
                category: 'community',
                crawlLimit: 25,
                priority: 1,
                includes: ['*mount*isa*', '*queensland*', '*qld*']
            },
            {
                url: 'https://www.redcross.org.au',
                name: 'Australian Red Cross',
                category: 'emergency',
                crawlLimit: 25,
                priority: 1,
                includes: ['*mount*isa*', '*queensland*']
            },
            {
                url: 'https://www.unitingcare.org.au',
                name: 'UnitingCare',
                category: 'community',
                crawlLimit: 20,
                priority: 2,
                includes: ['*queensland*', '*mount*isa*']
            },
            {
                url: 'https://www.anglicare.asn.au',
                name: 'Anglicare',
                category: 'community',
                crawlLimit: 20,
                priority: 2,
                includes: ['*queensland*', '*mount*isa*']
            },
            
            // Disability Services
            {
                url: 'https://www.ndis.gov.au',
                name: 'NDIS',
                category: 'disability',
                crawlLimit: 35,
                priority: 1,
                includes: ['*mount*isa*', '*queensland*', '*4825*']
            },
            {
                url: 'https://www.dss.gov.au',
                name: 'Department of Social Services',
                category: 'disability',
                crawlLimit: 20,
                priority: 2,
                includes: ['*mount*isa*', '*queensland*']
            },
            {
                url: 'https://www.qdn.org.au',
                name: 'Queensland Disability Network',
                category: 'disability',
                crawlLimit: 25,
                priority: 1
            },
            
            // Education & Youth
            {
                url: 'https://www.eq.edu.au',
                name: 'Education Queensland',
                category: 'education',
                crawlLimit: 30,
                priority: 2,
                includes: ['*mount*isa*', '*north*west*']
            },
            {
                url: 'https://www.pcyc.org.au',
                name: 'PCYC Queensland',
                category: 'youth',
                crawlLimit: 20,
                priority: 1,
                includes: ['*mount*isa*', '*queensland*']
            },
            {
                url: 'https://www.yfs.org.au',
                name: 'Youth & Family Services',
                category: 'youth',
                crawlLimit: 15,
                priority: 2,
                includes: ['*queensland*', '*mount*isa*']
            },
            
            // Employment & Training
            {
                url: 'https://www.jobsqueensland.gov.au',
                name: 'Jobs Queensland',
                category: 'employment',
                crawlLimit: 20,
                priority: 2,
                includes: ['*mount*isa*', '*north*west*']
            },
            {
                url: 'https://www.jobactive.gov.au',
                name: 'JobActive',
                category: 'employment',
                crawlLimit: 15,
                priority: 3,
                includes: ['*mount*isa*', '*4825*']
            },
            
            // Housing & Support
            {
                url: 'https://www.qld.gov.au/housing',
                name: 'Queensland Housing',
                category: 'housing',
                crawlLimit: 20,
                priority: 2,
                includes: ['*mount*isa*', '*north*west*']
            },
            {
                url: 'https://www.homelessnessaustralia.org.au',
                name: 'Homelessness Australia',
                category: 'housing',
                crawlLimit: 15,
                priority: 3,
                includes: ['*queensland*', '*mount*isa*']
            },
            
            // Legal Services
            {
                url: 'https://www.legalaid.qld.gov.au',
                name: 'Legal Aid Queensland',
                category: 'legal',
                crawlLimit: 25,
                priority: 1,
                includes: ['*mount*isa*', '*north*west*']
            },
            {
                url: 'https://www.qails.org.au',
                name: 'Queensland Association of Independent Legal Services',
                category: 'legal',
                crawlLimit: 20,
                priority: 2
            },
            
            // Indigenous Services
            {
                url: 'https://www.niaa.gov.au',
                name: 'National Indigenous Australians Agency',
                category: 'indigenous',
                crawlLimit: 20,
                priority: 2,
                includes: ['*queensland*', '*mount*isa*']
            },
            {
                url: 'https://www.qaihc.com.au',
                name: 'Queensland Aboriginal and Islander Health Council',
                category: 'indigenous',
                crawlLimit: 25,
                priority: 1
            },
            
            // Aged Care
            {
                url: 'https://www.myagedcare.gov.au',
                name: 'My Aged Care',
                category: 'aged_care',
                crawlLimit: 20,
                priority: 2,
                includes: ['*mount*isa*', '*queensland*']
            },
            {
                url: 'https://www.cota.org.au',
                name: 'Council on the Ageing',
                category: 'aged_care',
                crawlLimit: 15,
                priority: 3,
                includes: ['*queensland*']
            }
        ];
    }

    async crawlSiteComprehensively(target) {
        console.log(`🌐 Crawling: ${target.name}`);
        console.log(`   Category: ${target.category}`);
        console.log(`   URL: ${target.url}`);
        console.log(`   Pages to crawl: ${target.crawlLimit}`);

        try {
            const crawlOptions = {
                limit: target.crawlLimit,
                excludes: [
                    '*pdf*', '*jpg*', '*png*', '*gif*', '*zip*', '*doc*',
                    '*login*', '*admin*', '*dashboard*', '*private*'
                ],
                formats: ['extract'],
                extract: {
                    prompt: `
                    You are analyzing pages for services in Mount Isa, Queensland (postcode 4825).
                    
                    Extract ALL services, facilities, programs, or organizations that:
                    1. Are located in Mount Isa, Queensland
                    2. Serve people in Mount Isa 
                    3. Have a physical presence in Mount Isa
                    4. Provide services to Mount Isa residents
                    
                    For each service found, extract:
                    - name: Full official name
                    - description: What services/programs they provide (be specific)
                    - phone: Phone number (look for 07 47xx xxxx format)
                    - email: Email address
                    - address: Physical street address in Mount Isa
                    - category: Type of service (health, community, government, education, etc.)
                    - hours: Operating hours if mentioned
                    - website: Website URL if different from current page
                    - eligibility: Who can use the service
                    
                    Return as JSON array. Include government offices, community centers, health services, 
                    support services, educational facilities, recreational facilities, etc.
                    
                    Be thorough - extract every relevant service mentioned on the page.
                    `
                }
            };

            // Add includes filter if specified
            if (target.includes) {
                crawlOptions.includes = target.includes;
            }

            const result = await this.firecrawl.crawlUrl(target.url, crawlOptions);

            if (result.success && result.data) {
                console.log(`   ✅ Crawled ${result.data.length} pages`);
                
                const allServices = [];
                let extractedCount = 0;

                // Process each crawled page
                for (const page of result.data) {
                    if (page.extract && page.extract.length > 0) {
                        const services = Array.isArray(page.extract) ? page.extract : [page.extract];
                        
                        services.forEach(service => {
                            if (this.isValidMountIsaService(service)) {
                                allServices.push({
                                    ...service,
                                    source_url: page.metadata?.url || target.url,
                                    source_site: target.name,
                                    source_category: target.category,
                                    extraction_confidence: 0.82
                                });
                                extractedCount++;
                            }
                        });
                    }
                }

                console.log(`   📊 Extracted ${extractedCount} Mount Isa services`);
                return allServices;

            } else {
                console.log(`   ❌ Crawl failed: ${result.error || 'Unknown error'}`);
                return [];
            }

        } catch (error) {
            console.log(`   ❌ Error: ${error.message}`);
            return [];
        }
    }

    isValidMountIsaService(service) {
        if (!service || !service.name) return false;
        
        const searchText = `
            ${service.name || ''} 
            ${service.description || ''} 
            ${service.address || ''} 
            ${service.location || ''}
        `.toLowerCase();

        // Must mention Mount Isa, Queensland, or relevant postcodes
        const mountIsaIndicators = [
            'mount isa', 'mt isa', 'mountisa',
            '4825', '4828', '4829', '4830', // Mount Isa region postcodes
            'north west queensland', 'gulf country'
        ];

        const hasMountIsaConnection = mountIsaIndicators.some(indicator => 
            searchText.includes(indicator)
        );

        // Must have some meaningful content
        const hasSubstance = service.name.length > 3 && 
                           (service.description || service.phone || service.email || service.address);

        return hasMountIsaConnection && hasSubstance;
    }

    async saveServiceBatch(services) {
        let savedCount = 0;
        const client = await this.db.connect();

        try {
            for (const service of services) {
                try {
                    const cleanService = this.cleanServiceData(service);
                    
                    const query = `
                        INSERT INTO services (
                            name, description, phone, email, website, address,
                            suburb, postcode, state, data_source, confidence_score,
                            research_metadata, discovery_date
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (name, COALESCE(address, '')) DO UPDATE SET
                            description = COALESCE(EXCLUDED.description, services.description),
                            phone = COALESCE(EXCLUDED.phone, services.phone),
                            email = COALESCE(EXCLUDED.email, services.email),
                            website = COALESCE(EXCLUDED.website, services.website),
                            last_updated = NOW()
                        RETURNING id;
                    `;

                    const metadata = {
                        source_site: service.source_site,
                        source_url: service.source_url,
                        source_category: service.source_category,
                        extraction_method: 'comprehensive_firecrawl',
                        crawled_at: new Date().toISOString()
                    };

                    const result = await client.query(query, [
                        cleanService.name,
                        cleanService.description,
                        cleanService.phone,
                        cleanService.email,
                        cleanService.website,
                        cleanService.address,
                        'Mount Isa',
                        cleanService.postcode || '4825',
                        'QLD',
                        'comprehensive_research',
                        service.extraction_confidence || 0.82,
                        JSON.stringify(metadata),
                        new Date()
                    ]);

                    savedCount++;
                    
                    if (savedCount % 10 === 0) {
                        console.log(`   💾 Saved ${savedCount} services so far...`);
                    }

                } catch (dbError) {
                    if (dbError.code !== '23505') { // Ignore duplicates
                        console.log(`   ⚠️  DB error for ${service.name}: ${dbError.message}`);
                    }
                }
            }

        } finally {
            client.release();
        }

        return savedCount;
    }

    cleanServiceData(service) {
        return {
            name: this.cleanText(service.name) || 'Unknown Service',
            description: this.cleanText(service.description) || 'Service in Mount Isa, Queensland',
            phone: this.extractPhoneNumber(service.phone),
            email: this.extractEmail(service.email),
            website: this.cleanUrl(service.website || service.source_url),
            address: this.cleanText(service.address),
            postcode: this.extractPostcode(service.address || service.description)
        };
    }

    cleanText(text) {
        if (!text || typeof text !== 'string') return null;
        return text.trim().replace(/\s+/g, ' ').substring(0, 500);
    }

    extractPhoneNumber(phone) {
        if (!phone) return null;
        const phoneMatch = phone.match(/(\+61\s*7|07|\(07\))\s*\d{4}\s*\d{4}/);
        return phoneMatch ? phoneMatch[0].trim() : null;
    }

    extractEmail(email) {
        if (!email) return null;
        const emailMatch = email.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/);
        return emailMatch ? emailMatch[0] : null;
    }

    extractPostcode(text) {
        if (!text) return null;
        const postcodeMatch = text.match(/\b(4825|4828|4829|4830)\b/);
        return postcodeMatch ? postcodeMatch[0] : null;
    }

    cleanUrl(url) {
        if (!url || !url.startsWith('http')) return null;
        return url.substring(0, 255);
    }

    async runComprehensiveResearch() {
        console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║            🚀 COMPREHENSIVE MOUNT ISA SERVICE DISCOVERY 🚀                   ║
║                                                                               ║
║  Scaling up to discover HUNDREDS of Mount Isa services                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        `);

        console.log('🎯 COMPREHENSIVE RESEARCH STRATEGY:');
        console.log(`   📊 ${this.researchTargets.length} major websites to crawl`);
        console.log(`   🔍 Up to ${this.researchTargets.reduce((sum, t) => sum + t.crawlLimit, 0)} pages to analyze`);
        console.log('   🤖 AI extraction from every relevant page');
        console.log('   💾 Automatic database storage with deduplication');
        console.log();

        // Sort by priority
        const sortedTargets = this.researchTargets.sort((a, b) => a.priority - b.priority);

        let totalFound = 0;
        let totalSaved = 0;
        const startTime = Date.now();

        for (const [index, target] of sortedTargets.entries()) {
            console.log(`🌐 [${index + 1}/${sortedTargets.length}] Processing: ${target.name}`);
            
            const services = await this.crawlSiteComprehensively(target);
            totalFound += services.length;

            if (services.length > 0) {
                console.log(`   📋 Saving ${services.length} services to database...`);
                const saved = await this.saveServiceBatch(services);
                totalSaved += saved;
                console.log(`   ✅ Saved ${saved} new services`);
            }

            console.log();
            
            // Progress update
            const elapsed = (Date.now() - startTime) / 1000 / 60;
            console.log(`   ⏱️  Progress: ${index + 1}/${sortedTargets.length} sites, ${elapsed.toFixed(1)} minutes elapsed`);
            
            // Rate limiting
            if (index < sortedTargets.length - 1) {
                console.log('   💤 Waiting 15 seconds before next site...');
                await new Promise(resolve => setTimeout(resolve, 15000));
            }
            console.log();
        }

        // Final comprehensive summary
        const totalTime = (Date.now() - startTime) / 1000 / 60;
        
        console.log('='.repeat(80));
        console.log('🎉 COMPREHENSIVE RESEARCH COMPLETE');
        console.log('='.repeat(80));
        console.log(`🔍 Total services discovered: ${totalFound}`);
        console.log(`💾 Total services saved: ${totalSaved}`);
        console.log(`🎯 Success rate: ${totalFound > 0 ? ((totalSaved/totalFound)*100).toFixed(1) : 0}%`);
        console.log(`⏱️  Total time: ${totalTime.toFixed(1)} minutes`);
        console.log(`📊 Average: ${(totalSaved/totalTime).toFixed(1)} services per minute`);
        console.log();

        // Show category breakdown
        const categoryQuery = `
            SELECT research_metadata->>'source_category' as category, COUNT(*) as count
            FROM services 
            WHERE data_source = 'comprehensive_research'
            GROUP BY research_metadata->>'source_category'
            ORDER BY count DESC;
        `;

        try {
            const client = await this.db.connect();
            const categoryResult = await client.query(categoryQuery);
            
            if (categoryResult.rows.length > 0) {
                console.log('📊 SERVICES BY CATEGORY:');
                categoryResult.rows.forEach(row => {
                    console.log(`   ${row.category || 'general'}: ${row.count} services`);
                });
                console.log();
            }
            
            client.release();
        } catch (error) {
            console.log('⚠️  Could not generate category breakdown');
        }

        console.log('🎉 COMPREHENSIVE DISCOVERY COMPLETE!');
        console.log('🌐 Start your app: npm start');
        console.log('📱 View hundreds of services at: http://localhost:8888');
        
        await this.db.end();
        return { found: totalFound, saved: totalSaved, timeMinutes: totalTime };
    }
}

// Run comprehensive research
async function main() {
    try {
        const researcher = new ComprehensiveMountIsaResearcher();
        const results = await researcher.runComprehensiveResearch();
        
        console.log(`\n✅ Mission accomplished! Discovered ${results.saved} Mount Isa services in ${results.timeMinutes.toFixed(1)} minutes`);
        
    } catch (error) {
        console.error('❌ Comprehensive research failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = ComprehensiveMountIsaResearcher;