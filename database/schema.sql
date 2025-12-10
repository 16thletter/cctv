-- PostgreSQL Schema for CCTV Face Recognition System
-- Multi-Camera Support with Face Recognition

-- Enable pgvector extension for face embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- ORGANIZATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50) UNIQUE,
    address TEXT,
    contact_person VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CAMERAS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
    location VARCHAR(255),
    description TEXT,
    rtsp_url_env VARCHAR(100),  -- Environment variable name for RTSP URL (e.g., 'CAMERA_MAIN_URL')
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PERSONS TABLE (Known People)
-- ============================================================================
CREATE TABLE IF NOT EXISTS persons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    employee_id VARCHAR(100) UNIQUE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
    department VARCHAR(100),
    designation VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    photo_path VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- EMPLOYEE ATTENDANCE SUMMARY TABLE (Daily IN/OUT counts per employee)
-- ============================================================================
CREATE TABLE IF NOT EXISTS employee_attendance (
    id SERIAL PRIMARY KEY,
    person_id INTEGER REFERENCES persons(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    total_in INTEGER DEFAULT 0,
    total_out INTEGER DEFAULT 0,
    first_in_time TIMESTAMP,
    last_out_time TIMESTAMP,
    total_duration_seconds INTEGER DEFAULT 0,  -- Total time spent inside
    is_present BOOLEAN DEFAULT false,  -- Currently inside or not
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_person_date UNIQUE (person_id, date)
);

-- ============================================================================
-- ORGANIZATION ATTENDANCE SUMMARY TABLE (Daily stats per organization)
-- ============================================================================
CREATE TABLE IF NOT EXISTS organization_attendance (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_employees INTEGER DEFAULT 0,  -- Total employees in organization
    present_count INTEGER DEFAULT 0,  -- Currently present
    total_in_count INTEGER DEFAULT 0,  -- Total IN events
    total_out_count INTEGER DEFAULT 0,  -- Total OUT events
    peak_occupancy INTEGER DEFAULT 0,  -- Maximum simultaneous presence
    peak_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_org_date UNIQUE (organization_id, date)
);

-- ============================================================================
-- FACE EMBEDDINGS TABLE (ArcFace 512-dimensional vectors)
-- ============================================================================
CREATE TABLE IF NOT EXISTS face_embeddings (
    id SERIAL PRIMARY KEY,
    person_id INTEGER REFERENCES persons(id) ON DELETE CASCADE,
    embedding VECTOR(512) NOT NULL,  -- ArcFace produces 512-dim embeddings
    quality_score FLOAT,  -- Face quality score (0-1)
    source_image_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_person_embedding UNIQUE (person_id)
);

-- ============================================================================
-- FACE DETECTIONS TABLE (All face detections from cameras)
-- ============================================================================
CREATE TABLE IF NOT EXISTS face_detections (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id),
    person_id INTEGER REFERENCES persons(id),  -- NULL if unknown person
    track_id INTEGER,
    confidence FLOAT NOT NULL,  -- Face recognition confidence
    detection_score FLOAT,  -- Face detection score
    bbox_x1 INTEGER,
    bbox_y1 INTEGER,
    bbox_x2 INTEGER,
    bbox_y2 INTEGER,
    frame_number INTEGER,
    snapshot_path VARCHAR(500),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ENTRY/EXIT LOGS TABLE (Counting events with face recognition)
-- ============================================================================
CREATE TABLE IF NOT EXISTS entry_exit_logs (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id),
    person_id INTEGER REFERENCES persons(id),  -- NULL if unknown person
    track_id INTEGER,
    event_type VARCHAR(10) NOT NULL,  -- 'IN' or 'OUT'
    confidence FLOAT,  -- Face recognition confidence
    position_x INTEGER,
    position_y INTEGER,
    snapshot_path VARCHAR(500),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PERSON JOURNEY TABLE (Cross-camera tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS person_journey (
    id SERIAL PRIMARY KEY,
    person_id INTEGER REFERENCES persons(id),
    from_camera_id INTEGER REFERENCES cameras(id),
    to_camera_id INTEGER REFERENCES cameras(id),
    from_timestamp TIMESTAMP,
    to_timestamp TIMESTAMP,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- COUNTING EVENTS TABLE (Legacy compatibility + detailed tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS counting_events (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER REFERENCES cameras(id),
    track_id INTEGER,
    event_type VARCHAR(10) NOT NULL,  -- 'IN' or 'OUT'
    position_x INTEGER,
    position_y INTEGER,
    count_in INTEGER,
    count_out INTEGER,
    occupancy INTEGER,
    frame_number INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Organizations indexes
CREATE INDEX IF NOT EXISTS idx_organizations_code ON organizations(code);
CREATE INDEX IF NOT EXISTS idx_organizations_active ON organizations(is_active);

-- Persons indexes
CREATE INDEX IF NOT EXISTS idx_persons_organization ON persons(organization_id);
CREATE INDEX IF NOT EXISTS idx_persons_employee_id ON persons(employee_id);
CREATE INDEX IF NOT EXISTS idx_persons_active ON persons(is_active);

-- Employee attendance indexes
CREATE INDEX IF NOT EXISTS idx_employee_attendance_person ON employee_attendance(person_id, date);
CREATE INDEX IF NOT EXISTS idx_employee_attendance_org ON employee_attendance(organization_id, date);
CREATE INDEX IF NOT EXISTS idx_employee_attendance_date ON employee_attendance(date);
CREATE INDEX IF NOT EXISTS idx_employee_attendance_present ON employee_attendance(is_present);

-- Organization attendance indexes
CREATE INDEX IF NOT EXISTS idx_org_attendance_org ON organization_attendance(organization_id, date);
CREATE INDEX IF NOT EXISTS idx_org_attendance_date ON organization_attendance(date);

-- Face detections indexes
CREATE INDEX IF NOT EXISTS idx_face_detections_camera ON face_detections(camera_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_face_detections_person ON face_detections(person_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_face_detections_timestamp ON face_detections(timestamp);

-- Entry/Exit logs indexes
CREATE INDEX IF NOT EXISTS idx_entry_exit_camera ON entry_exit_logs(camera_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_entry_exit_person ON entry_exit_logs(person_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_entry_exit_timestamp ON entry_exit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_entry_exit_type ON entry_exit_logs(event_type, timestamp);

-- Person journey indexes
CREATE INDEX IF NOT EXISTS idx_person_journey_person ON person_journey(person_id, from_timestamp);
CREATE INDEX IF NOT EXISTS idx_person_journey_cameras ON person_journey(from_camera_id, to_camera_id);

-- Camera indexes
CREATE INDEX IF NOT EXISTS idx_cameras_camera_id ON cameras(camera_id);
CREATE INDEX IF NOT EXISTS idx_cameras_organization ON cameras(organization_id);
CREATE INDEX IF NOT EXISTS idx_cameras_active ON cameras(is_active);

-- Counting events indexes
CREATE INDEX IF NOT EXISTS idx_counting_events_camera ON counting_events(camera_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_counting_events_timestamp ON counting_events(timestamp);

-- Vector similarity index for fast face matching (IVFFlat)
CREATE INDEX IF NOT EXISTS idx_face_embeddings_vector
ON face_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_cameras_updated_at BEFORE UPDATE ON cameras
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_persons_updated_at BEFORE UPDATE ON persons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employee_attendance_updated_at BEFORE UPDATE ON employee_attendance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_org_attendance_updated_at BEFORE UPDATE ON organization_attendance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

