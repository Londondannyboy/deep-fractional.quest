# Deep Fractional

LangChain Deep Agents + CopilotKit for fractional executive job matching.

## Status: Phase 4.1 In Progress (70% Complete)

| Phase | Status |
|-------|--------|
| Phase 1: Core Setup | COMPLETE |
| Phase 2.1: Pydantic Schemas | COMPLETE |
| Phase 2.2: HITL Confirmation | COMPLETE |
| Phase 2.3: Neon Persistence | COMPLETE |
| Phase 2.4: Neon Auth | COMPLETE |
| Phase 2.5: Job Search Agent | COMPLETE |
| Phase 2.6: Coaching Agent | COMPLETE (code) |
| Phase 2.7: PostgreSQL Checkpointer | COMPLETE |
| Phase 3: Hume EVI Voice | COMPLETE |
| Phase 4.1: Voice + User Identity | 70% COMPLETE |
| Phase 4.2: Middleware | IN PROGRESS |

**Assessment Score: 6/10** - See RESTART_PROMPT.md for detailed progress

## Production URLs

| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://deep-fractional-web.vercel.app |
| Agent (Railway) | https://agent-production-ccb0.up.railway.app |
| GitHub | https://github.com/Londondannyboy/deep-fractional.quest |

## Quick Start

```bash
# Agent (Python)
cd agent && uv run python main.py  # port 8123

# Frontend (Next.js)
cd frontend && npm run dev  # port 3000
```

## Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | LangChain Deep Agents (`create_deep_agent()`) |
| State Sync | CopilotKit AG-UI protocol |
| LLM | Gemini 2.0 Flash |
| Database | Neon PostgreSQL |
| Auth | Neon Auth (Google OAuth + Email OTP) |
| Checkpointer | AsyncPostgresSaver (langgraph-checkpoint-postgres) |
| Memory | Zep Cloud (cross-session facts/preferences) |
| Voice | Hume EVI (@humeai/voice-react) |
| Backend | FastAPI + uvicorn |
| Frontend | Next.js 15 + React 19 |
| Deploy | Railway (agent) + Vercel (frontend) |

## Key Files

**Agent:**
- `agent/agent.py` - Deep Agents graph with 3 subagents + HITL
- `agent/state.py` - TypedDict state schemas (user_id at top level)
- `agent/tools/onboarding.py` - 6 onboarding tools
- `agent/tools/jobs.py` - 6 job search tools
- `agent/tools/coaching.py` - 5 coaching tools
- `agent/tools/memory.py` - Zep memory integration
- `agent/persistence/neon.py` - asyncpg client for Neon PostgreSQL
- `agent/persistence/checkpointer.py` - PostgreSQL checkpointer
- `agent/main.py` - FastAPI entrypoint with lifespan

**Frontend (New/Updated in Phase 4):**
- `frontend/src/components/HITLCard.tsx` - HITL countdown timer card (NEW)
- `frontend/src/components/ProfileSidebar.tsx` - Confirmed DB state display (NEW)
- `frontend/src/components/providers.tsx` - NeonAuthUIProvider with Google OAuth (NEW)
- `frontend/src/app/api/zep-context/route.ts` - Zep memory fetch endpoint (NEW)
- `frontend/src/app/page.tsx` - Main UI + HITL hooks + ProfileSidebar
- `frontend/src/app/layout.tsx` - Providers wrapper
- `frontend/src/components/VoiceInput.tsx` - Hume EVI + Zep context
- `frontend/src/app/api/chat/completions/route.ts` - CLM endpoint (user_id extraction)
- `frontend/src/app/api/hume-token/route.ts` - Hume OAuth2 token

## Data Architecture

**Neon (Database) = Confirmed Data**
- `user_profiles` table stores HITL-confirmed preferences
- Data is authoritative and persisted after user confirmation

**Zep (Knowledge Graph) = Mentioned Facts**
- Stores facts/preferences mentioned in conversation
- Cross-session memory for voice context enrichment

## Key Patterns (Christian Bromann's Approach)

1. **Agent Creation**: `create_deep_agent()` with `CopilotKitMiddleware()` + `interrupt_on`
2. **Subagents**: onboarding-agent, job-search-agent, coaching-agent
3. **Tools**: `@tool(args_schema=PydanticModel)`, accept `user_id` for persistence
4. **HITL**: `interrupt_on` dict + `HITLCard` component with countdown timer
5. **User Identity**: `user_id` at top level of state, flows from Neon Auth -> Voice -> Agent
6. **Checkpointer**: `AsyncPostgresSaver` persists conversations
7. **Memory**: Zep stores cross-session facts, enriches voice prompts
8. **Auth**: `NeonAuthUIProvider` with Google OAuth
9. **State Sync**: `useCopilotReadable()` + `ProfileSidebar` visualization

## Phase 4 Progress

### Completed
- Voice + User Identity flow (VoiceInput -> CLM -> Agent)
- Google OAuth in Neon Auth
- Voice to CopilotKit message sync fix
- Zep context integration for voice
- HITL countdown timer (HITLCard component)
- Profile sidebar visualization (confirmed DB state)

### In Progress
- Summarization Middleware (75% token reduction)

### Remaining
- Tool Call Limit Middleware
- Voice/Chat context sharing
- Voice HITL announcements
- Update remaining HITL hooks with HITLCard
- `useCoAgentStateRender` for live state display
- `copilotkitEmitState` for progress updates

## Environment Variables

**Railway (agent):**
- `GOOGLE_API_KEY` - Gemini API key
- `GOOGLE_MODEL` - gemini-2.0-flash
- `DATABASE_URL` - Neon PostgreSQL connection string
- `ZEP_API_KEY` - Zep Cloud API key
- `ZEP_GRAPH` - fractional-jobs-graph

**Vercel (frontend):**
- `LANGGRAPH_DEPLOYMENT_URL` - Railway agent URL
- `NEON_AUTH_BASE_URL` - Neon Auth endpoint
- `HUME_API_KEY` - Hume API key (server-side)
- `HUME_SECRET_KEY` - Hume secret key (server-side)
- `NEXT_PUBLIC_HUME_CONFIG_ID` - Hume EVI config ID
- `ZEP_API_KEY` - Zep Cloud API key
- `ZEP_GRAPH` - fractional-jobs-graph

## Database Schema

**Neon Project:** sweet-hat-02969611

**Tables:**
- `neon_auth.*` - Neon Auth tables (user, session, etc.)
- `public.user_profiles` - Onboarding data
- `public.jobs` - Job listings
- `public.saved_jobs` - User saved jobs with status tracking
- `public.coaches` - Executive coach profiles
- `public.coaching_sessions` - User coaching session bookings
- `checkpoint_*` - LangGraph checkpointer tables (auto-created)

## Tools Summary

### Onboarding Tools (6)

| Tool | Description | HITL |
|------|-------------|------|
| `get_profile_status` | Check user's onboarding progress | No |
| `confirm_role_preference` | Set C-level role (CTO, CFO, etc.) | Yes |
| `confirm_trinity` | Set engagement type (Fractional, Interim, Advisory) | Yes |
| `confirm_experience` | Set years and industries | Yes |
| `confirm_location` | Set location and remote preference | Yes |
| `confirm_search_prefs` | Set day rate and availability | Yes |
| `complete_onboarding` | Finalize onboarding | Yes |

### Job Search Tools (6)

| Tool | Description | HITL |
|------|-------------|------|
| `search_jobs` | Search jobs with filters | No |
| `match_jobs` | Find jobs matching user profile | No |
| `save_job` | Save a job to user's list | Yes |
| `get_saved_jobs` | Get user's saved jobs | No |
| `update_job_status` | Update job status | Yes |
| `get_job_details` | Get full job details | No |

### Coaching Tools (5)

| Tool | Description | HITL |
|------|-------------|------|
| `find_coaches` | Search coaches by specialty/industry | No |
| `get_coach_details` | Get full coach profile | No |
| `schedule_session` | Book a coaching session | Yes |
| `get_my_sessions` | Get user's coaching sessions | No |
| `cancel_session` | Cancel an upcoming session | Yes |

### Memory Tools (3)

| Tool | Description | HITL |
|------|-------------|------|
| `get_user_memory` | Retrieve Zep facts/preferences | No |
| `save_user_preference` | Store a preference to Zep | Yes |
| `save_user_fact` | Store a fact to Zep | Yes |

## Session Restart

**See RESTART_PROMPT.md for:**
- Complete session progress summary
- Architecture diagram
- New component documentation
- Code change details
- Next steps with implementation examples
- Environment variable reference

*Last updated: January 30, 2026*
