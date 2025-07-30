/**
 * Background Service Scraper - Continuous Discovery
 * Runs scrapers on a loop to continuously discover new Mount Isa services
 */

const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');

class BackgroundScraper {
    constructor() {
        this.isRunning = false;
        this.intervalId = null;
        this.logFile = path.join(__dirname, 'scraper.log');
        this.statsFile = path.join(__dirname, 'scraper-stats.json');
        
        // Scraper configuration
        this.config = {
            interval: 6 * 60 * 60 * 1000, // Run every 6 hours
            scrapers: [
                'qld-gov-services-extractor.js',
                'healthinfonet-focused-extractor.js',
                'comprehensive-firecrawl-research.js',
                'expanded-source-discovery.js'
            ],
            maxConcurrent: 2, // Run max 2 scrapers at once
            retryAttempts: 3,
            retryDelay: 30 * 60 * 1000 // 30 minutes between retries
        };
    }

    async start() {
        if (this.isRunning) {
            await this.log('Background scraper already running');
            return;
        }

        this.isRunning = true;
        await this.log('🚀 Starting background scraper service');
        await this.updateStats({ status: 'started', startTime: new Date().toISOString() });

        // Run initial scrape
        await this.runScrapingCycle();

        // Set up interval for continuous scraping
        this.intervalId = setInterval(async () => {
            await this.runScrapingCycle();
        }, this.config.interval);

        await this.log(`✅ Background scraper started - running every ${this.config.interval / (60 * 60 * 1000)} hours`);
    }

    async stop() {
        if (!this.isRunning) {
            return;
        }

        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }

        await this.log('🛑 Background scraper stopped');
        await this.updateStats({ status: 'stopped', stopTime: new Date().toISOString() });
    }

    async runScrapingCycle() {
        const cycleStart = new Date();
        await this.log(`\n📊 Starting scraping cycle at ${cycleStart.toISOString()}`);

        const results = {
            success: 0,
            failed: 0,
            errors: [],
            newServices: 0
        };

        // Get initial service count
        const initialCount = await this.getCurrentServiceCount();

        // Run scrapers in batches to avoid overwhelming system
        for (let i = 0; i < this.config.scrapers.length; i += this.config.maxConcurrent) {
            const batch = this.config.scrapers.slice(i, i + this.config.maxConcurrent);
            const batchPromises = batch.map(scraper => this.runScraper(scraper));
            
            const batchResults = await Promise.allSettled(batchPromises);
            
            batchResults.forEach((result, index) => {
                if (result.status === 'fulfilled') {
                    results.success++;
                    this.log(`✅ ${batch[index]} completed successfully`);
                } else {
                    results.failed++;
                    results.errors.push(`${batch[index]}: ${result.reason}`);
                    this.log(`❌ ${batch[index]} failed: ${result.reason}`);
                }
            });

            // Wait between batches to avoid overwhelming the system
            if (i + this.config.maxConcurrent < this.config.scrapers.length) {
                await this.sleep(30000); // 30 second delay between batches
            }
        }

        // Get final service count
        const finalCount = await this.getCurrentServiceCount();
        results.newServices = Math.max(0, finalCount - initialCount);

        const cycleEnd = new Date();
        const duration = Math.round((cycleEnd - cycleStart) / 1000);

        await this.log(`\n📈 Scraping cycle completed in ${duration}s`);
        await this.log(`📊 Results: ${results.success} success, ${results.failed} failed, ${results.newServices} new services discovered`);

        if (results.errors.length > 0) {
            await this.log(`⚠️ Errors: ${results.errors.join(', ')}`);
        }

        // Update statistics
        await this.updateStats({
            lastRun: cycleEnd.toISOString(),
            duration: duration,
            results: results,
            totalServices: finalCount
        });

        return results;
    }

    async runScraper(scraperFile) {
        return new Promise((resolve, reject) => {
            const scraperPath = path.join(__dirname, scraperFile);
            
            // Check if scraper file exists
            fs.access(scraperPath).then(() => {
                const command = `node "${scraperPath}"`;
                
                exec(command, { 
                    timeout: 10 * 60 * 1000, // 10 minute timeout per scraper
                    cwd: __dirname 
                }, (error, stdout, stderr) => {
                    if (error) {
                        reject(`Execution error: ${error.message}`);
                        return;
                    }
                    
                    if (stderr && !stderr.includes('Warning')) {
                        reject(`Scraper error: ${stderr}`);
                        return;
                    }
                    
                    resolve(stdout);
                });
            }).catch(() => {
                reject(`Scraper file not found: ${scraperPath}`);
            });
        });
    }

    async getCurrentServiceCount() {
        return new Promise((resolve) => {
            const { Pool } = require('pg');
            const pool = new Pool({
                host: process.env.DB_HOST || 'localhost',
                database: process.env.DB_NAME || 'mount_isa_services',
                user: process.env.DB_USER || 'benknight',
                port: process.env.DB_PORT || '5432'
            });

            pool.query('SELECT COUNT(*) as count FROM services WHERE is_active = $1', [true])
                .then(result => {
                    pool.end();
                    resolve(parseInt(result.rows[0].count) || 0);
                })
                .catch(err => {
                    pool.end();
                    this.log(`Database error: ${err.message}`);
                    resolve(0);
                });
        });
    }

    async log(message) {
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] ${message}\n`;
        
        console.log(message);
        
        try {
            await fs.appendFile(this.logFile, logMessage);
        } catch (error) {
            console.error('Failed to write to log file:', error);
        }
    }

    async updateStats(stats) {
        try {
            let currentStats = {};
            try {
                const data = await fs.readFile(this.statsFile, 'utf8');
                currentStats = JSON.parse(data);
            } catch (error) {
                // File doesn't exist or is invalid, start fresh
            }

            const updatedStats = {
                ...currentStats,
                ...stats,
                lastUpdated: new Date().toISOString()
            };

            await fs.writeFile(this.statsFile, JSON.stringify(updatedStats, null, 2));
        } catch (error) {
            await this.log(`Failed to update stats: ${error.message}`);
        }
    }

    async getStats() {
        try {
            const data = await fs.readFile(this.statsFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            return { error: 'No stats available' };
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Graceful shutdown
    async shutdown() {
        await this.log('🔄 Graceful shutdown initiated');
        await this.stop();
        process.exit(0);
    }
}

// Handle process signals for graceful shutdown
const scraper = new BackgroundScraper();

process.on('SIGINT', async () => {
    console.log('\n🛑 Received SIGINT, shutting down gracefully...');
    await scraper.shutdown();
});

process.on('SIGTERM', async () => {
    console.log('\n🛑 Received SIGTERM, shutting down gracefully...');
    await scraper.shutdown();
});

// CLI interface
if (require.main === module) {
    const command = process.argv[2];
    
    switch (command) {
        case 'start':
            scraper.start().catch(console.error);
            break;
        case 'stop':
            scraper.stop().catch(console.error);
            break;
        case 'stats':
            scraper.getStats().then(stats => {
                console.log('📊 Scraper Statistics:');
                console.log(JSON.stringify(stats, null, 2));
            });
            break;
        case 'once':
            scraper.runScrapingCycle().then(results => {
                console.log('🎯 Single scraping cycle completed:', results);
                process.exit(0);
            }).catch(console.error);
            break;
        default:
            console.log(`
🕷️ Background Scraper Service

Usage:
  node background-scraper.js start   - Start continuous background scraping
  node background-scraper.js stop    - Stop background scraping
  node background-scraper.js once    - Run one scraping cycle
  node background-scraper.js stats   - Show scraping statistics

The scraper will run every 6 hours and discover new Mount Isa services automatically.
            `);
    }
}

module.exports = BackgroundScraper;