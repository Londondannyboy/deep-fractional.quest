-- Migration: Create coaching tables
-- Phase 2.6: Coaching Agent

-- ============================================================================
-- Coaches Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.coaches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic info
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,  -- e.g., "Executive Coach", "Leadership Advisor"
    email VARCHAR(255),
    phone VARCHAR(50),
    photo_url TEXT,

    -- Expertise
    specialty VARCHAR(100) NOT NULL,  -- leadership, career_transition, executive_presence, strategy
    industries TEXT[] DEFAULT '{}',   -- tech, finance, healthcare, retail, etc.
    bio TEXT,
    credentials TEXT[],               -- certifications, degrees

    -- Ratings & Experience
    rating DECIMAL(2,1) DEFAULT 5.0,  -- 1.0-5.0
    sessions_completed INTEGER DEFAULT 0,
    years_experience INTEGER,

    -- Pricing
    hourly_rate INTEGER,              -- in GBP
    intro_call_free BOOLEAN DEFAULT true,

    -- Availability
    availability JSONB DEFAULT '{}'::jsonb,  -- {monday: ["9am-12pm", "2pm-5pm"], ...}
    timezone VARCHAR(50) DEFAULT 'Europe/London',

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for coaches
CREATE INDEX IF NOT EXISTS idx_coaches_specialty ON public.coaches(specialty);
CREATE INDEX IF NOT EXISTS idx_coaches_rating ON public.coaches(rating DESC);
CREATE INDEX IF NOT EXISTS idx_coaches_industries ON public.coaches USING GIN(industries);
CREATE INDEX IF NOT EXISTS idx_coaches_active ON public.coaches(is_active) WHERE is_active = true;


-- ============================================================================
-- Coaching Sessions Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.coaching_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    user_id UUID NOT NULL REFERENCES neon_auth.user(id) ON DELETE CASCADE,
    coach_id UUID NOT NULL REFERENCES public.coaches(id) ON DELETE CASCADE,

    -- Session details
    session_type VARCHAR(50) NOT NULL,  -- intro_call, coaching_session, strategy_deep_dive
    topic TEXT,
    notes TEXT,

    -- Scheduling
    preferred_date DATE,
    preferred_time VARCHAR(50),  -- morning, afternoon, evening
    confirmed_at TIMESTAMPTZ,
    scheduled_start TIMESTAMPTZ,
    scheduled_end TIMESTAMPTZ,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending',  -- pending, scheduled, completed, cancelled, no_show
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT,

    -- Feedback (post-session)
    user_rating INTEGER,  -- 1-5
    user_feedback TEXT,
    coach_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user ON public.coaching_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_coach ON public.coaching_sessions(coach_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON public.coaching_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_scheduled ON public.coaching_sessions(scheduled_start)
    WHERE status = 'scheduled';


-- ============================================================================
-- Seed Sample Coaches
-- ============================================================================

INSERT INTO public.coaches (name, title, specialty, industries, bio, rating, sessions_completed, hourly_rate, years_experience, credentials, photo_url)
VALUES
    (
        'Sarah Mitchell',
        'Executive Leadership Coach',
        'leadership',
        ARRAY['tech', 'finance', 'consulting'],
        'Former McKinsey partner with 20+ years helping C-suite executives unlock their leadership potential. Specializes in first-time CxO transitions and board-level presence.',
        4.9,
        342,
        350,
        22,
        ARRAY['ICF Master Certified Coach', 'MBA Harvard Business School', 'Executive Coach Training - Columbia'],
        'https://api.dicebear.com/7.x/personas/svg?seed=sarah'
    ),
    (
        'James Chen',
        'Career Transition Specialist',
        'career_transition',
        ARRAY['tech', 'startups', 'enterprise'],
        'Tech executive turned coach. Helped 200+ executives navigate career pivots, from corporate to startup, interim to permanent, and fractional roles. Deep network in the UK tech ecosystem.',
        4.8,
        189,
        275,
        15,
        ARRAY['ICF Professional Certified Coach', 'Former CTO x3', 'Startup mentor at Seedcamp'],
        'https://api.dicebear.com/7.x/personas/svg?seed=james'
    ),
    (
        'Amanda Foster',
        'Executive Presence Coach',
        'executive_presence',
        ARRAY['media', 'retail', 'consumer'],
        'Former BBC executive and public speaking champion. Helps leaders command the room, master media appearances, and communicate with impact. Clients include FTSE 100 CEOs.',
        4.9,
        276,
        400,
        18,
        ARRAY['Certified Speaking Professional', 'ICF Associate Certified Coach', 'Former BBC Director'],
        'https://api.dicebear.com/7.x/personas/svg?seed=amanda'
    ),
    (
        'David Okonkwo',
        'Strategy & Growth Advisor',
        'strategy',
        ARRAY['tech', 'fintech', 'saas'],
        'Serial entrepreneur (3 exits) and fractional CFO. Bridges the gap between strategy and execution. Specializes in scaling from Series A to Series C and preparing for exit.',
        4.7,
        156,
        325,
        20,
        ARRAY['CFA Charterholder', 'Former PE Partner', 'Stanford GSB Graduate'],
        'https://api.dicebear.com/7.x/personas/svg?seed=david'
    ),
    (
        'Emma Williams',
        'Fractional Executive Coach',
        'career_transition',
        ARRAY['all'],
        'Pioneer of fractional executive model in the UK. Author of "The Fractional Executive" and advisor to top fractional placement firms. Helps executives build sustainable portfolio careers.',
        5.0,
        423,
        375,
        25,
        ARRAY['ICF Master Certified Coach', 'Author & Keynote Speaker', 'Forbes Contributor'],
        'https://api.dicebear.com/7.x/personas/svg?seed=emma'
    )
ON CONFLICT DO NOTHING;


-- ============================================================================
-- Update Trigger
-- ============================================================================

-- Function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
DROP TRIGGER IF EXISTS update_coaches_updated_at ON public.coaches;
CREATE TRIGGER update_coaches_updated_at
    BEFORE UPDATE ON public.coaches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_sessions_updated_at ON public.coaching_sessions;
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON public.coaching_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
