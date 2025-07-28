/**
 * BATCH Mount Isa Research - Process in small batches to respect rate limits
 */

require('dotenv').config();
const { Pool } = require('pg');
const FirecrawlApp = require('@mendable/firecrawl-js').default;

class BatchMountIsaResearcher {
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

        // Break into small batches of 3-5 URLs each
        this.batches = [
            {
                name: "Mount Isa Council Services",
                urls: [
                    'https://www.mountisa.qld.gov.au/community',
                    'https://www.mountisa.qld.gov.au/residents', 
                    'https://www.mountisa.qld.gov.au/business'
                ]
            },
            {
                name: "Health Services",
                urls: [
                    'https://www.health.qld.gov.au/north-west',
                    'https://www.healthdirect.gov.au',
                    'https://www.beyondblue.org.au'
                ]
            },
            {
                name: "Community Organizations",
                urls: [
                    'https://www.salvationarmy.org.au',
                    'https://www.redcross.org.au',
                    'https://www.unitingcare.org.au'
                ]
            },
            {
                name: "Disability & Support",
                urls: [
                    'https://www.ndis.gov.au',
                    'https://www.dss.gov.au',
                    'https://www.qdn.org.au'
                ]
            },
            {
                name: "Education & Youth",
                urls: [
                    'https://www.eq.edu.au',
                    'https://www.pcyc.org.au',
                    'https://www.yfs.org.au'
                ]
            }
        ];
    }

    async processBatch(batch, batchIndex) {
        console.log(`\n📦 BATCH ${batchIndex + 1}: ${batch.name}`);
        console.log(`🎯 Processing ${batch.urls.length} URLs`);
        
        const batchServices = [];
        
        for (const [urlIndex, url] of batch.urls.entries()) {
            console.log(`   🔍 [${urlIndex + 1}/${batch.urls.length}] Scraping: ${url}`);
            
            try {
                const result = await this.firecrawl.scrapeUrl(url, {
                    formats: ['extract'],
                    extract: {
                        prompt: `
                        Find services in Mount Isa, Queensland (postcode 4825).
                        
                        Extract:
                        - name: Service/organization name
                        - description: What they provide
                        - phone: Phone number (07 47xx xxxx format)
                        - email: Email address
                        - address: Street address in Mount Isa
                        - category: Type of service
                        
                        Return as JSON array. Only Mount Isa services.
                        `
                    }
                });

                if (result.success && result.extract) {
                    const services = Array.isArray(result.extract) ? result.extract : [result.extract];
                    
                    const validServices = services.filter(service => {
                        if (!service || !service.name) return false;
                        
                        const text = `${service.name} ${service.description || ''} ${service.address || ''}`.toLowerCase();
                        return text.includes('mount isa') || text.includes('4825');
                    });

                    console.log(`      ✅ Found ${validServices.length} Mount Isa services`);
                    batchServices.push(...validServices.map(s => ({ ...s, source_url: url })));
                    
                } else {
                    console.log(`      ⚠️  No services found`);
                }

                // Wait between URLs in same batch
                if (urlIndex < batch.urls.length - 1) {
                    console.log(`      ⏱️  Waiting 20 seconds...`);
                    await new Promise(resolve => setTimeout(resolve, 20000));
                }

            } catch (error) {
                if (error.message.includes('429')) {
                    console.log(`      ⏱️  Rate limited. Waiting 2 minutes...`);
                    await new Promise(resolve => setTimeout(resolve, 120000));
                } else {
                    console.log(`      ❌ Error: ${error.message}`);
                }
            }
        }

        // Save batch results
        if (batchServices.length > 0) {
            const saved = await this.saveBatchServices(batchServices);
            console.log(`   💾 Batch complete: ${saved} services saved`);
        }

        return batchServices.length;
    }

    async saveBatchServices(services) {
        let savedCount = 0;
        const client = await this.db.connect();

        try {
            for (const service of services) {
                try {
                    const query = `
                        INSERT INTO services (
                            name, description, phone, email, website, address,
                            suburb, postcode, state, data_source, confidence_score,
                            discovery_date
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        RETURNING id;
                    `;

                    await client.query(query, [
                        service.name?.trim() || 'Unknown Service',
                        service.description?.trim() || 'Service in Mount Isa',
                        this.cleanPhone(service.phone),
                        this.cleanEmail(service.email),
                        service.source_url,
                        service.address?.trim(),
                        'Mount Isa',
                        '4825',
                        'QLD',
                        'batch_research',
                        0.80,
                        new Date()
                    ]);

                    savedCount++;

                } catch (dbError) {
                    if (dbError.code !== '23505') { // Not duplicate
                        console.log(`      ⚠️  DB error: ${dbError.message}`);
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
        const match = phone.match(/07\s*\d{4}\s*\d{4}/);
        return match ? match[0] : null;
    }

    cleanEmail(email) {
        if (!email) return null;
        const match = email.match(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/);
        return match ? match[0] : null;
    }

    async runBatchResearch() {
        console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   📦 BATCH MOUNT ISA SERVICE RESEARCH 📦                     ║
║                                                                               ║
║  Processing in small batches to respect API rate limits                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        `);

        console.log(`🎯 BATCH STRATEGY:`);
        console.log(`   📦 ${this.batches.length} batches to process`);
        console.log(`   🔍 ${this.batches.reduce((sum, b) => sum + b.urls.length, 0)} total URLs`);
        console.log(`   ⏱️  2-3 minute breaks between batches`);
        console.log();

        let totalFound = 0;
        const startTime = Date.now();

        for (const [batchIndex, batch] of this.batches.entries()) {
            const batchFound = await this.processBatch(batch, batchIndex);
            totalFound += batchFound;

            // Long break between batches to respect rate limits
            if (batchIndex < this.batches.length - 1) {
                console.log(`\n⏱️  BREAK: Waiting 3 minutes before next batch...`);
                await new Promise(resolve => setTimeout(resolve, 180000)); // 3 minutes
            }
        }

        const totalTime = (Date.now() - startTime) / 1000 / 60;

        console.log(`\n${'='.repeat(70)}`);
        console.log('🎉 BATCH RESEARCH COMPLETE');
        console.log('='.repeat(70));
        console.log(`🔍 Total services discovered: ${totalFound}`);
        console.log(`⏱️  Total time: ${totalTime.toFixed(1)} minutes`);
        console.log();
        console.log('🌐 View results: npm start → http://localhost:8888');

        await this.db.end();
        return totalFound;
    }
}

async function main() {
    try {
        const researcher = new BatchMountIsaResearcher();
        await researcher.runBatchResearch();
    } catch (error) {
        console.error('❌ Batch research failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = BatchMountIsaResearcher;