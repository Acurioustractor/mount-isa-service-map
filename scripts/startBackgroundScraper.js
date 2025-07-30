/**
 * Start Background Scraper Service
 * Initializes and starts the continuous service discovery system
 */

require('dotenv').config();
const BackgroundScraper = require('../background-scraper');

async function startBackgroundScraper() {
    console.log('🕷️ Initializing Mount Isa Background Scraper Service');
    
    const scraper = new BackgroundScraper();
    
    try {
        await scraper.start();
        
        console.log(`
✅ Background Scraper Service Started Successfully!

📊 Configuration:
- Runs every 6 hours
- Max 2 concurrent scrapers
- Logs to: scraper.log
- Stats saved to: scraper-stats.json

🔍 Active Scrapers:
- Queensland Government Services
- Indigenous HealthInfoNet
- Firecrawl Research System
- Expanded Source Discovery

📈 The scraper will continuously discover new Mount Isa services and update the database.

🛑 To stop: Press Ctrl+C or run 'node background-scraper.js stop'
        `);
        
        // Keep the process alive
        process.stdin.resume();
        
    } catch (error) {
        console.error('❌ Failed to start background scraper:', error);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    startBackgroundScraper();
}

module.exports = startBackgroundScraper;