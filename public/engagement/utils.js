/**
 * Frontend utility functions for community engagement features
 */

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
 * Format time for display
 * @param {number} seconds - Time in seconds
 * @returns {string} Formatted time string (HH:MM:SS)
 */
function formatTime(seconds) {
  if (!seconds) return '00:00:00';
  
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  
  return [h, m, s]
    .map(v => v < 10 ? '0' + v : v)
    .join(':');
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
 * Get priority badge class
 * @param {string} level - Priority level
 * @returns {string} Bootstrap badge class
 */
function getPriorityBadgeClass(level) {
  const classes = {
    'high': 'bg-danger',
    'medium': 'bg-warning',
    'low': 'bg-success'
  };
  
  return classes[level] || 'bg-secondary';
}

/**
 * Get status badge class
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
    'addressed': 'bg-info',
    'validated': 'bg-success'
  };
  
  return statusClasses[status] || 'bg-secondary';
}

/**
 * Format percentage
 * @param {number} value - Percentage value (0-100)
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value) {
  if (value === undefined || value === null) return '0%';
  return Math.round(value) + '%';
}

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Generate a simple UUID
 * @returns {string} UUID string
 */
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Export functions
window.EngagementUtils = {
  formatDateForDisplay,
  formatTime,
  calculatePriorityLevel,
  getPriorityBadgeClass,
  getStatusBadgeClass,
  formatPercentage,
  truncateText,
  generateUUID
};
