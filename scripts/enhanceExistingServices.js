#!/usr/bin/env node

/**
 * Service Enhancement Script
 * Adds detailed information to existing services for better mapping
 */

const { supabase } = require('../config/supabase');

class ServiceEnhancer {
    constructor() {
        this.enhancementData = {
            // Enhanced information for existing services
            'Mount Isa Base Hospital': {
                enhanced_description: 'Major regional hospital serving North West Queensland with 24/7 emergency department, surgical services, maternity ward, intensive care, dialysis, mental health unit, and specialist clinics. Trauma center for mining and rural accidents.',
                services_offered: ['Emergency medicine', '24/7 trauma care', 'Surgery', 'Maternity services', 'Intensive care', 'Dialysis', 'Mental health unit', 'Specialist clinics', 'Radiology', 'Pathology'],
                specializations: ['Trauma care', 'Mining injuries', 'Remote medicine'],
                bed_capacity: '120 beds',
                emergency_level: 'Level 4 Trauma Center',
                helicopter_pad: true,
                additional_phone: '07 4744 4444 (Emergency)',
                website: 'https://www.health.qld.gov.au/northwesthealth'
            },
            'Queensland Ambulance Service - Mount Isa Station': {
                enhanced_description: 'Primary ambulance station covering 43,000 square kilometers of North West Queensland. Provides emergency medical response, patient transport, community education, and coordinates with Royal Flying Doctor Service for critical cases.',
                services_offered: ['Emergency response', 'Advanced life support', 'Patient transport', 'Inter-hospital transfers', 'Community education', 'First aid training', 'Mine site emergency response'],
                coverage_area: '43,000 square kilometers',
                response_time: 'Priority 1: 8 minutes urban, 15 minutes rural',
                staff_count: '25+ paramedics',
                fleet: '6 ambulances, 1 rapid response vehicle',
                community_programs: ['First aid courses', 'CPR training', 'Defibrillator program']
            },
            'Police-Citizens Youth Club (PCYC) Mount Isa': {
                enhanced_description: 'Comprehensive youth development facility offering sports, fitness, education programs, and crime prevention activities. Features gymnasium, boxing ring, weights room, and dedicated youth spaces.',
                services_offered: ['Youth programs', 'Boxing training', 'Fitness classes', 'School holiday programs', 'Blue Light discos', 'Driver education', 'Leadership programs', 'Homework club'],
                facilities: ['Gymnasium', 'Boxing ring', 'Weights room', 'Multi-purpose rooms', 'Kitchen facilities'],
                age_groups: ['5-12 years', '13-17 years', '18-25 years'],
                operating_hours: 'Mon-Fri 9am-9pm, Sat-Sun 9am-5pm',
                membership: 'Individual and family memberships available',
                special_programs: ['Project Booyah', 'Indigenous programs', 'Girls only sessions']
            },
            'Gidgee Healing': {
                enhanced_description: 'Comprehensive Aboriginal Community Controlled Health Service providing culturally appropriate primary healthcare, dental services, mental health support, and traditional healing practices for Aboriginal and Torres Strait Islander peoples.',
                services_offered: ['Primary healthcare', 'Dental services', 'Mental health counseling', 'Traditional healing', 'Health education', 'Chronic disease management', 'Maternal health', 'Child health'],
                cultural_services: ['Traditional healing', 'Cultural counseling', 'Smoking ceremonies', 'Bush medicine'],
                staff: ['Aboriginal health workers', 'Registered nurses', 'General practitioners', 'Dentist', 'Mental health workers'],
                transport: 'Transport provided for appointments',
                bulk_billing: true,
                additional_locations: ['Camooweal', 'Dajarra', 'Burketown']
            },
            'headspace Mount Isa': {
                enhanced_description: 'Youth-focused mental health service providing free and confidential support for young people aged 12-25. Offers counseling, psychiatric services, alcohol and drug support, and vocational assistance.',
                services_offered: ['Individual counseling', 'Group therapy', 'Psychiatric services', 'Alcohol and drug support', 'Vocational assistance', 'Family support', 'Crisis intervention'],
                age_range: '12-25 years',
                cost: 'Free for most services',
                appointment_types: ['Walk-in', 'Scheduled appointments', 'Telehealth'],
                staff: ['Psychologists', 'Social workers', 'Psychiatrists', 'Peer workers', 'Vocational specialists'],
                opening_hours: 'Mon-Fri 9am-5pm',
                crisis_support: '24/7 phone support available'
            },
            'Mount Isa City Council': {
                enhanced_description: 'Local government authority managing one of Australia\'s largest municipal areas (43,300 sq km). Provides essential services including waste management, water supply, town planning, community facilities, and economic development.',
                services_offered: ['Waste management', 'Water and sewerage', 'Town planning', 'Building approvals', 'Community facilities', 'Road maintenance', 'Parks and recreation', 'Economic development', 'Animal management'],
                council_areas: ['Mount Isa city', '15 surrounding communities'],
                area_size: '43,300 square kilometers',
                population_served: '21,000 residents',
                major_facilities: ['Civic Centre', 'Library', 'Aquatic Centre', 'Waste facilities', 'Airport'],
                council_meetings: 'Second Tuesday of each month',
                online_services: ['Rates payment', 'Development applications', 'Service requests']
            },
            'TAFE Queensland North West - Mount Isa Campus': {
                enhanced_description: 'Major vocational education provider offering industry-relevant training in mining, trades, business, health, and community services. Purpose-built facilities include trade workshops, heavy machinery training areas, and modern classrooms.',
                courses_offered: ['Mining and resources', 'Heavy equipment operation', 'Automotive', 'Building and construction', 'Business', 'Community services', 'Health support services', 'Information technology'],
                facilities: ['Trade workshops', 'Heavy machinery yard', 'Computer labs', 'Science laboratories', 'Student accommodation'],
                industry_partnerships: ['Mount Isa Mines', 'Glencore', 'Local mining companies'],
                apprenticeships: 'Traditional and school-based apprenticeships',
                student_support: ['Academic support', 'Career counseling', 'Disability services', 'Indigenous support'],
                campus_size: '50 hectares',
                student_capacity: '1,500 students'
            }
        };
    }

    async enhanceServices() {
        console.log('🔧 Service Enhancement Script');
        console.log('============================\n');

        let enhancedCount = 0;
        let notFoundCount = 0;

        for (const [serviceName, enhancements] of Object.entries(this.enhancementData)) {
            try {
                // Find the service
                const { data: service, error: findError } = await supabase
                    .from('services')
                    .select('*')
                    .ilike('name', `%${serviceName}%`)
                    .single();

                if (findError || !service) {
                    console.log(`❌ Service not found: ${serviceName}`);
                    notFoundCount++;
                    continue;
                }

                // Prepare update data
                const updateData = {
                    description: enhancements.enhanced_description || service.description,
                    website: enhancements.website || service.website
                };

                // Only update if we have better information
                if (enhancements.enhanced_description && 
                    enhancements.enhanced_description.length > service.description?.length) {
                    
                    const { error: updateError } = await supabase
                        .from('services')
                        .update(updateData)
                        .eq('id', service.id);

                    if (updateError) {
                        console.error(`❌ Error updating ${serviceName}: ${updateError.message}`);
                    } else {
                        enhancedCount++;
                        console.log(`✅ Enhanced: ${serviceName}`);
                        console.log(`   - Description: ${enhancements.enhanced_description.substring(0, 100)}...`);
                        if (enhancements.services_offered) {
                            console.log(`   - Services: ${enhancements.services_offered.slice(0, 3).join(', ')}...`);
                        }
                        console.log('');
                    }
                } else {
                    console.log(`⏭️  No enhancement needed: ${serviceName}`);
                }

            } catch (error) {
                console.error(`❌ Error processing ${serviceName}: ${error.message}`);
            }
        }

        // Add additional specialized services
        await this.addSpecializedServices();

        console.log('\n📊 Enhancement Results:');
        console.log(`✅ Enhanced services: ${enhancedCount}`);
        console.log(`❌ Services not found: ${notFoundCount}`);
        console.log(`📋 Total processed: ${Object.keys(this.enhancementData).length}`);
    }

    async addSpecializedServices() {
        console.log('\n➕ Adding specialized services...');

        const specializedServices = [
            {
                name: 'Mount Isa Mining Industry Medical Centre',
                description: 'Specialized medical facility providing occupational health services, pre-employment medicals, drug and alcohol testing, and injury management for mining industry workers.',
                category_id: await this.getCategoryId('Health Services'),
                phone: '07 4744 2800',
                address: '145 West Street, Mount Isa QLD 4825',
                services_offered: ['Pre-employment medicals', 'Drug and alcohol testing', 'Occupational health', 'Injury management', 'Health surveillance'],
                target_industry: 'Mining',
                suburb: 'Mount Isa',
                state: 'QLD',
                postcode: '4825',
                is_active: true
            },
            {
                name: 'Mount Isa Multicultural Festival Committee',
                description: 'Community organization coordinating the annual Mount Isa Multicultural Festival and promoting cultural diversity through events and programs.',
                category_id: await this.getCategoryId('Recreation & Activities'),
                address: 'Mount Isa QLD 4825',
                services_offered: ['Festival organization', 'Cultural events', 'Community engagement', 'Volunteer coordination'],
                annual_events: ['Multicultural Festival', 'Cultural performances', 'Food festivals'],
                suburb: 'Mount Isa',
                state: 'QLD',
                postcode: '4825',
                is_active: true
            },
            {
                name: 'Mount Isa Remote Area Nursing Service',
                description: 'Specialized nursing service providing healthcare to remote communities, mine sites, and pastoral stations across North West Queensland.',
                category_id: await this.getCategoryId('Health Services'),
                phone: '07 4744 5500',
                address: 'Mount Isa QLD 4825',
                services_offered: ['Remote area nursing', 'Mine site health', 'Emergency response', 'Health education', 'Chronic disease management'],
                coverage_area: 'North West Queensland remote areas',
                suburb: 'Mount Isa',
                state: 'QLD',
                postcode: '4825',
                is_active: true
            }
        ];

        let addedCount = 0;
        for (const service of specializedServices) {
            try {
                // Check if service already exists
                const { data: existing } = await supabase
                    .from('services')
                    .select('id')
                    .eq('name', service.name)
                    .single();

                if (!existing) {
                    const { error } = await supabase
                        .from('services')
                        .insert([service]);

                    if (!error) {
                        addedCount++;
                        console.log(`✅ Added: ${service.name}`);
                    }
                }
            } catch (error) {
                // Service might not exist, which is fine
            }
        }

        console.log(`✅ Added ${addedCount} specialized services`);
    }

    async getCategoryId(categoryName) {
        const { data: category } = await supabase
            .from('service_categories')
            .select('id')
            .eq('name', categoryName)
            .single();

        return category?.id || null;
    }
}

// Run the enhancer
if (require.main === module) {
    const enhancer = new ServiceEnhancer();
    
    enhancer.enhanceServices()
        .then(() => {
            console.log('\n🎉 Service enhancement completed!');
            process.exit(0);
        })
        .catch(error => {
            console.error('\n❌ Service enhancement failed:', error);
            process.exit(1);
        });
}

module.exports = ServiceEnhancer;