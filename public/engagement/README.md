# Community Engagement Features

This directory contains the frontend components for the community engagement features of the Mount Isa Service Map. These features support the collection, analysis, and coordination of community feedback to improve service delivery in remote communities.

## Features

### 1. Interview Recorder
- **File**: `recorder.html`
- **Purpose**: Record community interviews with audio capture
- **Key Features**:
  - One-button recording interface
  - Participant management
  - Session metadata capture
  - Offline-first design

### 2. Engagement Dashboard
- **File**: `dashboard.html`
- **Purpose**: Overview of all community engagement activities
- **Key Features**:
  - Statistics summary
  - Recent interviews display
  - Service gaps visualization
  - Action items tracking

### 3. Interview Details
- **File**: `interview.html`
- **Purpose**: Detailed view of individual interviews
- **Key Features**:
  - Audio playback controls
  - Interactive transcript viewer
  - AI-generated theme analysis
  - Related service gaps display

### 4. Service Gaps Analysis
- **File**: `gaps.html`
- **Purpose**: Identify and prioritize service delivery gaps
- **Key Features**:
  - Geographic gap mapping
  - Priority-based filtering
  - Severity scoring
  - Supporting evidence linking

### 5. Action Items Tracking
- **File**: `actions.html`
- **Purpose**: Track responses to identified service gaps
- **Key Features**:
  - Status tracking (proposed, in-progress, completed)
  - Responsible organization assignment
  - Due date management
  - Progress monitoring

## Navigation

All engagement pages include a consistent navigation menu at the top for easy movement between features.

## Data Flow

1. **Record** interviews with community members using the recorder
2. **Analyze** interviews to identify key themes and service gaps
3. **Prioritize** gaps based on severity and community impact
4. **Assign** action items to address identified gaps
5. **Track** progress on action items to completion

## Technical Implementation

The frontend components are built with:
- Bootstrap 5 for responsive design
- Vanilla JavaScript for interactivity
- Chart.js for data visualization
- Bootstrap Icons for UI elements

The components communicate with the backend API endpoints defined in `routes/engagement/index.js`.

## Getting Started

1. Ensure the backend server is running (`npm start`)
2. Open `dashboard.html` in a web browser
3. Navigate between features using the top navigation menu

## Future Enhancements

Planned improvements include:
- Integration with speech-to-text APIs for automatic transcription
- Machine learning for improved theme extraction
- Real-time collaboration features
- Mobile-optimized interfaces for field use
- Offline data synchronization
