# Mount Isa Service Map

A comprehensive service mapping system for Mount Isa and Lower Gulf communities, focusing on disability support, health services, and youth support.

## Overview

This project provides a platform to catalog, search, and manage community services in Mount Isa and surrounding areas. It includes:

- A public-facing directory for residents to find services
- An admin backend for service coordination and data management
- Web scraping capabilities to gather information from online sources
- Tools for manual data collection and import

## Features

### Public Directory
- Searchable service directory with filtering by category and location
- Responsive web interface accessible on desktop and mobile devices
- Detailed service information including contact details, hours, and eligibility

### Community Engagement Tools
- **Interview Recorder**: Capture community feedback through audio recordings
- **Engagement Dashboard**: Overview of community engagement activities
- **Service Gap Analysis**: Identify and prioritize service delivery gaps
- **Action Item Tracking**: Monitor responses to community needs
- **Interview Analysis**: AI-powered theme extraction from community conversations

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

## Installation

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

## Acknowledgments

This project was developed to support the community of Mount Isa and the Lower Gulf region in Queensland, Australia, with a focus on improving access to services for people with disabilities, health services, and youth support programs.
