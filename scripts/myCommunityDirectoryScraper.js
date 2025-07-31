#!/usr/bin/env node

/**
 * My Community Directory Scraper for Mount Isa
 * Extracts services from mycommunitydirectory.com.au
 */

const axios = require('axios');
const cheerio = require('cheerio');
const { supabase } = require('../config/supabase');

class MyCommunityDirectoryScraper {
    constructor() {
        this.baseUrl = 'https://www.mycommunitydirectory.com.au';
        this.mountIsaUrl = '/Queensland/Mount_Isa';
        this.services = [];
        this.categories = {};
    }

    async scrapeDirectory() {
        console.log('🕷️ Starting My Community Directory Scraper for Mount Isa');
        console.log('=====================================================\n');

        await this.loadCategories();

        // Scrape main categories
        const mainCategories = [
            { path: '/Aboriginal_Services', category: 'Community Support' },
            { path: '/Welfare_Assistance___Services', category: 'Community Support' },
            { path: '/Disability_Services', category: 'Disability Support' },
            { path: '/Education', category: 'Education & Training' },
            { path: '/Health', category: 'Health Services' },
            { path: '/Sport', category: 'Recreation & Activities' },
            { path: '/Community_Clubs___Interest_Groups', category: 'Recreation & Activities' },
            { path: '/Child_Care___Family_Day_Care', category: 'Education & Training' },
            { path: '/Mental_Health', category: 'Mental Health' },
            { path: '/Youth_Services___Youth_Groups', category: 'Youth Support' }
        ];

        for (const cat of mainCategories) {
            await this.scrapeCategoryPage(cat.path, cat.category);
        }

        await this.saveServices();

        console.log('\n✅ Scraping complete!');
        console.log(`Total services found: ${this.services.length}`);
    }

    async loadCategories() {
        const { data: categories } = await supabase
            .from('service_categories')
            .select('*');
        
        categories.forEach(cat => {
            this.categories[cat.name] = cat.id;
        });
    }

    async scrapeCategoryPage(categoryPath, defaultCategory) {
        try {
            const url = `${this.baseUrl}${this.mountIsaUrl}${categoryPath}`;
            console.log(`\n🔍 Scraping category: ${categoryPath}`);
            console.log(`📍 URL: ${url}`);

            const response = await axios.get(url, {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            });

            const $ = cheerio.load(response.data);

            // Look for service listings
            $('.service-listing, .listing-item, .result-item, [class*="service"]').each((index, element) => {
                const $elem = $(element);
                
                // Extract service information
                const name = $elem.find('h2, h3, .title, .name').first().text().trim() ||
                           $elem.find('a').first().text().trim();
                
                if (!name || name.length < 3) return;

                const description = $elem.find('.description, .summary, p').first().text().trim();
                const phone = this.extractPhone($elem.text());
                const address = this.extractAddress($elem);
                const website = $elem.find('a[href*="http"]').attr('href');

                if (name && !this.isDuplicate(name)) {
                    const service = {
                        name: name.substring(0, 100), // Limit name length
                        description: description || `${defaultCategory} service in Mount Isa`,
                        category: defaultCategory,
                        phone: phone,
                        address: address || 'Mount Isa QLD 4825',
                        website: website,
                        confidence: 80
                    };

                    this.services.push(service);
                    console.log(`✅ Found: ${service.name}`);
                }
            });

            // Also check for links to individual services
            $('a[href*="/service/"], a[href*="/organisation/"]').each((index, element) => {
                const $link = $(element);
                const serviceName = $link.text().trim();
                const serviceUrl = $link.attr('href');

                if (serviceName && !this.isDuplicate(serviceName) && serviceUrl) {
                    // For now, just add basic info - could enhance to scrape individual pages
                    const service = {
                        name: serviceName.substring(0, 100),
                        description: `${defaultCategory} service in Mount Isa`,
                        category: defaultCategory,
                        address: 'Mount Isa QLD 4825',
                        website: serviceUrl.startsWith('http') ? serviceUrl : `${this.baseUrl}${serviceUrl}`,
                        confidence: 75
                    };

                    this.services.push(service);
                    console.log(`✅ Found: ${service.name}`);
                }
            });

            console.log(`Found ${this.services.length} services in this category`);

        } catch (error) {
            console.error(`❌ Error scraping ${categoryPath}: ${error.message}`);
        }
    }

    extractPhone(text) {
        // Australian phone number patterns
        const phonePattern = /(?:\+?61|0)[2-9]\s?\d{4}\s?\d{4}|\(0[2-9]\)\s?\d{4}\s?\d{4}|13\s?\d{2}\s?\d{2}|1[38]00\s?\d{3}\s?\d{3}/g;
        const matches = text.match(phonePattern);
        if (matches) {
            // Clean and return first match
            return matches[0].replace(/\s+/g, ' ').trim().substring(0, 20);
        }
        return null;
    }

    extractAddress(element) {
        const text = element.text();
        // Look for Mount Isa addresses
        const addressPattern = /\d+[^,\n]*(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Circuit|Ct)[^,\n]*Mount Isa[^,\n]*QLD[^,\n]*482\d/i;
        const match = text.match(addressPattern);
        return match ? match[0].trim() : null;
    }

    isDuplicate(name) {
        return this.services.some(s => 
            s.name.toLowerCase() === name.toLowerCase() ||
            this.similarityScore(s.name, name) > 0.8
        );
    }

    similarityScore(str1, str2) {
        const s1 = str1.toLowerCase();
        const s2 = str2.toLowerCase();
        
        if (s1 === s2) return 1;
        
        // Check if one contains the other
        if (s1.includes(s2) || s2.includes(s1)) return 0.9;
        
        // Basic similarity check
        const words1 = s1.split(/\s+/);
        const words2 = s2.split(/\s+/);
        const commonWords = words1.filter(w => words2.includes(w));
        
        return commonWords.length / Math.max(words1.length, words2.length);
    }

    async saveServices() {
        console.log('\n💾 Saving discovered services to database...');
        
        let savedCount = 0;
        let skippedCount = 0;

        for (const service of this.services) {
            try {
                // Check if service already exists
                const { data: existing } = await supabase
                    .from('services')
                    .select('id')
                    .eq('name', service.name)
                    .single();

                if (existing) {
                    skippedCount++;
                    continue;
                }

                const { error } = await supabase
                    .from('services')
                    .insert([{
                        name: service.name,
                        description: service.description,
                        category_id: this.categories[service.category] || this.categories['Community Support'],
                        phone: service.phone,
                        website: service.website,
                        address: service.address,
                        suburb: 'Mount Isa',
                        state: 'QLD',
                        postcode: '4825',
                        is_active: true
                    }]);

                if (!error) {
                    savedCount++;
                    console.log(`✅ Saved: ${service.name}`);
                }

            } catch (error) {
                console.error(`❌ Error with ${service.name}: ${error.message}`);
            }
        }

        console.log(`\n📊 Results: ${savedCount} saved, ${skippedCount} skipped`);
    }
}

// Run the scraper
if (require.main === module) {
    const scraper = new MyCommunityDirectoryScraper();
    
    scraper.scrapeDirectory()
        .then(() => {
            console.log('\n🎉 My Community Directory scraping completed!');
            process.exit(0);
        })
        .catch(error => {
            console.error('\n❌ Scraping failed:', error);
            process.exit(1);
        });
}

module.exports = MyCommunityDirectoryScraper;