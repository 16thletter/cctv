-- ============================================================================
-- MIGRATION: Add Camera-Specific Counting Line Settings
-- ============================================================================
-- This migration adds columns to store camera-specific counting line settings
-- Each camera can have its own custom counting lines, or use defaults from config
-- ============================================================================

-- Add counting line configuration columns to cameras table
ALTER TABLE cameras 
ADD COLUMN IF NOT EXISTS outside_line_x1 FLOAT,
ADD COLUMN IF NOT EXISTS outside_line_y1 FLOAT,
ADD COLUMN IF NOT EXISTS outside_line_x2 FLOAT,
ADD COLUMN IF NOT EXISTS outside_line_y2 FLOAT,
ADD COLUMN IF NOT EXISTS inside_line_x1 FLOAT,
ADD COLUMN IF NOT EXISTS inside_line_y1 FLOAT,
ADD COLUMN IF NOT EXISTS inside_line_x2 FLOAT,
ADD COLUMN IF NOT EXISTS inside_line_y2 FLOAT,
ADD COLUMN IF NOT EXISTS in_direction VARCHAR(10) DEFAULT 'down',
ADD COLUMN IF NOT EXISTS line_color_r INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS line_color_g INTEGER DEFAULT 255,
ADD COLUMN IF NOT EXISTS line_color_b INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS line_thickness INTEGER DEFAULT 3,
ADD COLUMN IF NOT EXISTS cooldown_frames INTEGER DEFAULT 75,
ADD COLUMN IF NOT EXISTS min_track_length INTEGER DEFAULT 5;

-- Add comments to explain the columns
COMMENT ON COLUMN cameras.outside_line_x1 IS 'Outside line start X (normalized 0.0-1.0, NULL = use default)';
COMMENT ON COLUMN cameras.outside_line_y1 IS 'Outside line start Y (normalized 0.0-1.0, NULL = use default)';
COMMENT ON COLUMN cameras.outside_line_x2 IS 'Outside line end X (normalized 0.0-1.0, NULL = use default)';
COMMENT ON COLUMN cameras.outside_line_y2 IS 'Outside line end Y (normalized 0.0-1.0, NULL = use default)';
COMMENT ON COLUMN cameras.inside_line_x1 IS 'Inside line start X (normalized 0.0-1.0, NULL = use default)';
COMMENT ON COLUMN cameras.inside_line_y1 IS 'Inside line start Y (normalized 0.0-1.0, NULL = use default)';
COMMENT ON COLUMN cameras.inside_line_x2 IS 'Inside line end X (normalized 0.0-1.0, NULL = use default)';
COMMENT ON COLUMN cameras.inside_line_y2 IS 'Inside line end Y (normalized 0.0-1.0, NULL = use default)';
COMMENT ON COLUMN cameras.in_direction IS 'Direction that counts as IN: up, down, left, right';
COMMENT ON COLUMN cameras.line_color_r IS 'Line color Red component (0-255)';
COMMENT ON COLUMN cameras.line_color_g IS 'Line color Green component (0-255)';
COMMENT ON COLUMN cameras.line_color_b IS 'Line color Blue component (0-255)';
COMMENT ON COLUMN cameras.line_thickness IS 'Line thickness in pixels';
COMMENT ON COLUMN cameras.cooldown_frames IS 'Frames to wait before counting same person again';
COMMENT ON COLUMN cameras.min_track_length IS 'Minimum track length before counting';

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. All new columns are NULLABLE - NULL means "use default from config.yaml"
-- 2. Coordinates are normalized (0.0 to 1.0) for resolution independence
-- 3. Existing cameras will have NULL values = use defaults
-- 4. New cameras can specify custom lines or leave NULL for defaults
-- ============================================================================

