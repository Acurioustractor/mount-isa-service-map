# 🚀 Vercel Deployment Guide

## Quick Deploy to Vercel

### Step 1: Import Project
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"New Project"**
3. Import: `https://github.com/Acurioustractor/mount-isa-service-map`

### Step 2: Environment Variables
Copy and paste these into Vercel Environment Variables section:

```env
NODE_ENV=production
PORT=3000
JWT_SECRET=mount_isa_community_voices_jwt_2024_secure_key_change_this
SESSION_SECRET=mount_isa_session_secret_2024_change_this_too
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@mountisa.community
ADMIN_PASSWORD=MountIsa2024!Admin
```

### Step 3: Database Setup (Choose One Option)

#### Option A: Vercel Postgres (Recommended)
1. In Vercel Dashboard → **Storage** → **Create Database** → **Postgres**
2. Copy the connection details and add to Environment Variables:

```env
DB_HOST=[from Vercel Postgres dashboard]
DB_NAME=[from Vercel Postgres dashboard]
DB_USER=[from Vercel Postgres dashboard]
DB_PASSWORD=[from Vercel Postgres dashboard]
DB_PORT=5432
```

#### Option B: Supabase (Free Alternative)
1. Go to [supabase.com](https://supabase.com) → Create project
2. Go to Settings → Database → Copy connection string
3. Add to Vercel Environment Variables:

```env
DB_HOST=db.[your-project].supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[your-supabase-password]
DB_PORT=5432
```

### Step 4: Deploy
Click **"Deploy"** and wait 2-3 minutes!

### Step 5: Initialize Database
After deployment, run database setup:

**Download and run locally:**
```bash
git clone https://github.com/Acurioustractor/mount-isa-service-map
cd mount-isa-service-map
npm install

# Create .env with production database credentials
echo "DB_HOST=[your-production-host]
DB_NAME=[your-production-name]
DB_USER=[your-production-user]
DB_PASSWORD=[your-production-password]
DB_PORT=5432" > .env

# Initialize database
npm run init-db
npm run import-data
```

## 🎉 You're Live!

Your platform will be available at: `https://[your-project-name].vercel.app`

### Test These Features:
- ✅ Welcome page with Aboriginal heritage focus
- ✅ Interactive service map with fullscreen mode
- ✅ Story timeline with community transformation
- ✅ Service directory with 44+ services
- ✅ Community voice recording system

---

## Troubleshooting

**Build Fails:** Check Vercel build logs for specific errors  
**Database Connection:** Verify environment variables are correctly set  
**Map Not Loading:** Ensure all environment variables are added  
**Services Not Showing:** Run database initialization scripts  

Need help? The platform includes comprehensive documentation and support.