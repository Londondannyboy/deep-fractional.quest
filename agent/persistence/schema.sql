-- User Profiles table for Deep Fractional
-- Run this in Neon console or via psql

CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES neon_auth.user(id) ON DELETE CASCADE,
    role_preference VARCHAR(50),
    trinity VARCHAR(50),
    experience_years INTEGER,
    industries TEXT[],
    location VARCHAR(255),
    remote_preference VARCHAR(50),
    day_rate_min INTEGER,
    day_rate_max INTEGER,
    availability VARCHAR(100),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON public.user_profiles(user_id);

-- Comment for documentation
COMMENT ON TABLE public.user_profiles IS 'Stores onboarding data for fractional executives';
