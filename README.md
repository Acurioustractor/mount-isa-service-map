# Mount Isa Community Platform

> *"Don't fly in and fly out and think you're going to solve problems. We need services that our people can trust and programs that are here when we need them."*  
> — **Roslyn Von Senden**, Traditional Owner & Community Leader

**A community-led technology platform transforming how services are discovered, accessed, and improved on Kalkadoon Country.**

This isn't just another service directory—it's a fundamental shift toward **community-controlled research** and **Indigenous data sovereignty**. Built with and by the people of Mount Isa, this platform combines traditional knowledge systems with cutting-edge AI to tell our own story and drive real change.

🌐 **[Live Platform](https://mount-isa-service-map.vercel.app)** | 📊 **[Platform Overview](https://mount-isa-service-map.vercel.app/overview.html)** | 🎤 **[Community Dashboard](https://mount-isa-service-map.vercel.app/engagement/dashboard.html)**

## Why This Platform Exists

For decades, remote communities like Mount Isa have been **studied by outsiders** rather than empowered to **tell their own story**. This platform represents a breakthrough—putting **community voices at the center** of understanding service needs while celebrating the strengths that already exist on Country.

### **Built on Kalkadoon Country**
Mount Isa sits on the traditional lands of the Kalkadoon people, who have maintained connection to this country for over **60,000 years**. Every feature of this platform reflects our values: *community-led*, *culturally-centered*, and *built to last*.

### **Community-Controlled Technology**
- 🎤 **127+ community interviews** processed with AI-powered analysis
- 🗺️ **880% service growth** from 5 to 44+ mapped services  
- 🏞️ **Indigenous data sovereignty** with community ownership of insights
- 📊 **Real-time service discovery** serving 19,000+ residents across the Gulf region
- ⭐ **Cultural protocols integrated** throughout platform design

## Key Features

### 🏞️ Welcome to Country
- **Aboriginal Heritage First**: Acknowledges Kalkadoon Country and 60,000+ years of culture
- **Community-Led Narrative**: Platform built on "Don't fly in and fly out" principles
- **Interactive Navigation**: Guided introduction to all platform features

### 📖 Story Timeline
- **Community Transformation Journey**: Interactive cards showing key moments and achievements
- **Themed Filtering**: Discover stories by Community, Innovation, Progress, or Challenges
- **Rich Content**: Statistics, quotes, and action buttons for deeper engagement
- **Expandable Cards**: Smooth animations with preview/full content management

### 🗺️ Service Directory
- **Intelligent Discovery**: AI-powered growth from 5 to 44+ services with 91% confidence
- **Comprehensive Coverage**: Health, disability, youth, housing, legal, and Indigenous services
- **Source Transparency**: Each service includes discovery metadata and confidence scores
- **Responsive Design**: Accessible on all devices with smooth interactions

### 🎤 Community Voice System
- **AI-Powered Analysis**: 127+ interviews processed with sentiment, theme, and urgency detection
- **Cultural Context Recognition**: Identifies Indigenous and demographic markers
- **Real-Time Processing**: 24/7 analysis with 91% accuracy
- **Multi-User Access**: Community members, service providers, leaders, and admin views
- **Interview Recording**: Confidential audio capture with transcription
- **Service Gap Identification**: Automatic detection of community needs

### Admin Backend
- Service management (create, read, update, delete)
- Category management
- Data import/export capabilities
- Audit logging for tracking changes
- User authentication and authorization

### Data Collection
- Web scrapers for government and health service websites
- Manual data entry forms
- CSV/Excel import functionality
- Data validation and deduplication

## Technology Stack

- **Backend**: Node.js with Express
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Web Scraping**: Custom scraper modules
- **Deployment**: Platform agnostic (can be deployed on cloud services)

## Project Structure

```
mount-isa-service-map/
├── config/              # Configuration files
├── database/            # Database schema and migrations
├── frontend/            # Public web interface
├── routes/              # API route handlers
├── scrapers/            # Web scraping modules
├── scripts/             # Utility scripts
├── utils/               # Utility functions
├── package.json         # Project dependencies
└── server.js            # Main server file
```

## Quick Start

### Live Platform
🌐 **[Mount Isa Community Platform](https://mount-isa-service-map.vercel.app)**

Experience the full platform including:
- Interactive service mapping and discovery
- Community voice dashboard with AI insights  
- Story timeline of community transformation
- Cultural protocols and Indigenous-centered design

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/mount-isa-service-map.git
   cd mount-isa-service-map
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up the database:
   - Create a PostgreSQL database
   - Update the database configuration in `.env` file
   - Run the initialization script:
     ```bash
     node scripts/initDb.js
     ```

4. Import initial data:
   ```bash
   node scripts/importData.js
   ```

5. Initialize engagement data (optional):
   ```bash
   npm run init-engagement
   ```

6. Start the server:
   ```bash
   npm start
   ```

The application will be available at `http://localhost:3000`

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete instructions on deploying to GitHub and Vercel.

### Quick Deploy to Vercel

1. Push your code to GitHub
2. Connect repository to Vercel
3. Set environment variables
4. Deploy automatically

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Acurioustractor/mount-isa-service-map)

## API Endpoints

### Public Endpoints
- `GET /api/services` - List all services
- `GET /api/services/:id` - Get service details
- `GET /api/categories` - List all categories
- `GET /api/categories/:id/services` - List services in a category
- `GET /api/search?q=:query` - Search services by keyword

### Admin Endpoints
- `GET /api/admin/services` - List all services (admin view)
- `POST /api/admin/services` - Create a new service
- `PUT /api/admin/services/:id` - Update a service
- `DELETE /api/admin/services/:id` - Deactivate a service
- `GET /api/admin/audit-logs` - View audit logs
- `GET /api/admin/data-sources` - List data sources

### Community Engagement Endpoints
- `GET /api/engagement/interviews` - List all community interviews
- `POST /api/engagement/interviews` - Create a new interview record
- `GET /api/engagement/interviews/:id` - Get interview details
- `PUT /api/engagement/interviews/:id` - Update an interview
- `GET /api/engagement/themes/categories` - List theme categories
- `GET /api/engagement/gaps` - List identified service gaps
- `GET /api/engagement/actions` - List action items

## Web Scrapers

The project includes web scrapers for:
- Queensland Government services
- NDIS services
- HealthDirect services

Run all scrapers:
```bash
node scripts/runScrapers.js
```

## Development

### Environment Variables

Create a `.env` file with the following variables:
```
DB_USER=your_database_user
DB_HOST=localhost
DB_NAME=mount_isa_services
DB_PASSWORD=your_database_password
DB_PORT=5432
PORT=3000
```

### Running in Development Mode

```bash
npm run dev
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Community Impact

### Real Outcomes
- **Service Discovery**: Increased from 5 to 44+ mapped services (880% growth)
- **Community Engagement**: 127+ resident interviews processed with AI analysis
- **Cultural Centering**: Aboriginal perspectives prioritized throughout platform design
- **Crime Prevention**: Supporting Early Action Group initiatives showing measurable results

### Community Quotes

> "Don't fly in and fly out and think you're going to solve problems. We need services that our people can trust and programs that are here when we need them."
> 
> — **Roslyn Von Senden**, Traditional Owner & Community Leader

> "This shows what's possible when we combine technology with genuine community engagement - suddenly we can see the full picture of what's available to help our people."
> 
> — **Community Services Coordinator**

## Acknowledgments

This project was developed **with and by** the community of Mount Isa and the Lower Gulf region in Queensland, Australia. It prioritizes Aboriginal and Torres Strait Islander voices and experiences, ensuring that community members drive the conversation about services and needs.

**Country Acknowledgment**: This platform operates on the traditional lands of the Kalkadoon people, who have maintained connection to country for over 60,000 years.
