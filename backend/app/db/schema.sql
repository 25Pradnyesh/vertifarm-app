-- ==============================================================================
-- VertiFarm PostgreSQL & Supabase Database Schema
-- Stage 4: Backend & Database Foundation
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 1. Users / Profiles Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(128) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'Farm Owner',
    farm_name VARCHAR(255) DEFAULT 'Greenhouse 1',
    avatar_url TEXT,
    auth_provider VARCHAR(50) DEFAULT 'google',
    google_id VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- ==============================================================================
-- 2. Farms Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS farms (
    id VARCHAR(128) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    owner_id VARCHAR(128) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    sensor_count INTEGER DEFAULT 0,
    zone_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_farms_owner_id ON farms(owner_id);

-- ==============================================================================
-- 3. Zones Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS zones (
    id VARCHAR(128) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    farm_id VARCHAR(128) NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    crop VARCHAR(255) NOT NULL,
    sensor_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_zones_farm_id ON zones(farm_id);

-- ==============================================================================
-- 4. Sensors / Hardware Devices Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS sensors (
    id VARCHAR(128) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    farm_id VARCHAR(128) NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    zone_id VARCHAR(128) REFERENCES zones(id) ON DELETE SET NULL,
    zone_name VARCHAR(255) DEFAULT 'Zone 1',
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,          -- e.g. DHT22, Capacitive, Analog, BH1750, ESP32-CAM
    metric VARCHAR(50) NOT NULL,          -- temperature, humidity, soilMoisture, ph, tds, light, camera
    status VARCHAR(50) DEFAULT 'active',  -- active, warning, offline
    last_seen VARCHAR(100) DEFAULT 'Just now',
    battery_level INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sensors_farm_id ON sensors(farm_id);
CREATE INDEX IF NOT EXISTS idx_sensors_zone_id ON sensors(zone_id);
CREATE INDEX IF NOT EXISTS idx_sensors_metric ON sensors(metric);

-- ==============================================================================
-- 5. Sensor Readings (Telemetry Time-Series)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS sensor_readings (
    id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(128) REFERENCES sensors(id) ON DELETE CASCADE,
    farm_id VARCHAR(128) REFERENCES farms(id) ON DELETE CASCADE,
    metric VARCHAR(50) NOT NULL,
    value NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'healthy', -- healthy, warning, critical
    status_label VARCHAR(100),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_readings_sensor_time ON sensor_readings(sensor_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_readings_farm_metric ON sensor_readings(farm_id, metric, timestamp DESC);

-- ==============================================================================
-- 6. Alerts Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(128) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    farm_id VARCHAR(128) NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    zone_id VARCHAR(128) REFERENCES zones(id) ON DELETE SET NULL,
    zone_name VARCHAR(255) NOT NULL,
    metric VARCHAR(50) NOT NULL,
    severity VARCHAR(50) NOT NULL,        -- critical, warning, info
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    current_value VARCHAR(100) NOT NULL,
    threshold_value VARCHAR(100) NOT NULL,
    is_resolved BOOLEAN DEFAULT false,
    recommendation TEXT NOT NULL,
    timestamp VARCHAR(100) DEFAULT 'Just now',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_farm_id ON alerts(farm_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_is_resolved ON alerts(is_resolved);

-- ==============================================================================
-- 7. AI Plant Health Scans Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS ai_scans (
    id VARCHAR(128) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    farm_id VARCHAR(128) REFERENCES farms(id) ON DELETE CASCADE,
    user_id VARCHAR(128) REFERENCES users(id) ON DELETE CASCADE,
    plant_type VARCHAR(255) NOT NULL,
    disease_name VARCHAR(255) NOT NULL,
    is_healthy BOOLEAN DEFAULT false,
    confidence NUMERIC(5, 2) NOT NULL,
    image_url TEXT NOT NULL,
    timestamp VARCHAR(100) NOT NULL,
    recommendations JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_scans_farm_id ON ai_scans(farm_id);
CREATE INDEX IF NOT EXISTS idx_ai_scans_user_id ON ai_scans(user_id);

-- ==============================================================================
-- 8. Camera Captures Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS camera_captures (
    id VARCHAR(128) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    camera_id VARCHAR(100) NOT NULL,
    farm_id VARCHAR(128) REFERENCES farms(id) ON DELETE CASCADE,
    zone_name VARCHAR(255) NOT NULL,
    image_url TEXT NOT NULL,
    timestamp VARCHAR(100) NOT NULL,
    is_live BOOLEAN DEFAULT true,
    next_capture_in VARCHAR(50) DEFAULT '05:00',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_camera_captures_farm_id ON camera_captures(farm_id);

-- ==============================================================================
-- 9. Recommendations Table
-- ==============================================================================
CREATE TABLE IF NOT EXISTS recommendations (
    id VARCHAR(128) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    farm_id VARCHAR(128) REFERENCES farms(id) ON DELETE CASCADE,
    user_id VARCHAR(128) REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,        -- irrigation, ph, nutrition, environment, disease
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(50) NOT NULL,        -- high, medium, low
    tab VARCHAR(50) NOT NULL,             -- forYou, general
    actionable_link VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_tab ON recommendations(tab);

-- ==============================================================================
-- Row Level Security (RLS) Policies for Supabase
-- Ensures strict user isolation by farm ownership
-- ==============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE farms ENABLE ROW LEVEL SECURITY;
ALTER TABLE zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensors ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE camera_captures ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

-- Users policy
CREATE POLICY "Users can view and update own profile"
    ON users FOR ALL
    USING (auth.uid()::text = id);

-- Farms policy
CREATE POLICY "Users can manage own farms"
    ON farms FOR ALL
    USING (auth.uid()::text = owner_id);

-- Zones policy
CREATE POLICY "Users can access zones of own farms"
    ON zones FOR ALL
    USING (EXISTS (SELECT 1 FROM farms WHERE farms.id = zones.farm_id AND farms.owner_id = auth.uid()::text));

-- Sensors policy
CREATE POLICY "Users can access sensors of own farms"
    ON sensors FOR ALL
    USING (EXISTS (SELECT 1 FROM farms WHERE farms.id = sensors.farm_id AND farms.owner_id = auth.uid()::text));

-- Telemetry readings policy
CREATE POLICY "Users can access readings of own farms"
    ON sensor_readings FOR ALL
    USING (EXISTS (SELECT 1 FROM farms WHERE farms.id = sensor_readings.farm_id AND farms.owner_id = auth.uid()::text));

-- Alerts policy
CREATE POLICY "Users can access alerts of own farms"
    ON alerts FOR ALL
    USING (EXISTS (SELECT 1 FROM farms WHERE farms.id = alerts.farm_id AND farms.owner_id = auth.uid()::text));

-- Scans policy
CREATE POLICY "Users can access own scans"
    ON ai_scans FOR ALL
    USING (auth.uid()::text = user_id OR EXISTS (SELECT 1 FROM farms WHERE farms.id = ai_scans.farm_id AND farms.owner_id = auth.uid()::text));

-- Recommendations policy
CREATE POLICY "Users can access own recommendations"
    ON recommendations FOR ALL
    USING (user_id IS NULL OR auth.uid()::text = user_id);
