-- StayFit Database Schema
-- PostgreSQL

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INTEGER,
    gender VARCHAR(20),
    weight_kg FLOAT,
    height_cm FLOAT,
    activity_level VARCHAR(30) DEFAULT 'moderate',
    goal VARCHAR(20) DEFAULT 'maintain',
    daily_calorie_budget INTEGER DEFAULT 2000,
    profile_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meals table
CREATE TABLE IF NOT EXISTS meals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_type VARCHAR(20) NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    image_url VARCHAR(500),
    food_items JSONB DEFAULT '[]',
    total_calories INTEGER DEFAULT 0,
    protein_g FLOAT DEFAULT 0,
    carbs_g FLOAT DEFAULT 0,
    fat_g FLOAT DEFAULT 0,
    fiber_g FLOAT DEFAULT 0,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily logs table (aggregated per day)
CREATE TABLE IF NOT EXISTS daily_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    total_calories INTEGER DEFAULT 0,
    total_protein_g FLOAT DEFAULT 0,
    total_carbs_g FLOAT DEFAULT 0,
    total_fat_g FLOAT DEFAULT 0,
    budget INTEGER DEFAULT 2000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, log_date)
);

-- Indexes for performance
CREATE INDEX idx_meals_user_id ON meals(user_id);
CREATE INDEX idx_meals_logged_at ON meals(logged_at);
CREATE INDEX idx_meals_user_date ON meals(user_id, logged_at);
CREATE INDEX idx_daily_logs_user_date ON daily_logs(user_id, log_date);
