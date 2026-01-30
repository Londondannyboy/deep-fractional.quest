# Deep Fractional - Restart Prompt (Phase 4)

## Mission

Production-ready fractional executive career platform using CopilotKit + LangGraph Deep Agents with voice interface.

## Current Status: Phase 3 Complete - Ready for Phase 4

**Live URLs:**
- Frontend: https://deep-fractional-web.vercel.app
- Agent: https://agent-production-ccb0.up.railway.app
- GitHub: https://github.com/Londondannyboy/deep-fractional.quest

## Architecture (Christian's CopilotKit Pattern)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │   CopilotChat   │◄───│   VoiceInput    │    │  NeonAuthUI    │  │
│  │   (sidebar)     │    │   (Hume EVI)    │    │  (sign-in)     │  │
│  │                 │    │                 │    │                │  │
│  │ useHumanInTheLoop│    │ appendMessage() │    │ useSession()   │  │
│  └────────┬────────┘    └────────┬────────┘    └───────┬────────┘  │
│           │                      │                      │          │
│           ▼                      ▼                      │          │
│  ┌─────────────────┐    ┌─────────────────┐            │          │
│  │ /api/copilotkit │    │ /api/hume-token │            │          │
│  │ (AG-UI route)   │    │ (OAuth2 CC)     │            │          │
│  └────────┬────────┘    └─────────────────┘            │          │
│           │                                             │          │
└───────────┼─────────────────────────────────────────────┼──────────┘
            │                                             │
            ▼                                             ▼
┌───────────────────────────────────────┐    ┌───────────────────────┐
│       DeepAgents (Railway)            │    │    Neon PostgreSQL    │
│                                       │    │                       │
│  ┌─────────────────────────────────┐  │    │  user_profiles        │
│  │         ORCHESTRATOR            │  │    │  jobs                 │
│  │   (routes to subagents)         │  │    │  saved_jobs           │
│  └─────────────┬───────────────────┘  │    │  coaches (NEEDS MIGRATION) │
│                │                      │    │  coaching_sessions    │
│   ┌────────────┼────────────┐        │    │  checkpoint_*         │
│   ▼            ▼            ▼        │    │  neon_auth.*          │
│ ┌─────┐    ┌─────┐    ┌─────────┐   │    └───────────────────────┘
│ │Onb. │    │Jobs │    │Coaching │   │
│ │Agent│    │Agent│    │Agent    │   │    ┌───────────────────────┐
│ └──┬──┘    └──┬──┘    └────┬────┘   │    │      Zep Cloud        │
│    │          │            │         │    │   (cross-session      │
│    ▼          ▼            ▼         │    │    memory/facts)      │
│  6 tools    6 tools     5 tools      │    └───────────────────────┘
│  + HITL     + HITL      + HITL       │
│                                       │    ┌───────────────────────┐
│  CopilotKitMiddleware                │    │     Hume EVI Cloud    │
│  AsyncPostgresSaver (checkpointer)   │◄───│   (voice interface)   │
│  Gemini 2.0 Flash                    │    └───────────────────────┘
└───────────────────────────────────────┘
```

## What's Working

| Feature | Status | Notes |
|---------|--------|-------|
| CopilotKit Chat | ✅ Working | Sidebar with tool execution UI |
| Hume EVI Voice | ✅ Working | Voice → transcript → sidebar |
| Onboarding Tools | ✅ Working | 6 tools with HITL confirmation |
| Job Search Tools | ✅ Working | 6 tools for search/save/track |
| Coaching Tools | ⚠️ Code Ready | DB migration needed (see below) |
| Memory Tools | ✅ Working | Zep integration for facts |
| PostgreSQL Checkpointer | ✅ Working | Conversation persistence |
| Neon Auth | ✅ Working | Email OTP login, session management |
| Auth UI | ✅ Working | Sign-in/out links in sidebar |

## What's NOT Working Yet

### 1. Coaching Database Tables (MANUAL ACTION REQUIRED)

Run this in Neon SQL Editor (Project: `sweet-hat-02969611`):

```sql
-- Copy from: agent/migrations/003_create_coaching_tables.sql
-- Or run in Neon console: https://console.neon.tech/app/projects/sweet-hat-02969611/sql-editor
```

Full migration SQL:
```sql
CREATE TABLE IF NOT EXISTS public.coaches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    photo_url TEXT,
    specialty VARCHAR(100) NOT NULL,
    industries TEXT[] DEFAULT '{}',
    bio TEXT,
    credentials TEXT[],
    rating DECIMAL(2,1) DEFAULT 5.0,
    sessions_completed INTEGER DEFAULT 0,
    years_experience INTEGER,
    hourly_rate INTEGER,
    intro_call_free BOOLEAN DEFAULT true,
    availability JSONB DEFAULT '{}'::jsonb,
    timezone VARCHAR(50) DEFAULT 'Europe/London',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_coaches_specialty ON public.coaches(specialty);
CREATE INDEX IF NOT EXISTS idx_coaches_rating ON public.coaches(rating DESC);
CREATE INDEX IF NOT EXISTS idx_coaches_industries ON public.coaches USING GIN(industries);

CREATE TABLE IF NOT EXISTS public.coaching_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES neon_auth.user(id) ON DELETE CASCADE,
    coach_id UUID NOT NULL REFERENCES public.coaches(id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL,
    topic TEXT,
    notes TEXT,
    preferred_date DATE,
    preferred_time VARCHAR(50),
    confirmed_at TIMESTAMPTZ,
    scheduled_start TIMESTAMPTZ,
    scheduled_end TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT,
    user_rating INTEGER,
    user_feedback TEXT,
    coach_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON public.coaching_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_coach ON public.coaching_sessions(coach_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON public.coaching_sessions(status);

-- Seed sample coaches
INSERT INTO public.coaches (name, title, specialty, industries, bio, rating, sessions_completed, hourly_rate, years_experience, credentials, photo_url)
VALUES
    ('Sarah Mitchell', 'Executive Leadership Coach', 'leadership',
     ARRAY['tech', 'finance', 'consulting'],
     'Former McKinsey partner with 20+ years helping C-suite executives.', 4.9, 342, 350, 22,
     ARRAY['ICF Master Certified Coach', 'MBA Harvard Business School'],
     'https://api.dicebear.com/7.x/personas/svg?seed=sarah'),
    ('James Chen', 'Career Transition Specialist', 'career_transition',
     ARRAY['tech', 'startups', 'enterprise'],
     'Tech executive turned coach. Helped 200+ executives navigate career pivots.', 4.8, 189, 275, 15,
     ARRAY['ICF Professional Certified Coach', 'Former CTO x3'],
     'https://api.dicebear.com/7.x/personas/svg?seed=james'),
    ('Amanda Foster', 'Executive Presence Coach', 'executive_presence',
     ARRAY['media', 'retail', 'consumer'],
     'Former BBC executive and public speaking champion.', 4.9, 276, 400, 18,
     ARRAY['Certified Speaking Professional', 'Former BBC Director'],
     'https://api.dicebear.com/7.x/personas/svg?seed=amanda'),
    ('David Okonkwo', 'Strategy & Growth Advisor', 'strategy',
     ARRAY['tech', 'fintech', 'saas'],
     'Serial entrepreneur (3 exits) and fractional CFO.', 4.7, 156, 325, 20,
     ARRAY['CFA Charterholder', 'Former PE Partner'],
     'https://api.dicebear.com/7.x/personas/svg?seed=david'),
    ('Emma Williams', 'Fractional Executive Coach', 'career_transition',
     ARRAY['all'],
     'Pioneer of fractional executive model in the UK.', 5.0, 423, 375, 25,
     ARRAY['ICF Master Certified Coach', 'Author & Keynote Speaker'],
     'https://api.dicebear.com/7.x/personas/svg?seed=emma')
ON CONFLICT DO NOTHING;
```

### 2. Google OAuth (Optional Enhancement)

The NeonAuthUIProvider's `socialProviders` prop doesn't exist in current types. Options:
1. Use email OTP only (current - works fine)
2. Configure Google OAuth in Neon dashboard directly
3. Wait for @neondatabase/auth update with social provider support

### 3. Voice HITL Confirmations

Current architecture: Voice bypasses HITL confirmations (goes direct to agent via transcript).
This is intentional for voice UX but means voice can't confirm tool calls.

Options for Phase 4:
- Keep as-is (voice is conversational, chat is transactional)
- Add voice-specific confirmation prompts in agent responses
- Route voice through same HITL flow (requires architectural change)

### 4. Jobs Seed Data

The `jobs` table exists but may need more realistic seed data for demos.

## Key Files

**Agent (Python - Railway):**
```
agent/
├── agent.py              # Deep Agents orchestrator + 3 subagents
├── main.py               # FastAPI with lifespan management
├── state.py              # TypedDict state schemas
├── tools/
│   ├── onboarding.py     # 6 onboarding tools + HITL
│   ├── jobs.py           # 6 job search tools
│   ├── coaching.py       # 5 coaching tools
│   └── memory.py         # Zep memory integration
├── persistence/
│   ├── neon.py           # asyncpg client
│   └── checkpointer.py   # PostgreSQL checkpointer
└── migrations/
    ├── 002_create_jobs_tables.sql
    └── 003_create_coaching_tables.sql  # ← RUN THIS MANUALLY
```

**Frontend (Next.js - Vercel):**
```
frontend/src/
├── app/
│   ├── page.tsx                    # Main UI + 11 HITL hooks
│   ├── layout.tsx                  # CopilotKit + NeonAuth providers
│   ├── api/
│   │   ├── copilotkit/route.ts     # AG-UI endpoint
│   │   ├── hume-token/route.ts     # OAuth2 token for Hume
│   │   ├── chat/completions/route.ts # CLM endpoint (Hume → Agent)
│   │   └── auth/[...path]/route.ts # Neon Auth handler
│   └── auth/[path]/page.tsx        # Sign-in/sign-up pages
├── components/
│   └── VoiceInput.tsx              # Hume EVI component
└── lib/auth/
    └── client.ts                   # Neon Auth client
```

## Environment Variables

**Vercel (frontend):**
```
LANGGRAPH_DEPLOYMENT_URL=https://agent-production-ccb0.up.railway.app
NEON_AUTH_BASE_URL=https://ep-divine-waterfall-abig6fic.neonauth.eu-west-2.aws.neon.tech/neondb/auth
HUME_API_KEY=<from Hume dashboard>
HUME_SECRET_KEY=<from Hume dashboard>
NEXT_PUBLIC_HUME_CONFIG_ID=5900eabb-8de1-42cf-ba18-3a718257b3e7
ZEP_API_KEY=<from Zep Cloud>
```

**Railway (agent):**
```
GOOGLE_API_KEY=<Gemini API key>
GOOGLE_MODEL=gemini-2.0-flash
DATABASE_URL=<Neon PostgreSQL connection string>
ZEP_API_KEY=<from Zep Cloud>
```

## Phase 4 Todo List

### Immediate (Before Next Session)

- [ ] **Run coaching migration 003** - Manual SQL in Neon console
- [ ] **Test full flow end-to-end** - Onboarding → Job Search → Coaching
- [ ] **Verify voice + chat sync** - Both should show same conversation

### Short-term Enhancements

- [ ] **More jobs seed data** - Add 20+ realistic fractional exec roles
- [ ] **Profile editing** - Allow users to modify saved preferences
- [ ] **Job application tracking** - Add status workflow (applied → interviewing → offer)
- [ ] **Session feedback** - Post-coaching session ratings

### Medium-term Features

- [ ] **Job matching algorithm** - Score jobs based on profile match %
- [ ] **Coach availability** - Real-time calendar integration
- [ ] **Push notifications** - New job alerts, session reminders
- [ ] **Analytics dashboard** - Application stats, profile views

### Code Quality (Refactoring)

- [ ] **Extract HITL components** - page.tsx from 634 → ~200 lines
- [ ] **Extract voice hooks** - VoiceInput.tsx cleanup
- [ ] **Tool base classes** - Reduce duplication across tools
- [ ] **Add tests** - Unit tests for critical paths

## Quick Commands

```bash
# Local development
cd agent && uv run python main.py          # Agent on :8123
cd frontend && npm run dev                  # Frontend on :3000

# Deploy
git add -A && git commit -m "message" && git push origin main

# Check Vercel
cd frontend && vercel env ls

# Check Railway logs
railway logs -n 100

# Run migration (in Neon SQL Editor)
# https://console.neon.tech/app/projects/sweet-hat-02969611/sql-editor
```

## Hume Dashboard Setup

For voice to work, ensure in Hume dashboard:
- **EVI Config ID**: 5900eabb-8de1-42cf-ba18-3a718257b3e7
- **CLM URL**: https://deep-fractional-web.vercel.app/api/chat/completions (optional)
- **Method**: POST
- **Format**: OpenAI-compatible

## Technical Notes

### Why Voice Bypasses HITL

Voice transcripts go through `appendMessage()` to CopilotKit, then to the agent. The agent processes them as regular messages, not tool confirmation requests. This is by design:

1. Voice UX should be conversational, not modal
2. HITL confirmations are visual (buttons in sidebar)
3. Voice users get confirmations via agent response ("I've saved that job for you")

### Checkpointer Tables

LangGraph auto-creates these tables:
- `checkpoint_*` - Conversation state snapshots
- These persist conversation history across browser refreshes

### Neon Auth Tables

Neon Auth manages:
- `neon_auth.user` - User accounts
- `neon_auth.session` - Active sessions
- `neon_auth.account` - OAuth providers (future)

---

*Last updated: January 30, 2026 - Phase 3 Complete, Phase 4 Ready*
