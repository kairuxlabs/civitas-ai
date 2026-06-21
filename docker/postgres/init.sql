CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) UNIQUE NOT NULL DEFAULT 'hanoi',
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS districts (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) NOT NULL DEFAULT 'hanoi',
    name VARCHAR(100) NOT NULL,
    geojson JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) NOT NULL DEFAULT 'hanoi',
    district_id INTEGER REFERENCES districts(id),
    timestamp TIMESTAMPTZ NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    rain FLOAT,
    wind_speed FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aqi (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) NOT NULL DEFAULT 'hanoi',
    district_id INTEGER REFERENCES districts(id),
    timestamp TIMESTAMPTZ NOT NULL,
    pm25 FLOAT,
    pm10 FLOAT,
    co FLOAT,
    no2 FLOAT,
    aqi_index INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) NOT NULL DEFAULT 'hanoi',
    district_id INTEGER REFERENCES districts(id),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    impact_level VARCHAR(20) DEFAULT 'low',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS citizen_feedback (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) NOT NULL DEFAULT 'hanoi',
    district_id INTEGER REFERENCES districts(id),
    category VARCHAR(100),
    sentiment VARCHAR(20),
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS city_score (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) NOT NULL DEFAULT 'hanoi',
    district_id INTEGER REFERENCES districts(id),
    timestamp TIMESTAMPTZ NOT NULL,
    traffic_score FLOAT DEFAULT 0,
    environment_score FLOAT DEFAULT 0,
    citizen_score FLOAT DEFAULT 0,
    risk_score FLOAT DEFAULT 0,
    overall_score FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_decisions (
    id SERIAL PRIMARY KEY,
    city_id VARCHAR(50) NOT NULL DEFAULT 'hanoi',
    district_id INTEGER REFERENCES districts(id),
    query TEXT,
    prediction JSONB,
    impact JSONB,
    recommendations JSONB,
    confidence FLOAT,
    explanation JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed Hanoi districts
INSERT INTO cities (city_id, name) VALUES ('hanoi', 'Hà Nội') ON CONFLICT DO NOTHING;

INSERT INTO districts (city_id, name) VALUES
    ('hanoi', 'Hoàn Kiếm'),
    ('hanoi', 'Ba Đình'),
    ('hanoi', 'Đống Đa'),
    ('hanoi', 'Hai Bà Trưng'),
    ('hanoi', 'Hoàng Mai'),
    ('hanoi', 'Thanh Xuân'),
    ('hanoi', 'Cầu Giấy'),
    ('hanoi', 'Long Biên'),
    ('hanoi', 'Nam Từ Liêm'),
    ('hanoi', 'Bắc Từ Liêm'),
    ('hanoi', 'Tây Hồ'),
    ('hanoi', 'Hà Đông')
ON CONFLICT DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_weather_district_time ON weather(district_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_aqi_district_time ON aqi(district_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_city_score_district_time ON city_score(district_id, timestamp DESC);
