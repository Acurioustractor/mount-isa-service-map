#!/usr/bin/env node

// Script to run web scrapers and collect service information

const { ScraperManager } = require('../scrapers');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

async function runScrapers() {
  try {
    console.log('Running web scrapers...');
    
    const scraperManager = new ScraperManager();
    const results = await scraperManager.runAllScrapers();
    
    console.log('Scraping completed!');
    console.log(`Found ${results.services.length} services from all scrapers`);
    
    if (results.errors.length > 0) {
      console.log('Errors:');
      results.errors.forEach(error => {
        console.log(`- ${error.scraper}: ${error.error}`);
      });
    }
    
    // Display sample of found services
    console.log('\nSample services found:');
    results.services.slice(0, 5).forEach((service, index) => {
      console.log(`${index + 1}. ${service.name} (${service.category})`);
      console.log(`   ${service.description}`);
      console.log(`   Source: ${service.source}`);
      console.log(`   URL: ${service.url}\n`);
    });
    
    if (results.services.length > 5) {
      console.log(`... and ${results.services.length - 5} more services`);
    }
  } catch (error) {
    console.error('Error running scrapers:', error);
    process.exit(1);
  }
}

// Run scrapers if script is called directly
if (require.main === module) {
  runScrapers();
}

module.exports = { runScrapers };
