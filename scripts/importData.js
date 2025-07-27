#!/usr/bin/env node

// Script to import initial data into the database

const { importInitialServices } = require('../utils/dataImport');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

async function importData() {
  try {
    console.log('Importing initial service data...');
    
    const results = await importInitialServices();
    
    console.log('Import completed!');
    console.log(`Imported: ${results.imported} services`);
    console.log(`Skipped: ${results.skipped} services`);
    
    if (results.errors.length > 0) {
      console.log('Errors:');
      results.errors.forEach(error => {
        console.log(`- ${error.service}: ${error.error}`);
      });
    }
  } catch (error) {
    console.error('Error importing data:', error);
    process.exit(1);
  }
}

// Run import if script is called directly
if (require.main === module) {
  importData();
}

module.exports = { importData };
