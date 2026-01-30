# Deep Fractional - Comprehensive Phase 4 Restart Plan

## Mission

Production-ready fractional executive career platform using CopilotKit + LangGraph Deep Agents (Christian's pattern) with voice interface.

## Current Status: Phase 3 Complete - Voice Working, Auth Working

**Live URLs:**
- Frontend: https://deep-fractional-web.vercel.app
- Agent: https://agent-production-ccb0.up.railway.app
- GitHub: https://github.com/Londondannyboy/deep-fractional.quest
- Neon Project: `sweet-hat-02969611`
- Neon SQL Editor: https://console.neon.tech/app/projects/sweet-hat-02969611/sql-editor

---

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
│  └─────────────┬───────────────────┘  │    │  coaches ⚠️           │
│                │                      │    │  coaching_sessions ⚠️ │
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

**⚠️ = Needs migration 003 (see below)**

---

## What's Working

| Feature | Status | File Location |
|---------|--------|---------------|
| CopilotKit Chat | ✅ Working | `frontend/src/app/page.tsx` |
| HITL Confirmations | ✅ Working | `frontend/src/app/page.tsx:180-450` (11 hooks) |
| Hume EVI Voice | ✅ Working | `frontend/src/components/VoiceInput.tsx` |
| Voice → Sidebar Sync | ✅ Working | Via `appendMessage()` |
| Neon Auth (Email OTP) | ✅ Working | `frontend/src/app/auth/[path]/page.tsx` |
| Auth UI in Sidebar | ✅ Working | `frontend/src/app/page.tsx:95-115` |
| Onboarding Tools | ✅ Working | `agent/tools/onboarding.py` (6 tools) |
| Job Search Tools | ✅ Working | `agent/tools/jobs.py` (6 tools) |
| Coaching Tools | ⚠️ Code Ready | `agent/tools/coaching.py` (DB needed) |
| Memory Tools | ✅ Working | `agent/tools/memory.py` (3 tools) |
| PostgreSQL Checkpointer | ✅ Working | `agent/persistence/checkpointer.py` |

---

## IMMEDIATE ACTION REQUIRED

### 1. Run Coaching Migration 003

**Location:** Neon SQL Editor
**URL:** https://console.neon.tech/app/projects/sweet-hat-02969611/sql-editor

Copy-paste this SQL:

```sql
-- Migration 003: Coaching Tables
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

-- Seed 5 sample coaches
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

---

## Phase 4 Todo List (Priority Order)

### Phase 4.1: Voice + User Identity (PRIORITY)

| Task | File | Description |
|------|------|-------------|
| **Pass userId to Hume session** | `frontend/src/components/VoiceInput.tsx:45` | Include `user.id` from Neon Auth in Hume session metadata |
| **Extract userId in CLM endpoint** | `frontend/src/app/api/chat/completions/route.ts:25` | Parse userId from Hume session, pass to agent |
| **Voice triggers HITL in sidebar** | `frontend/src/app/page.tsx` | When voice calls a tool, show confirmation UI |

**Current Gap:** Voice transcripts bypass HITL because they go through `appendMessage()` directly. The agent processes them but doesn't trigger the `useHumanInTheLoop` render in sidebar.

**Solution Options:**
1. **Option A (Recommended):** Voice remains conversational (no modal confirmations). Agent confirms via speech: "I've saved that job for you."
2. **Option B:** Route voice through same HITL flow by having agent emit `interrupt` events that pause until user clicks confirm in sidebar.

### Phase 4.2: Christian's CopilotKit Patterns to Implement

These patterns from Christian's reference repos should be implemented:

#### Pattern 1: `useLangGraphInterrupt` for Custom Interrupt UI

**Reference:** `@copilotkit/react-core/hooks/use-langgraph-interrupt.ts`

```typescript
// frontend/src/app/page.tsx - Add custom interrupt handling
import { useLangGraphInterrupt } from "@copilotkit/react-core";

useLangGraphInterrupt({
  enabled: ({ eventValue, agentMetadata }) => {
    // Filter which interrupts this handler responds to
    return agentMetadata.nodeName === "onboarding-agent";
  },
  handler: ({ event, resolve }) => {
    // Pre-process the interrupt
    console.log("Interrupt received:", event.value);
  },
  render: ({ event, result, resolve }) => {
    // Render custom confirmation UI
    return (
      <div className="interrupt-dialog">
        <p>{event.value.message}</p>
        <button onClick={() => resolve("confirmed")}>Confirm</button>
        <button onClick={() => resolve("rejected")}>Cancel</button>
      </div>
    );
  }
});
```

#### Pattern 2: `copilotkitEmitState` for Progress Updates

**Reference:** `@copilotkit/sdk-js/langgraph/utils.ts:203-232`

```python
# agent/agent.py - Emit intermediate state during long operations
from copilotkit import copilotkit_emit_state

async def search_jobs_node(state, config):
    # Emit progress as we search
    await copilotkit_emit_state(config, {"search_progress": "Searching..."})

    # ... do search ...

    await copilotkit_emit_state(config, {"search_progress": "Found 15 matches"})

    return state
```

#### Pattern 3: `copilotkitCustomizeConfig` for Selective Emission

**Reference:** `@copilotkit/sdk-js/langgraph/utils.ts:51-152`

```python
# agent/agent.py - Control what gets emitted to frontend
from copilotkit import copilotkit_customize_config

config = copilotkit_customize_config(
    config,
    emit_messages=True,
    emit_tool_calls=["confirm_role_preference", "save_job"],  # Only emit these
    emit_intermediate_state=[
        {"state_key": "search_results", "tool": "search_jobs", "tool_argument": "results"}
    ]
)
```

#### Pattern 4: `copilotKitInterrupt` for HITL with Custom Actions

**Reference:** `@copilotkit/sdk-js/langgraph/utils.ts:422-491`

```python
# agent/tools/onboarding.py - Trigger HITL with action+args
from copilotkit import copilotkit_interrupt

def confirm_role_preference_node(state, config):
    # This triggers HITL with specific action signature
    response = copilotkit_interrupt(
        action="confirm_role",
        args={"role": state["proposed_role"], "confidence": 0.95}
    )

    if response["answer"] == "confirmed":
        return {"role_preference": state["proposed_role"]}
    else:
        return {"messages": [AIMessage(content="No problem, what role would you prefer?")]}
```

#### Pattern 5: Agent State Rendering with `useCoAgentStateRender`

**Reference:** CopilotKit docs - Shared State

```typescript
// frontend/src/app/page.tsx - Render agent state in UI
import { useCoAgentStateRender } from "@copilotkit/react-core";

useCoAgentStateRender({
  name: "fractional_quest",
  render: ({ state }) => {
    if (state.current_step !== undefined) {
      return (
        <OnboardingProgress
          step={state.current_step}
          role={state.role_preference}
          trinity={state.trinity}
        />
      );
    }
    return null;
  }
});
```

### Phase 4.3: Database & Data

| Task | Location | Description |
|------|----------|-------------|
| Run coaching migration | Neon SQL Editor | See SQL above |
| Seed more jobs | `agent/migrations/` | Add 20+ realistic fractional roles |
| Add profile editing | New tool | `update_profile_field(field, value)` |

### Phase 4.4: Refactoring (From Plan Analysis)

| Task | Current | Target | Lines Saved |
|------|---------|--------|-------------|
| Extract HITL components | `page.tsx:634 lines` | `~200 lines` | ~400 |
| Extract voice hooks | `VoiceInput.tsx:333 lines` | `~200 lines` | ~130 |
| Tool base classes | 3 files with duplication | Shared base | ~150 |
| CLM utilities | `route.ts:292 lines` | Extracted to lib/ | ~100 |

---

## Key File Reference

### Agent (Python - Railway)

| File | Lines | Purpose |
|------|-------|---------|
| `agent/agent.py` | ~300 | Deep Agents orchestrator + 3 subagents |
| `agent/main.py` | ~100 | FastAPI entrypoint with lifespan |
| `agent/state.py` | ~80 | TypedDict state schemas |
| `agent/tools/onboarding.py` | 504 | 6 onboarding tools + Pydantic schemas |
| `agent/tools/jobs.py` | 465 | 6 job search tools |
| `agent/tools/coaching.py` | 345 | 5 coaching tools |
| `agent/tools/memory.py` | 320 | Zep memory integration |
| `agent/persistence/neon.py` | 604 | asyncpg client for all DB operations |
| `agent/persistence/checkpointer.py` | ~50 | PostgreSQL checkpointer setup |

### Frontend (Next.js - Vercel)

| File | Lines | Purpose |
|------|-------|---------|
| `frontend/src/app/page.tsx` | 634 | Main UI + 11 HITL hooks |
| `frontend/src/app/layout.tsx` | 42 | CopilotKit + NeonAuth providers |
| `frontend/src/components/VoiceInput.tsx` | 333 | Hume EVI component |
| `frontend/src/app/api/copilotkit/route.ts` | ~35 | AG-UI endpoint |
| `frontend/src/app/api/hume-token/route.ts` | ~50 | Hume OAuth2 token |
| `frontend/src/app/api/chat/completions/route.ts` | 292 | CLM endpoint (Hume → Agent) |
| `frontend/src/app/api/auth/[...path]/route.ts` | ~30 | Neon Auth handler |
| `frontend/src/app/auth/[path]/page.tsx` | 25 | Auth pages |
| `frontend/src/lib/auth/client.ts` | ~10 | Neon Auth client |

---

## Environment Variables

### Vercel (frontend)

```bash
LANGGRAPH_DEPLOYMENT_URL=https://agent-production-ccb0.up.railway.app
NEON_AUTH_BASE_URL=https://ep-divine-waterfall-abig6fic.neonauth.eu-west-2.aws.neon.tech/neondb/auth
HUME_API_KEY=<from Hume dashboard>
HUME_SECRET_KEY=<from Hume dashboard>
NEXT_PUBLIC_HUME_CONFIG_ID=5900eabb-8de1-42cf-ba18-3a718257b3e7
ZEP_API_KEY=<from Zep Cloud>
```

### Railway (agent)

```bash
GOOGLE_API_KEY=<Gemini API key>
GOOGLE_MODEL=gemini-2.0-flash
DATABASE_URL=<Neon PostgreSQL connection string>
ZEP_API_KEY=<from Zep Cloud>
```

---

## PRD Reference

See `docs/PRD.md` for full product requirements including:

- **User Journey:** Onboarding (6 steps) → Job Search → Coaching
- **Validation Values:**
  ```python
  VALID_ROLES = ["cto", "cfo", "cmo", "coo", "cpo", "other"]
  VALID_TRINITY = ["fractional", "interim", "advisory", "open"]
  VALID_REMOTE = ["remote", "hybrid", "onsite", "flexible"]
  VALID_AVAILABILITY = ["immediately", "1_month", "3_months", "flexible"]
  ```
- **Success Metrics:** Onboarding completion rate, Time to complete, State sync reliability, HITL acceptance rate

---

## Christian's Patterns Summary

| Pattern | CopilotKit Reference | Our Implementation |
|---------|---------------------|-------------------|
| **Deep Agents** | `create_deep_agent()` | `agent/agent.py` ✅ |
| **HITL via interrupt_on** | `useHumanInTheLoop` | `page.tsx` (11 hooks) ✅ |
| **State Sync** | `useCopilotReadable` | `page.tsx:75-90` ✅ |
| **Agent State Render** | `useCoAgentStateRender` | Not yet implemented |
| **Custom Interrupts** | `useLangGraphInterrupt` | Not yet implemented |
| **Emit Intermediate State** | `copilotkitEmitState` | Not yet implemented |
| **Selective Emission** | `copilotkitCustomizeConfig` | Not yet implemented |

---

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

# Run Neon migration
# Open: https://console.neon.tech/app/projects/sweet-hat-02969611/sql-editor
# Paste SQL from above
```

---

## Hume Dashboard Setup

For voice to work:
- **EVI Config ID:** `5900eabb-8de1-42cf-ba18-3a718257b3e7`
- **CLM URL:** `https://deep-fractional-web.vercel.app/api/chat/completions` (optional)
- **Method:** POST
- **Format:** OpenAI-compatible

---

## Technical Notes

### Why Voice Bypasses HITL

Voice transcripts flow: `Hume EVI → VoiceInput.tsx → appendMessage() → CopilotKit → Agent`

The agent processes them as regular user messages, not as HITL confirmation responses. This is intentional for voice UX - you don't want modal dialogs interrupting voice conversations.

### Checkpointer Tables (Auto-Created)

LangGraph creates these automatically:
- `checkpoint_*` tables for conversation state

### Neon Auth Tables (Auto-Created)

Neon Auth manages:
- `neon_auth.user` - User accounts
- `neon_auth.session` - Active sessions
- `neon_auth.account` - OAuth providers

---

*Last updated: January 30, 2026 - Phase 3 Complete, Phase 4 Ready*
