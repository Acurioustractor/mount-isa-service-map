#!/usr/bin/env node

// Script to intelligently re-categorize services based on their names and descriptions

const { supabase } = require('../config/supabase');

const categoryRules = [
    {
        category: 'Health Services',
        keywords: [
            'health', 'medical', 'ambulance', 'hospital', 'clinic'
        ]
    },
    {
        category: 'Mental Health',
        keywords: [
            'mental health', 'counselling', 'therapy', 'psychological', 'psychiatr',
            'anxiety', 'depression', 'stress', 'trauma', 'grief', 'wellbeing'
        ]
    },
    {
        category: 'Youth Support',
        keywords: [
            'youth', 'young people', 'children', 'child', 'kid', 'teen', 'adolescent',
            'student', 'school'
        ]
    },
    {
        category: 'Disability Support',
        keywords: [
            'disability', 'NDIS', 'accessible', 'special needs', 'support worker',
            'seniors', 'aged care'
        ]
    },
    {
        category: 'Housing & Accommodation',
        keywords: [
            'housing', 'accommodation', 'rental', 'tenancy', 'homeless', 'shelter',
            'rent', 'property', 'residence', 'homes'
        ]
    },
    {
        category: 'Education & Training',
        keywords: [
            'education', 'training', 'TAFE', 'university', 'college', 'apprentice',
            'skills', 'learning', 'study'
        ]
    },
    {
        category: 'Justice & Legal',
        keywords: [
            'justice', 'legal', 'court', 'child safety', 'child protection',
            'family support', 'women', 'domestic violence'
        ]
    },
    {
        category: 'Emergency Services',
        keywords: [
            'emergency', 'police', 'fire', 'ambulance', 'rescue', 'safety',
            'crime prevention', 'security'
        ]
    },
    {
        category: 'Recreation & Activities',
        keywords: [
            'recreation', 'sport', 'activities', 'community centre', 'library',
            'cultural', 'arts', 'events'
        ]
    }
];

function categorizeService(service) {
    if (!service) return { category: 'Community Support', matches: 0, keywords: [] };
    
    const text = `${service.name || ''} ${service.description || ''}`.toLowerCase();
    
    // Check each category rule for keyword matches
    for (const rule of categoryRules) {
        if (!rule || !rule.category || !rule.keywords) continue;
        
        const matches = rule.keywords.filter(keyword => text.includes(keyword.toLowerCase()));
        if (matches.length > 0) {
            return { category: rule.category, matches: matches.length, keywords: matches };
        }
    }
    
    // Default to Community Support if no specific match
    return { category: 'Community Support', matches: 0, keywords: [] };
}

async function recategorizeServices() {
    try {
        console.log('🏷️  Starting intelligent service re-categorization...');
        
        // Get all services from Supabase
        const { data: services, error: fetchError } = await supabase
            .from('services')
            .select('id, name, description, category_id')
            .eq('is_active', true);
            
        if (fetchError) {
            throw new Error('Failed to fetch services: ' + fetchError.message);
        }
        
        console.log(`📋 Found ${services.length} services to categorize`);
        
        // Get all categories for mapping
        const { data: categories, error: catError } = await supabase
            .from('service_categories')
            .select('*');
            
        if (catError) {
            throw new Error('Failed to fetch categories: ' + catError.message);
        }
        
        // Create category name to ID mapping
        const categoryMap = {};
        categories.forEach(cat => {
            categoryMap[cat.name] = cat.id;
        });
        
        console.log(`📂 Available categories:`, Object.keys(categoryMap));
        
        // Debug: let's see what categories we found
        categories.forEach(cat => {
            console.log(`  - ${cat.name} (ID: ${cat.id})`);
        });
        
        // Categorize each service
        const updates = [];
        const categoryCounts = {};
        
        for (const service of services) {
            const result = categorizeService(service);
            if (!result.category) {
                console.error(`❌ No category returned for service:`, service);
                continue;
            }
            
            // Create category if it doesn't exist
            if (!categoryMap[result.category]) {
                console.log(`➕ Creating new category: ${result.category}`);
                const { data: newCategory, error: createError } = await supabase
                    .from('service_categories')
                    .insert([{
                        name: result.category,
                        description: `Services related to ${result.category.toLowerCase()}`,
                        is_active: true
                    }])
                    .select()
                    .single();
                    
                if (createError) {
                    console.error(`❌ Failed to create category ${result.category}:`, createError.message);
                } else if (newCategory) {
                    categoryMap[result.category] = newCategory.id;
                    console.log(`✅ Created category: ${result.category} (ID: ${newCategory.id})`);
                }
            }
            
            updates.push({
                id: service.id,
                category_id: categoryMap[result.category],
                categorization_info: {
                    category: result.category,
                    confidence: result.matches,
                    keywords: result.keywords
                }
            });
            
            // Track category counts
            categoryCounts[result.category] = (categoryCounts[result.category] || 0) + 1;
            
            if (result.matches > 0) {
                console.log(`✅ ${service.name} → ${result.category} (${result.matches} matches: ${result.keywords.join(', ')})`);
            } else {
                console.log(`📝 ${service.name} → ${result.category} (default)`);
            }
        }
        
        // Update services in batches
        console.log('\n📤 Updating service categories in Supabase...');
        const batchSize = 10;
        let updatedCount = 0;
        
        for (let i = 0; i < updates.length; i += batchSize) {
            const batch = updates.slice(i, i + batchSize);
            
            // Process each update individually to avoid conflicts
            let batchSuccessCount = 0;
            for (const update of batch) {
                const { error: individualError } = await supabase
                    .from('services')
                    .update({ category_id: update.category_id })
                    .eq('id', update.id);
                
                if (individualError) {
                    console.warn(`Failed to update service ${update.id}:`, individualError.message);
                } else {
                    batchSuccessCount++;
                }
            }
            
            const error = null; // Reset error since we handled individually
                
            updatedCount += batchSuccessCount;
            console.log(`✅ Updated batch ${Math.floor(i/batchSize) + 1}: ${batchSuccessCount}/${batch.length} services`);
        }
        
        // Display categorization summary
        console.log('\n📊 Categorization Summary:');
        Object.entries(categoryCounts)
            .sort(([,a], [,b]) => b - a)
            .forEach(([category, count]) => {
                console.log(`  • ${category}: ${count} services`);
            });
        
        console.log(`\n🎉 Successfully re-categorized ${updatedCount} services!`);
        console.log('🌐 Check the updated filters at: https://mount-isa-service-map.vercel.app');
        
    } catch (error) {
        console.error('❌ Error during re-categorization:', error);
        process.exit(1);
    }
}

// Run if script is called directly
if (require.main === module) {
    recategorizeServices();
}

module.exports = { recategorizeServices };