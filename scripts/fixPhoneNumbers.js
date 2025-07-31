#!/usr/bin/env node

const { supabase } = require('../config/supabase');

async function fixPhoneNumbers() {
    const servicesToFix = [
        {
            name: 'Mount Isa Fire and Rescue Station',
            description: 'Queensland Fire and Emergency Services - unified facility for Fire and Rescue Service. Emergency response and fire safety education.',
            category: 'Emergency Services',
            phone: '000 or 07 4744 1544', // Shortened version
            address: 'Helen Street, Mount Isa QLD 4825',
            website: 'https://www.qfes.qld.gov.au/'
        },
        {
            name: 'Mount Isa State Emergency Service (SES)',
            description: 'Queensland SES volunteers providing emergency assistance during floods, storms and disasters. Co-located with Fire and Rescue.',
            category: 'Emergency Services',
            phone: '132 500', // Just SES emergency number
            address: 'Helen Street, Mount Isa QLD 4825',
            website: 'https://www.ses.qld.gov.au/'
        }
    ];

    // Get category IDs
    const { data: categories } = await supabase
        .from('service_categories')
        .select('*');
    
    const categoryMap = {};
    categories.forEach(cat => {
        categoryMap[cat.name] = cat.id;
    });

    for (const service of servicesToFix) {
        const { error } = await supabase
            .from('services')
            .insert([{
                name: service.name,
                description: service.description,
                category_id: categoryMap[service.category],
                phone: service.phone,
                address: service.address,
                website: service.website,
                suburb: 'Mount Isa',
                state: 'QLD',
                postcode: '4825',
                is_active: true
            }]);

        if (error) {
            console.error(`❌ Error: ${error.message}`);
        } else {
            console.log(`✅ Fixed: ${service.name}`);
        }
    }
}

fixPhoneNumbers().catch(console.error);