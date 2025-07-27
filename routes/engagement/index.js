const express = require('express');
const db = require('../../config/db');
const {
  getLocationIdByName,
  getThemeCategoryIdByName,
  getGapIdByServiceType,
  formatDateForDisplay,
  calculatePriorityLevel,
  getStatusBadgeClass
} = require('../../utils/engagementHelpers');

const router = express.Router();

// Get all interviews with optional filtering
router.get('/interviews', async (req, res) => {
  try {
    const { location, dateFrom, dateTo, validated } = req.query;
    
    let query = `
      SELECT 
        ci.id,
        ci.interview_date,
        ci.duration_seconds,
        ci.recording_type,
        ci.language,
        ci.validation_status,
        l.name as location_name,
        au.first_name as interviewer_first_name,
        au.last_name as interviewer_last_name
      FROM community_interviews ci
      LEFT JOIN locations l ON ci.location_id = l.id
      LEFT JOIN admin_users au ON ci.interviewer_id = au.id
      WHERE 1=1
    `;
    
    const params = [];
    
    if (location) {
      params.push(location);
      query += ` AND l.name = $${params.length}`;
    }
    
    if (dateFrom) {
      params.push(dateFrom);
      query += ` AND ci.interview_date >= $${params.length}`;
    }
    
    if (dateTo) {
      params.push(dateTo);
      query += ` AND ci.interview_date <= $${params.length}`;
    }
    
    if (validated !== undefined) {
      if (validated === 'true') {
        query += ` AND ci.validation_status = 'validated'`;
      } else if (validated === 'false') {
        query += ` AND ci.validation_status != 'validated'`;
      }
    }
    
    query += ' ORDER BY ci.interview_date DESC';
    
    const result = await db.query(query, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch interviews' });
  }
});

// Get interview by ID with full details
router.get('/interviews/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const query = `
      SELECT 
        ci.*,
        l.name as location_name,
        au.first_name as interviewer_first_name,
        au.last_name as interviewer_last_name
      FROM community_interviews ci
      LEFT JOIN locations l ON ci.location_id = l.id
      LEFT JOIN admin_users au ON ci.interviewer_id = au.id
      WHERE ci.id = $1
    `;
    
    const result = await db.query(query, [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Interview not found' });
    }
    
    // Get participants
    const participantsQuery = `
      SELECT * FROM interview_participants WHERE interview_id = $1
    `;
    const participantsResult = await db.query(participantsQuery, [id]);
    
    // Get themes
    const themesQuery = `
      SELECT 
        it.*,
        tc.name as theme_category_name
      FROM interview_themes it
      LEFT JOIN theme_categories tc ON it.theme_category_id = tc.id
      WHERE it.interview_id = $1
    `;
    const themesResult = await db.query(themesQuery, [id]);
    
    const interview = {
      ...result.rows[0],
      participants: participantsResult.rows,
      themes: themesResult.rows
    };
    
    res.json(interview);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch interview' });
  }
});

// Create a new interview
router.post('/interviews', async (req, res) => {
  try {
    const {
      location_id,
      interviewer_id,
      interview_date,
      duration_seconds,
      recording_url,
      recording_type,
      transcript,
      ai_summary,
      language,
      participant_count,
      consent_obtained
    } = req.body;
    
    const query = `
      INSERT INTO community_interviews (
        location_id, interviewer_id, interview_date, duration_seconds,
        recording_url, recording_type, transcript, ai_summary, language,
        participant_count, consent_obtained
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      RETURNING id, interview_date
    `;
    
    const params = [
      location_id, interviewer_id, interview_date, duration_seconds,
      recording_url, recording_type, transcript, ai_summary, language,
      participant_count, consent_obtained
    ];
    
    const result = await db.query(query, params);
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to create interview' });
  }
});

// Update an interview
router.put('/interviews/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const {
      location_id,
      interview_date,
      duration_seconds,
      recording_url,
      recording_type,
      transcript,
      ai_summary,
      language,
      participant_count,
      consent_obtained,
      validation_status
    } = req.body;
    
    const query = `
      UPDATE community_interviews SET
        location_id = $1,
        interview_date = $2,
        duration_seconds = $3,
        recording_url = $4,
        recording_type = $5,
        transcript = $6,
        ai_summary = $7,
        language = $8,
        participant_count = $9,
        consent_obtained = $10,
        validation_status = $11,
        updated_at = CURRENT_TIMESTAMP
      WHERE id = $12
      RETURNING id, interview_date
    `;
    
    const params = [
      location_id, interview_date, duration_seconds,
      recording_url, recording_type, transcript, ai_summary, language,
      participant_count, consent_obtained, validation_status, id
    ];
    
    const result = await db.query(query, params);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Interview not found' });
    }
    
    res.json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to update interview' });
  }
});

// Get all theme categories
router.get('/themes/categories', async (req, res) => {
  try {
    const query = 'SELECT * FROM theme_categories ORDER BY name';
    const result = await db.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch theme categories' });
  }
});

// Get identified service gaps
router.get('/gaps', async (req, res) => {
  try {
    const { location, status, serviceType } = req.query;
    
    let query = `
      SELECT 
        ig.*,
        l.name as location_name
      FROM identified_gaps ig
      LEFT JOIN locations l ON ig.location_id = l.id
      WHERE 1=1
    `;
    
    const params = [];
    
    if (location) {
      params.push(location);
      query += ` AND l.name = $${params.length}`;
    }
    
    if (status) {
      params.push(status);
      query += ` AND ig.status = $${params.length}`;
    }
    
    if (serviceType) {
      params.push(serviceType);
      query += ` AND ig.service_type = $${params.length}`;
    }
    
    query += ' ORDER BY ig.severity_score DESC, ig.last_mentioned DESC';
    
    const result = await db.query(query, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch service gaps' });
  }
});

// Get action items
router.get('/actions', async (req, res) => {
  try {
    const { status, dueDateFrom, dueDateTo } = req.query;
    
    let query = `
      SELECT 
        ai.*,
        ig.description as gap_description
      FROM action_items ai
      LEFT JOIN identified_gaps ig ON ai.gap_id = ig.id
      WHERE 1=1
    `;
    
    const params = [];
    
    if (status) {
      params.push(status);
      query += ` AND ai.status = $${params.length}`;
    }
    
    if (dueDateFrom) {
      params.push(dueDateFrom);
      query += ` AND ai.target_date >= $${params.length}`;
    }
    
    if (dueDateTo) {
      params.push(dueDateTo);
      query += ` AND ai.target_date <= $${params.length}`;
    }
    
    query += ' ORDER BY ai.target_date ASC';
    
    const result = await db.query(query, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch action items' });
  }
});

module.exports = router;
