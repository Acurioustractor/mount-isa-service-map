/**
 * Test Firecrawl with a single page first
 */

require('dotenv').config();
const FirecrawlApp = require('@mendable/firecrawl-js').default;

async function testFirecrawl() {
    console.log('🔥 Testing Firecrawl with Mount Isa City Council...');
    
    const firecrawl = new FirecrawlApp({
        apiKey: process.env.FIRECRAWL_API_KEY
    });

    try {
        // Test with a single page first
        const result = await firecrawl.scrapeUrl('https://www.mountisa.qld.gov.au', {
            formats: ['extract'],
            extract: {
                prompt: `
                Find any services mentioned on this page that are located in Mount Isa, Queensland.
                Extract: service name, description, phone number, email, address
                Return as JSON array.
                `
            }
        });

        console.log('✅ Firecrawl test successful!');
        console.log('📊 Result:', JSON.stringify(result, null, 2));

    } catch (error) {
        console.log('❌ Firecrawl test failed:', error.message);
    }
}

testFirecrawl();