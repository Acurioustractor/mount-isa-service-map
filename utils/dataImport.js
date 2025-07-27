// Utility functions for importing service data

const db = require('../config/db');

/**
 * Import services from JSON data
 * @param {Array} services - Array of service objects
 * @returns {Object} Import results
 */
async function importServices(services) {
  const results = {
    imported: 0,
    skipped: 0,
    errors: []
  };
  
  for (const service of services) {
    try {
      // Check if service already exists
      const existingQuery = `
        SELECT id FROM services 
        WHERE name = $1 AND address = $2 AND suburb = $3
      `;
      const existingResult = await db.query(existingQuery, [
        service.name,
        service.address,
        service.suburb
      ]);
      
      if (existingResult.rows.length > 0) {
        // Service already exists, skip
        results.skipped++;
        continue;
      }
      
      // Get category ID
      let categoryId = null;
      if (service.category) {
        const categoryQuery = `
          SELECT id FROM service_categories 
          WHERE name = $1
        `;
        const categoryResult = await db.query(categoryQuery, [service.category]);
        if (categoryResult.rows.length > 0) {
          categoryId = categoryResult.rows[0].id;
        }
      }
      
      // Insert service
      const insertQuery = `
        INSERT INTO services (
          name, description, category_id, address, suburb, state, postcode,
          latitude, longitude, phone, email, website,
          eligibility_criteria, service_hours, availability, cost, referral_required
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
        RETURNING id
      `;
      
      const insertParams = [
        service.name,
        service.description,
        categoryId,
        service.address,
        service.suburb,
        service.state || 'QLD',
        service.postcode,
        service.latitude,
        service.longitude,
        service.phone,
        service.email,
        service.website,
        service.eligibility_criteria,
        service.service_hours,
        service.availability,
        service.cost,
        service.referral_required || false
      ];
      
      await db.query(insertQuery, insertParams);
      results.imported++;
    } catch (err) {
      results.errors.push({
        service: service.name,
        error: err.message
      });
    }
  }
  
  return results;
}

/**
 * Import initial services from the overview document
 * @returns {Object} Import results
 */
async function importInitialServices() {
  // This would be populated with data from the overview document
  const services = [
    {
      name: "headspace Mount Isa",
      description: "Local youth mental health centre offering free counselling, drug and alcohol support, and physical and sexual health services for ages 12-25.",
      category: "Mental Health",
      address: "13 Simpson Street",
      suburb: "Mount Isa",
      state: "QLD",
      postcode: "4825",
      phone: "(07) 4743 3700",
      email: "info@headspacemountisa.com.au",
      website: "https://headspacemountisa.com.au",
      eligibility_criteria: "Ages 12-25",
      service_hours: "Monday-Friday 8:30am-5:00pm",
      availability: "Walk-in and appointment based",
      cost: "Free",
      referral_required: false
    },
    {
      name: "Police-Citizens Youth Club (PCYC) Mount Isa",
      description: "Cornerstone for youth engagement offering a wide range of programs that give young people purpose, skills, and positive role models.",
      category: "Youth Support",
      address: "10 Simpson Street",
      suburb: "Mount Isa",
      state: "QLD",
      postcode: "4825",
      phone: "(07) 4742 1644",
      email: "mountisa@pcycqld.org.au",
      website: "https://pcycqld.org.au/centres/mount-isa/",
      eligibility_criteria: "All youth",
      service_hours: "Monday-Friday 8:00am-9:00pm, Saturday-Sunday 9:00am-5:00pm",
      availability: "Open access",
      cost: "Membership fees apply",
      referral_required: false
    },
    {
      name: "Gidgee Healing",
      description: "Aboriginal Community Controlled Health Service delivering primary health care across North West and Lower Gulf communities.",
      category: "Health Services",
      address: "34 Miles Street",
      suburb: "Mount Isa",
      state: "QLD",
      postcode: "4825",
      phone: "(07) 4742 2200",
      email: "info@gidgee.org.au",
      website: "https://gidgee.org.au",
      eligibility_criteria: "Open to all, with focus on Aboriginal and Torres Strait Islander communities",
      service_hours: "Monday-Friday 8:00am-5:00pm",
      availability: "Appointment based",
      cost: "Bulk billing available",
      referral_required: false
    }
    // More services would be added here
  ];
  
  return await importServices(services);
}

module.exports = {
  importServices,
  importInitialServices
};
