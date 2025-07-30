# Production Database Setup Instructions

## Step 1: Create Vercel Postgres Database
1. Go to https://vercel.com/dashboard
2. Click on your `mount-isa-service-map` project  
3. Go to **Storage** tab → **Create Database** → **Postgres**
4. Name it `mount-isa-db` and click **Create**

## Step 2: Add Environment Variables to Vercel
Copy these from your Vercel Postgres dashboard and add to your project's Environment Variables:

```env
POSTGRES_URL="postgresql://..."
POSTGRES_PRISMA_URL="postgresql://..."
POSTGRES_URL_NON_POOLING="postgresql://..."
POSTGRES_USER="..."
POSTGRES_HOST="..."
POSTGRES_PASSWORD="..."
POSTGRES_DATABASE="..."
```

Also add these manually in Vercel:
```env
DB_HOST=[copy from POSTGRES_HOST]
DB_NAME=[copy from POSTGRES_DATABASE] 
DB_USER=[copy from POSTGRES_USER]
DB_PASSWORD=[copy from POSTGRES_PASSWORD]
DB_PORT=5432
```

## Step 3: Initialize Production Database
Run these commands locally with production credentials:

```bash
# Create .env.production with production database credentials
echo "DB_HOST=[your-production-host]
DB_NAME=[your-production-name]
DB_USER=[your-production-user]
DB_PASSWORD=[your-production-password]
DB_PORT=5432
JWT_SECRET=mount_isa_community_voices_jwt_2024_secure_key
SESSION_SECRET=mount_isa_session_secret_2024" > .env.production

# Initialize production database
NODE_ENV=production npm run init-db
NODE_ENV=production npm run import-data
```

## Step 4: Verify Setup
After deployment, your app should work at:
https://mount-isa-service-map.vercel.app

## Current Status
✅ App deployed to Vercel
✅ Basic environment variables set
⏳ Database creation needed
⏳ Database initialization needed