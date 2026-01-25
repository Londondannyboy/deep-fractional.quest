-- Migration: Create jobs and saved_jobs tables for Phase 2.5
-- Run this in Neon Console: https://console.neon.tech/app/projects/sweet-hat-02969611/query

-- Jobs table: stores job listings
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    role_type VARCHAR(50) NOT NULL,  -- cto, cfo, cmo, coo, cpo
    engagement_type VARCHAR(50) NOT NULL,  -- fractional, interim, advisory
    description TEXT,
    location VARCHAR(255),
    remote_preference VARCHAR(50),  -- remote, hybrid, onsite, flexible
    day_rate_min INTEGER,
    day_rate_max INTEGER,
    industries TEXT[],
    requirements TEXT[],
    experience_years_min INTEGER,
    posted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for job search
CREATE INDEX IF NOT EXISTS idx_jobs_role_type ON public.jobs(role_type);
CREATE INDEX IF NOT EXISTS idx_jobs_engagement_type ON public.jobs(engagement_type);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON public.jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON public.jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_remote_preference ON public.jobs(remote_preference);

-- Saved jobs table: tracks user-saved jobs
CREATE TABLE IF NOT EXISTS public.saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES neon_auth.user(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    status VARCHAR(50) DEFAULT 'saved',  -- saved, applied, interviewing, rejected, accepted
    UNIQUE(user_id, job_id)
);

-- Indexes for saved jobs
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_id ON public.saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_job_id ON public.saved_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_status ON public.saved_jobs(status);

-- Insert sample job listings for testing
INSERT INTO public.jobs (title, company, role_type, engagement_type, description, location, remote_preference, day_rate_min, day_rate_max, industries, requirements, experience_years_min) VALUES
('Fractional CTO', 'TechStart Ltd', 'cto', 'fractional', 'Lead technical strategy for growing fintech startup. 2-3 days/week commitment.', 'London', 'hybrid', 800, 1200, ARRAY['Tech', 'Finance'], ARRAY['10+ years tech leadership', 'Startup experience', 'Financial services background'], 10),
('Interim CFO', 'GrowthCo', 'cfo', 'interim', 'Full-time interim CFO role for 6-month engagement during Series B fundraise.', 'Manchester', 'onsite', 1000, 1500, ARRAY['Tech', 'SaaS'], ARRAY['IPO experience', 'Series B/C fundraising', 'SaaS metrics expertise'], 15),
('Advisory CMO', 'BrandNew Agency', 'cmo', 'advisory', 'Strategic marketing advisor for digital agency. 1 day/week.', 'Remote', 'remote', 600, 900, ARRAY['Marketing', 'Digital', 'Agency'], ARRAY['B2B marketing expertise', 'Agency experience', 'Digital transformation'], 8),
('Fractional COO', 'ScaleUp Ventures', 'coo', 'fractional', 'Operational leadership for portfolio company. Help scale from 50 to 200 employees.', 'Birmingham', 'flexible', 850, 1100, ARRAY['Tech', 'Operations'], ARRAY['Scaling experience', 'Process optimization', 'Team building'], 12),
('Fractional CPO', 'ProductFirst', 'cpo', 'fractional', 'Product leadership for B2B SaaS company. Define roadmap and mentor team.', 'Edinburgh', 'hybrid', 750, 1000, ARRAY['Tech', 'SaaS', 'Product'], ARRAY['B2B SaaS product experience', 'Team leadership', 'Agile/Scrum'], 8),
('Interim CTO', 'HealthTech Solutions', 'cto', 'interim', 'Lead engineering team through platform migration. 4-6 month engagement.', 'London', 'hybrid', 1100, 1400, ARRAY['Healthcare', 'Tech'], ARRAY['Platform migration experience', 'Healthcare/compliance knowledge', 'Team of 20+ engineers'], 12),
('Fractional CFO', 'EcoStart', 'cfo', 'fractional', 'Financial leadership for sustainability startup. Seed to Series A journey.', 'Bristol', 'remote', 700, 950, ARRAY['CleanTech', 'Sustainability'], ARRAY['Early-stage startup experience', 'Fundraising', 'Financial modeling'], 10),
('Advisory CTO', 'Legacy Corp', 'cto', 'advisory', 'Technical advisor for digital transformation initiative. Board-level engagement.', 'London', 'onsite', 1200, 1800, ARRAY['Enterprise', 'Digital Transformation'], ARRAY['Enterprise architecture', 'Digital transformation', 'Board experience'], 15);
