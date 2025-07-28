const db = require('../config/db');

async function initEngagementData() {
  try {
    console.log('Initializing engagement data...');
    
    // Insert sample locations
    const locations = [
      { name: 'Mount Isa', type: 'city', population: 25000, remoteness_category: 'Remote' },
      { name: 'Mornington Island', type: 'community', population: 1200, remoteness_category: 'Very Remote' },
      { name: 'Normanton', type: 'town', population: 1800, remoteness_category: 'Remote' },
      { name: 'Doomadgee', type: 'community', population: 900, remoteness_category: 'Very Remote' }
    ];
    
    for (const location of locations) {
      const query = `
        INSERT INTO locations (name, type, population, remoteness_category)
        VALUES ($1, $2, $3, $4)
      `;
      await db.query(query, [location.name, location.type, location.population, location.remoteness_category]);
    }
    
    console.log('Inserted sample locations');
    
    // Insert sample theme categories
    const themes = [
      { name: 'Long Wait Times', description: 'Issues with service wait times', color_code: '#dc3545' },
      { name: 'Access Barriers', description: 'Geographic or other barriers to accessing services', color_code: '#fd7e14' },
      { name: 'Telehealth', description: 'Remote consultation options', color_code: '#ffc107' },
      { name: 'Staffing Shortages', description: 'Insufficient staff to meet demand', color_code: '#28a745' },
      { name: 'Emergency Department Use', description: 'Reliance on emergency services for non-emergency care', color_code: '#007bff' },
      { name: 'Transport Issues', description: 'Challenges with transportation to services', color_code: '#6f42c1' },
      { name: 'Cultural Safety', description: 'Concerns about cultural appropriateness of services', color_code: '#e83e8c' },
      { name: 'Youth Engagement', description: 'Challenges engaging young people with services', color_code: '#20c997' }
    ];
    
    for (const theme of themes) {
      const query = `
        INSERT INTO theme_categories (name, description, color_code)
        VALUES ($1, $2, $3)
      `;
      await db.query(query, [theme.name, theme.description, theme.color_code]);
    }
    
    console.log('Inserted sample theme categories');
    
    // Insert sample service gaps
    const gaps = [
      {
        service_type: 'Youth Mental Health',
        location_name: 'Mount Isa',
        description: 'Limited specialized mental health services for young people, with wait times exceeding 3 months.',
        severity_score: 8,
        people_affected_estimate: 150,
        status: 'active'
      },
      {
        service_type: 'Accessible Transport',
        location_name: 'Mornington Island',
        description: 'Lack of wheelchair-accessible transport for medical appointments and daily activities.',
        severity_score: 7,
        people_affected_estimate: 75,
        status: 'active'
      },
      {
        service_type: 'Elder Care',
        location_name: 'Normanton',
        description: 'Limited in-home care options for elderly community members wishing to age in place.',
        severity_score: 6,
        people_affected_estimate: 42,
        status: 'active'
      }
    ];
    
    for (const gap of gaps) {
      // Get location ID
      const locationResult = await db.query('SELECT id FROM locations WHERE name = $1', [gap.location_name]);
      if (locationResult.rows.length === 0) continue;
      
      const locationId = locationResult.rows[0].id;
      
      const query = `
        INSERT INTO identified_gaps (
          service_type, location_id, description, severity_score, 
          people_affected_estimate, status
        )
        VALUES ($1, $2, $3, $4, $5, $6)
      `;
      await db.query(query, [
        gap.service_type, 
        locationId, 
        gap.description, 
        gap.severity_score, 
        gap.people_affected_estimate, 
        gap.status
      ]);
    }
    
    console.log('Inserted sample service gaps');
    
    // Insert sample action items
    const actions = [
      {
        title: 'Expand Telehealth Services',
        description: 'Implement telehealth options for mental health services to reduce wait times for young people.',
        service_type: 'Youth Mental Health',
        responsible_organization: 'Health Department',
        target_date: '2025-08-15',
        status: 'in_progress'
      },
      {
        title: 'Mobile Disability Transport Service',
        description: 'Develop a mobile transport service for people with disabilities across the region.',
        service_type: 'Accessible Transport',
        responsible_organization: 'Social Services',
        target_date: '2025-09-30',
        status: 'proposed'
      },
      {
        title: 'Community Feedback Portal',
        description: 'Launch online portal for community members to share feedback and suggestions.',
        service_type: 'Community Engagement',
        responsible_organization: 'Digital Team',
        target_date: '2025-07-10',
        status: 'completed'
      }
    ];
    
    for (const action of actions) {
      // Get gap ID if exists
      let gapId = null;
      if (action.service_type) {
        const gapResult = await db.query(
          'SELECT id FROM identified_gaps WHERE service_type = $1 LIMIT 1', 
          [action.service_type]
        );
        if (gapResult.rows.length > 0) {
          gapId = gapResult.rows[0].id;
        }
      }
      
      const query = `
        INSERT INTO action_items (
          title, description, gap_id, responsible_organization, 
          target_date, status
        )
        VALUES ($1, $2, $3, $4, $5, $6)
      `;
      await db.query(query, [
        action.title,
        action.description,
        gapId,
        action.responsible_organization,
        action.target_date,
        action.status
      ]);
    }
    
    console.log('Inserted sample action items');
    
    console.log('Engagement data initialization complete!');
    process.exit(0);
  } catch (err) {
    console.error('Error initializing engagement data:', err);
    process.exit(1);
  }
}

// Run the initialization
initEngagementData();
