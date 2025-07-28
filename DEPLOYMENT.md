# Deployment Guide

This guide covers deploying the Mount Isa Service Map to GitHub and Vercel.

## Prerequisites

- GitHub account
- Vercel account (free tier available)
- PostgreSQL database (for production)

## 1. GitHub Repository Setup

### Initial Repository Creation

1. Create a new repository on GitHub:
   - Go to [github.com/new](https://github.com/new)
   - Repository name: `mount-isa-service-map`
   - Description: "Community-led service mapping platform for Mount Isa with storytelling timeline and AI-powered community voice analysis"
   - Set to Public or Private as needed
   - Don't initialize with README (we have existing files)

### Push to GitHub

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Mount Isa Service Map with Community Engagement Features"

# Add remote origin (replace with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/mount-isa-service-map.git

# Push to GitHub
git push -u origin main
```

## 2. Database Setup for Production

### Option A: Vercel Postgres (Recommended)
1. In Vercel Dashboard, go to Storage
2. Create a new Postgres database
3. Note the connection details for environment variables

### Option B: External PostgreSQL
- Use services like Supabase, Railway, or Neon
- Create database and get connection string

### Database Schema Setup
Once you have a production database, run the schema:

```sql
-- Copy contents from database/schema.sql
-- and community-voice-schema.sql
```

## 3. Vercel Deployment

### Connect Repository to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure build settings:
   - **Framework Preset**: Other
   - **Build Command**: `npm install`
   - **Output Directory**: Leave empty
   - **Install Command**: `npm install`

### Environment Variables

In Vercel project settings, add these environment variables:

```
# Database (from your production database)
DB_HOST=your_production_db_host
DB_NAME=your_production_db_name
DB_USER=your_production_db_user
DB_PASSWORD=your_production_db_password
DB_PORT=5432

# Server
NODE_ENV=production

# Security (generate secure values)
JWT_SECRET=your_secure_jwt_secret
SESSION_SECRET=your_secure_session_secret

# Admin (for initial setup)
ADMIN_USERNAME=admin
ADMIN_EMAIL=your_admin_email
ADMIN_PASSWORD=your_secure_admin_password

# Optional: External APIs
FIRECRAWL_API_KEY=your_firecrawl_key_if_needed
```

### Deploy

1. Click "Deploy" in Vercel
2. Wait for build to complete
3. Visit your deployed site

## 4. Post-Deployment Setup

### Initialize Database

Once deployed, you may need to initialize your production database:

```bash
# If you have access to run scripts on production
node scripts/initDb.js
node scripts/importData.js
```

### Test the Application

1. Visit your Vercel URL
2. Test the welcome page loads correctly
3. Test navigation to services and story timeline
4. Test community voice recording (if database is set up)

## 5. Custom Domain (Optional)

1. In Vercel project settings, go to "Domains"
2. Add your custom domain
3. Follow DNS configuration instructions

## 6. Monitoring and Maintenance

### Vercel Analytics
- Enable Vercel Analytics in project settings
- Monitor page views and performance

### Database Monitoring
- Monitor database usage and performance
- Set up backup schedules

### Updates
```bash
# For future updates
git add .
git commit -m "Description of changes"
git push

# Vercel will automatically redeploy
```

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Vercel build logs
   - Ensure all dependencies are in package.json
   - Verify Node.js version compatibility

2. **Database Connection Errors**
   - Verify environment variables are correct
   - Check database server is accessible from Vercel
   - Ensure database exists and schema is applied

3. **Static File Issues**
   - Ensure frontend files are in the frontend/ directory
   - Check vercel.json routing configuration

4. **CSP Errors**
   - Review Content Security Policy settings in server.js
   - Ensure all inline scripts use proper event listeners

## Environment-Specific Notes

### Development
- Use localhost database
- Set NODE_ENV=development
- Use .env file (not committed to git)

### Production
- Use production database
- Set NODE_ENV=production
- Use Vercel environment variables
- Enable security headers and HTTPS

## Support

For deployment issues:
1. Check Vercel documentation
2. Review GitHub repository issues
3. Contact the development team

---

## Quick Reference Commands

```bash
# Local development
npm run dev

# Production start
npm start

# Database initialization
node scripts/initDb.js

# Import sample data
node scripts/importData.js
```