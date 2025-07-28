/**
 * SCALED Mount Isa Service Discovery v2
 * Works within API rate limits and uses correct Firecrawl format
 */

require('dotenv').config();
const { Pool } = require('pg');
const FirecrawlApp = require('@mendable/firecrawl-js').default;

class ScaledMountIsaResearcher {
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

        // High-priority pages that will yield the most Mount Isa services
        this.priorityTargets = [
            // Mount Isa specific pages (highest priority)
            'https://www.mountisa.qld.gov.au/community/health-services',
            'https://www.mountisa.qld.gov.au/community/community-services',
            'https://www.mountisa.qld.gov.au/community/recreation-facilities',
            'https://www.mountisa.qld.gov.au/residents/library-services',
            
            // Queensland Health Mount Isa
            'https://www.health.qld.gov.au/north-west/mount-isa/services',  
            'https://www.health.qld.gov.au/north-west/services',
            
            // NDIS Mount Isa specific
            'https://www.ndis.gov.au/participants/local-area-coordinators/queensland/mount-isa',
            
            // Community organizations with Mount Isa presence
            'https://www.salvationarmy.org.au/find-us/qld/mount-isa',
            'https://www.redcross.org.au/get-help/find-services/mount-isa', 
            'https://www.unitingcare.org.au/services/location/mount-isa',
            
            // Education
            'https://www.eq.edu.au/find-school?q=mount%20isa',
            'https://www.pcyc.org.au/mount-isa',
            
            // Legal services
            'https://www.legalaid.qld.gov.au/offices/mount-isa',
            
            // Indigenous services
            'https://www.qaihc.com.au/services/north-west-queensland',
            
            // Employment
            'https://www.jobsqueensland.gov.au/locations/mount-isa'
        ];

        this.serviceExtractionPrompt = `
        Extract ALL services, organizations, facilities or programs mentioned on this page that are located in or serve Mount Isa, Queensland.

        For each service found, extract:
        - name: Official name of the service/organization
        - description: What they do/provide (be specific)
        - phone: Phone number (especially 07 47xx xxxx)
        - email: Email address  
        - address: Street address in Mount Isa
        - category: health, community, government, education, disability, aged_care, youth, legal, indigenous, employment, etc.
        - website: Website URL if mentioned
        - hours: Operating hours
        - eligibility: Who can access the service

        Return as JSON array. Only include services that are clearly in Mount Isa or serve Mount Isa residents.
        `;
    }

    async scrapeUrlWithRetry(url, retries = 3) {
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                console.log(`   🔍 Scraping: ${url} (attempt ${attempt})`);
                
                const result = await this.firecrawl.scrapeUrl(url, {
                    formats: ['extract'],
                    extract: {
                        prompt: this.serviceExtractionPrompt
                    }
                });

                if (result.success) {
                    return result;
                } else {
                    console.log(`   ⚠️  Attempt ${attempt} failed: ${result.error}`);
                }

            } catch (error) {
                if (error.message.includes('429') || error.message.includes('rate limit')) {
                    const waitTime = Math.min(60 * attempt, 300); // Max 5 minutes
                    console.log(`   ⏱️  Rate limited. Waiting ${waitTime} seconds...`);
                    await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
                } else {
                    console.log(`   ❌ Attempt ${attempt} error: ${error.message}`);
                }
            }

            if (attempt < retries) {
                await new Promise(resolve => setTimeout(resolve, 10000)); // 10 second delay
            }
        }

        return null;
    }

    async processUrl(url, index, total) {
        console.log(`🌐 [${index + 1}/${total}] Processing: ${url}`);
        
        const result = await this.scrapeUrlWithRetry(url);
        
        if (!result || !result.extract) {
            console.log(`   ❌ No data extracted`);
            return [];
        }

        const services = Array.isArray(result.extract) ? result.extract : [result.extract];
        const validServices = [];

        for (const service of services) {
            if (this.isValidMountIsaService(service)) {
                validServices.push({
                    ...service,
                    source_url: url,
                    extraction_confidence: 0.83
                });
            }
        }

        console.log(`   ✅ Found ${validServices.length} valid Mount Isa services`);
        return validServices;
    }

    isValidMountIsaService(service) {
        if (!service || !service.name || service.name.length < 3) {
            return false;
        }

        const searchText = `
            ${service.name || ''} 
            ${service.description || ''} 
            ${service.address || ''}
        `.toLowerCase();

        // Must have Mount Isa connection
        const mountIsaTerms = [
            'mount isa', 'mt isa', 'mountisa',
            '4825', '4828', '4829', '4830',
            'north west queensland'
        ];

        const hasMountIsaConnection = mountIsaTerms.some(term => 
            searchText.includes(term)
        );

        // Must have some contact info or meaningful description
        const hasSubstance = (
            service.phone || 
            service.email || 
            service.address || 
            (service.description && service.description.length > 20)
        );

        return hasMountIsaConnection && hasSubstance;
    }

    async saveServices(services) {
        if (services.length === 0) return 0;

        let savedCount = 0;
        const client = await this.db.connect();

        try {
            for (const service of services) {
                try {
                    const cleanService = {
                        name: service.name?.trim() || 'Unknown Service',
                        description: service.description?.trim() || 'Service in Mount Isa',
                        phone: this.cleanPhone(service.phone),
                        email: this.cleanEmail(service.email),
                        website: service.website || service.source_url,
                        address: service.address?.trim() || null,
                        category: service.category || 'general'
                    };

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
                        source_url: service.source_url,
                        extraction_method: 'scaled_firecrawl_v2',
                        scraped_at: new Date().toISOString(),
                        category: service.category
                    };

                    await client.query(query, [
                        cleanService.name,
                        cleanService.description,
                        cleanService.phone,
                        cleanService.email,
                        cleanService.website,
                        cleanService.address,
                        'Mount Isa',
                        '4825',
                        'QLD',
                        'scaled_research_v2',
                        service.extraction_confidence || 0.83,
                        JSON.stringify(metadata),
                        new Date()
                    ]);

                    savedCount++;
                    console.log(`   💾 Saved: ${cleanService.name}`);

                } catch (dbError) {
                    if (dbError.code !== '23505') { // Ignore duplicates
                        console.log(`   ⚠️  DB error: ${dbError.message}`);
                    }
                }
            }

        } finally {
            client.release();
        }

        return savedCount;
    }

    cleanPhone(phone) {
        if (!phone) return null;
        const match = phone.match(/(\+61\s*7|07|\(07\))\s*\d{4}\s*\d{4}/);
        return match ? match[0].trim() : null;
    }

    cleanEmail(email) {
        if (!email) return null;
        const match = email.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/);
        return match ? match[0] : null;
    }

    async runScaledResearch() {
        console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                🎯 SCALED MOUNT ISA SERVICE DISCOVERY v2 🎯                   ║
║                                                                               ║
║  Optimized for API rate limits while maximizing service discovery            ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        `);

        console.log('🚀 SCALED RESEARCH STRATEGY:');
        console.log(`   📊 ${this.priorityTargets.length} high-priority URLs to scrape`);
        console.log('   🎯 Focused on Mount Isa specific pages');
        console.log('   ⏱️  Built-in rate limiting and retry logic');
        console.log('   💾 Automatic deduplication and database storage');
        console.log();

        let totalFound = 0;
        let totalSaved = 0;
        const startTime = Date.now();

        for (const [index, url] of this.priorityTargets.entries()) {
            const services = await this.processUrl(url, index, this.priorityTargets.length);
            totalFound += services.length;

            if (services.length > 0) {
                const saved = await this.saveServices(services);
                totalSaved += saved;
            }

            // Progress update
            const elapsed = (Date.now() - startTime) / 1000 / 60;
            console.log(`   📊 Progress: ${index + 1}/${this.priorityTargets.length} URLs, ${totalSaved} services saved, ${elapsed.toFixed(1)}min elapsed`);
            
            // Rate limiting between requests
            if (index < this.priorityTargets.length - 1) {
                console.log(`   ⏱️  Waiting 30 seconds before next URL...`);
                await new Promise(resolve => setTimeout(resolve, 30000));
            }
            console.log();
        }

        // Final summary
        const totalTime = (Date.now() - startTime) / 1000 / 60;
        
        console.log('='.repeat(70));
        console.log('🎉 SCALED RESEARCH COMPLETE');
        console.log('='.repeat(70));
        console.log(`🔍 Total services found: ${totalFound}`);
        console.log(`💾 Total services saved: ${totalSaved}`);
        console.log(`🎯 Success rate: ${totalFound > 0 ? ((totalSaved/totalFound)*100).toFixed(1) : 0}%`);
        console.log(`⏱️  Total time: ${totalTime.toFixed(1)} minutes`);
        console.log();

        console.log('🎉 Research complete!');
        console.log('🌐 Start your app: npm start');
        console.log('📱 View services at: http://localhost:8888');
        
        await this.db.end();
        return { found: totalFound, saved: totalSaved };
    }
}

async function main() {
    try {
        const researcher = new ScaledMountIsaResearcher();
        await researcher.runScaledResearch();
    } catch (error) {
        console.error('❌ Scaled research failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = ScaledMountIsaResearcher;