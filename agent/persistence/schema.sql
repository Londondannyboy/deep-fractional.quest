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

-- =============================================================================
-- Jobs table for job postings (database + Tavily web search results)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT,
    url TEXT,
    role_type VARCHAR(50),
    engagement_type VARCHAR(50),
    location VARCHAR(255),
    remote_preference VARCHAR(50),
    day_rate_min INTEGER,
    day_rate_max INTEGER,
    industries TEXT[],
    source VARCHAR(50) DEFAULT 'manual',  -- 'manual', 'tavily', 'scraper', etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for faster job searches
CREATE INDEX IF NOT EXISTS idx_jobs_role_type ON public.jobs(role_type);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON public.jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_engagement ON public.jobs(engagement_type);
CREATE INDEX IF NOT EXISTS idx_jobs_url ON public.jobs(url);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON public.jobs(source);

COMMENT ON TABLE public.jobs IS 'Job postings from database and Tavily web search';

-- =============================================================================
-- Saved Jobs table (user's saved/bookmarked jobs)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES neon_auth.user(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'saved',  -- saved, applied, interviewing, rejected, accepted
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_id ON public.saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_status ON public.saved_jobs(status);

COMMENT ON TABLE public.saved_jobs IS 'User saved/bookmarked jobs with status tracking';
