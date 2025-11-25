-- 'cities' table
-- list of cities covered

CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100)
);


-- for login and signup
-- 'users' table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- stores hashed password
    created_at TIMESTAMT_PZ DEFAULT NOW()
);

-- 'road_segments' table
CREATE TABLE road_segments (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    path GEOGRAPHY(LINESTRING, 4326), -- the line of the road

    -- manual score (0-10) for how bad the road is
    static_hazard_score SMALLINT DEFAULT 0 CHECK (static_hazard_score >= 0 AND static_hazard_score <= 10)
);

-- 'flood_hotspots' table
-- waterlogging spots
CREATE TABLE flood_hotspots (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    location GEOGRAPHY(POINT, 4326), -- the location point
    description TEXT
);

-- 'reports' table
-- all live user "Fast Reports"
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    city_id INTEGER REFERENCES cities(id),
    location GEOGRAPHY(POINT, 4326), -- location of the hazard
    report_type VARCHAR(50) NOT NULL, -- "Construction", "Accident", etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ -- so reports can disappear after a few hours
);