/**
 * Run Intelligent Mount Isa Service Research
 * Integrates with the existing Node.js application and database
 */

const { Pool } = require('pg');
const axios = require('axios');
const cheerio = require('cheerio');

class MountIsaServiceResearcher {
    constructor() {
        // Use existing database configuration from config/db.js
        this.db = new Pool({
            host: process.env.DB_HOST || 'localhost',
            database: process.env.DB_NAME || 'mount_isa_services',
            user: process.env.DB_USER || 'benknight',
            port: process.env.DB_PORT || '5432'
        });

        // Mount Isa service search queries
        this.searchQueries = [
            'Mount Isa Hospital Queensland Health',
            'Mount Isa Community Health Centre', 
            'Mount Isa disability services NDIS',
            'Mount Isa aged care services',
            'Mount Isa youth services PCYC',
            'Mount Isa mental health counselling',
            'Gidgee Healing Indigenous health Mount Isa',
            'Mount Isa neighbourhood centre community',
            'Salvation Army Mount Isa services',
            'Red Cross Mount Isa support',
            'Mount Isa medical centre GP',
            'Mount Isa family services childcare',
            'Mount Isa employment services',
            'Mount Isa legal aid services',
            'Mount Isa emergency services crisis'
        ];

        // Known Mount Isa service websites to check directly
        this.knownSites = [
            {
                url: 'https://www.health.qld.gov.au/north-west/mount-isa',
                name: 'Mount Isa Hospital - Queensland Health',
                type: 'health'
            },
            {
                url: 'https://www.mountisa.qld.gov.au/community/health-services', 
                name: 'Mount Isa City Council Health Services',
                type: 'health'
            },
            {
                url: 'https://gidgeehealing.org.au',
                name: 'Gidgee Healing',
                type: 'health'
            },
            {
                url: 'https://www.salvationarmy.org.au/find-us/qld/mount-isa',
                name: 'Salvation Army Mount Isa',
                type: 'community'
            },
            {
                url: 'https://www.redcross.org.au/get-help/find-services/mount-isa',
                name: 'Red Cross Mount Isa',
                type: 'community'
            }
        ];
    }

    async extractServiceFromSite(siteInfo) {
        console.log(`🔍 Extracting from: ${siteInfo.name}`);
        
        try {
            const response = await axios.get(siteInfo.url, {
                timeout: 10000,
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
            });

            const $ = cheerio.load(response.data);
            
            // Extract service information
            const service = {
                name: this.extractName($, siteInfo.name),
                description: this.extractDescription($),
                phone: this.extractPhone($),
                email: this.extractEmail($),
                website: siteInfo.url,
                address: this.extractAddress($),
                category: siteInfo.type,
                suburb: 'Mount Isa',
                postcode: '4825',
                state: 'QLD',
                confidence_score: 0.8,
                data_source: 'intelligent_research'
            };

            // Validate we got useful information
            if (service.name && (service.phone || service.email || service.address)) {
                return service;
            }

            return null;

        } catch (error) {
            console.log(`⚠️  Failed to extract from ${siteInfo.url}: ${error.message}`);
            return null;
        }
    }

    extractName($, fallbackName) {
        // Try title tag
        const title = $('title').text().trim();
        if (title && title.toLowerCase().includes('mount isa')) {
            return title;
        }

        // Try h1 tag
        const h1 = $('h1').first().text().trim();
        if (h1 && h1.length < 100) {
            return h1;
        }

        return fallbackName;
    }

    extractDescription($) {
        // Try meta description
        const metaDesc = $('meta[name="description"]').attr('content');
        if (metaDesc) {
            return metaDesc.trim();
        }

        // Try first meaningful paragraph
        const paragraphs = $('p');
        for (let i = 0; i < paragraphs.length; i++) {
            const text = $(paragraphs[i]).text().trim();
            if (text.length > 50 && text.length < 500) {
                return text;
            }
        }

        return 'Service provider in Mount Isa, Queensland';
    }

    extractPhone($) {
        const text = $.text();
        
        // Australian phone number patterns
        const phonePatterns = [
            /\(07\)\s*\d{4}\s*\d{4}/,  // (07) 4744 4444
            /07\s*\d{4}\s*\d{4}/,      // 07 4744 4444
            /\d{2}\s*4744\s*\d{4}/,    // Mount Isa area code
            /\d{2}\s*4749\s*\d{4}/     // Mount Isa area code
        ];

        for (const pattern of phonePatterns) {
            const match = text.match(pattern);
            if (match) {
                return match[0].trim();
            }
        }

        return null;
    }

    extractEmail($) {
        const text = $.text();
        const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/;
        
        const match = text.match(emailPattern);
        if (match) {
            const email = match[0];
            // Filter out obvious non-contact emails
            if (!email.toLowerCase().includes('noreply') && 
                !email.toLowerCase().includes('no-reply')) {
                return email;
            }
        }

        return null;
    }

    extractAddress($) {
        const text = $.text();
        
        // Mount Isa address patterns
        const addressPatterns = [
            /\d+[A-Za-z]?\s+[A-Za-z\s]+(Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Court|Ct)[^,\n]*(?:Mount Isa|Mt Isa)/i,
            /[A-Za-z\s]+(Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Court|Ct)[^,\n]*(?:Mount Isa|Mt Isa)/i
        ];

        for (const pattern of addressPatterns) {
            const match = text.match(pattern);
            if (match && match[0].length < 200) {
                return match[0].trim();
            }
        }

        return null;
    }

    async saveService(service) {
        console.log(`💾 Saving: ${service.name}`);

        try {
            const client = await this.db.connect();
            
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

            console.log(`✅ Saved service: ${service.name} (ID: ${serviceId})`);
            return serviceId;

        } catch (error) {
            console.log(`❌ DB Error for ${service.name}: ${error.message}`);
            return null;
        }
    }

    async runResearch() {
        console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║           🔍 MOUNT ISA INTELLIGENT SERVICE RESEARCH RUNNER 🔍                ║
║                                                                               ║
║  Automatically discovers Mount Isa services and saves to database            ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        `);

        console.log('🚀 Starting Mount Isa service discovery...');
        console.log(`📊 Checking ${this.knownSites.length} known service websites`);
        console.log();

        const discoveredServices = [];
        let savedCount = 0;

        // Extract from known sites
        for (const [index, site] of this.knownSites.entries()) {
            console.log(`🔎 [${index + 1}/${this.knownSites.length}] Processing: ${site.name}`);
            
            const service = await this.extractServiceFromSite(site);
            
            if (service) {
                discoveredServices.push(service);
                
                const serviceId = await this.saveService(service);
                if (serviceId) {
                    savedCount++;
                }
            } else {
                console.log(`   ⚠️  No useful information extracted`);
            }

            // Wait between requests to be respectful
            await new Promise(resolve => setTimeout(resolve, 2000));
            console.log();
        }

        // Summary
        console.log('='.repeat(60));
        console.log('📈 DISCOVERY COMPLETE');
        console.log('='.repeat(60));
        console.log(`🔍 Services discovered: ${discoveredServices.length}`);
        console.log(`💾 Services saved to database: ${savedCount}`);
        console.log();

        if (discoveredServices.length > 0) {
            console.log('🏆 DISCOVERED SERVICES:');
            discoveredServices.forEach((service, index) => {
                console.log(`   ${index + 1}. ${service.name}`);
                console.log(`      📞 ${service.phone || 'No phone'}`);
                console.log(`      ✉️  ${service.email || 'No email'}`);
                console.log(`      🌐 ${service.website}`);
                console.log(`      📍 ${service.address || 'No address'}`);
                console.log(`      ⭐ Confidence: ${(service.confidence_score * 100).toFixed(0)}%`);
                console.log();
            });
        }

        console.log('🎉 Research completed!');
        console.log('📊 Check your services table in the database for new entries');

        await this.db.end();
        return discoveredServices;
    }
}

// Run the research
async function main() {
    try {
        const researcher = new MountIsaServiceResearcher();
        await researcher.runResearch();
    } catch (error) {
        console.error('❌ Research failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = MountIsaServiceResearcher;