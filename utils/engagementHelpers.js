/**
 * Utility functions for community engagement features
 */

const db = require('../config/db');

/**
 * Get location ID by name
 * @param {string} locationName - Name of the location
 * @returns {Promise<string|null>} Location ID or null if not found
 */
async function getLocationIdByName(locationName) {
  try {
    const result = await db.query(
      'SELECT id FROM locations WHERE name = $1',
      [locationName]
    );
    
    return result.rows.length > 0 ? result.rows[0].id : null;
  } catch (error) {
    console.error('Error getting location ID:', error);
    return null;
  }
}

/**
 * Get theme category ID by name
 * @param {string} categoryName - Name of the theme category
 * @returns {Promise<string|null>} Theme category ID or null if not found
 */
async function getThemeCategoryIdByName(categoryName) {
  try {
    const result = await db.query(
      'SELECT id FROM theme_categories WHERE name = $1',
      [categoryName]
    );
    
    return result.rows.length > 0 ? result.rows[0].id : null;
  } catch (error) {
    console.error('Error getting theme category ID:', error);
    return null;
  }
}

/**
 * Get service gap ID by service type
 * @param {string} serviceType - Type of service
 * @returns {Promise<string|null>} Service gap ID or null if not found
 */
async function getGapIdByServiceType(serviceType) {
  try {
    const result = await db.query(
      'SELECT id FROM identified_gaps WHERE service_type = $1 LIMIT 1',
      [serviceType]
    );
    
    return result.rows.length > 0 ? result.rows[0].id : null;
  } catch (error) {
    console.error('Error getting gap ID:', error);
    return null;
  }
}

/**
 * Format date for display
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDateForDisplay(date) {
  if (!date) return '';
  
  const d = new Date(date);
  return d.toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
}

/**
 * Calculate priority level based on severity score
 * @param {number} score - Severity score (1-10)
 * @returns {string} Priority level (low|medium|high)
 */
function calculatePriorityLevel(score) {
  if (score >= 8) return 'high';
  if (score >= 5) return 'medium';
  return 'low';
}

/**
 * Calculate status badge class
 * @param {string} status - Status value
 * @returns {string} Bootstrap badge class
 */
function getStatusBadgeClass(status) {
  const statusClasses = {
    'proposed': 'bg-secondary',
    'in_progress': 'bg-warning',
    'completed': 'bg-success',
    'delayed': 'bg-danger',
    'active': 'bg-primary',
    'addressed': 'bg-info'
  };
  
  return statusClasses[status] || 'bg-secondary';
}

module.exports = {
  getLocationIdByName,
  getThemeCategoryIdByName,
  getGapIdByServiceType,
  formatDateForDisplay,
  calculatePriorityLevel,
  getStatusBadgeClass
};
