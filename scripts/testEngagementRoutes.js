const express = require('express');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

async function testEngagementRoutes() {
  console.log('Testing Community Engagement Routes...\n');
  
  try {
    // Start the server in the background
    console.log('Starting server...');
    const serverProcess = exec('npm start');
    
    // Wait a moment for the server to start
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Test routes
    const routes = [
      '/',
      '/api/engagement/interviews',
      '/api/engagement/themes/categories',
      '/api/engagement/gaps',
      '/api/engagement/actions'
    ];
    
    for (const route of routes) {
      try {
        console.log(`Testing route: ${route}`);
        const { stdout, stderr } = await execPromise(`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000${route}`);
        const statusCode = stdout.trim();
        
        if (statusCode === '200') {
          console.log(`✓ ${route} - Status: ${statusCode}`);
        } else {
          console.log(`✗ ${route} - Status: ${statusCode}`);
        }
      } catch (error) {
        console.log(`✗ ${route} - Error: ${error.message}`);
      }
    }
    
    // Kill the server process
    serverProcess.kill();
    console.log('\nServer stopped.');
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}

// Run the tests
testEngagementRoutes();
