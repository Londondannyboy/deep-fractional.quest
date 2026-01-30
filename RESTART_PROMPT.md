# Deep Fractional - Restart Prompt

## Mission

Build a production-ready fractional executive career platform using CopilotKit + LangGraph Deep Agents (Christian's pattern) with voice interface.

## Current Status: Phase 3 Complete - Voice Integration Working

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
│  └─────────────┬───────────────────┘  │    │  coaches              │
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
| Coaching Tools | ✅ Working | 5 tools (DB migration needed) |
| Memory Tools | ✅ Working | Zep integration for facts |
| PostgreSQL Checkpointer | ✅ Working | Conversation persistence |
| Neon Auth | ⚠️ Partial | UI works, user_id not passed to voice yet |

## What's NOT Working Yet

1. **Voice doesn't know user identity** - VoiceInput needs to pass userId to session
2. **Coaching DB tables** - Need to run migration 003
3. **Jobs DB tables** - Need to seed with actual jobs data
4. **Profile persistence via voice** - CLM endpoint needs user_id from session

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
    └── 003_create_coaching_tables.sql
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

## Comparison: Legacy vs Christian's Pattern

| Aspect | fractional.quest (Legacy) | deep-fractional.quest (Christian's) |
|--------|---------------------------|-------------------------------------|
| Agent | Pydantic AI (single) | LangGraph Deep Agents (multi) |
| State Sync | Manual webhooks | AG-UI protocol (real-time) |
| HITL | None | `interrupt_on` + useHumanInTheLoop |
| Persistence | Zep only | PostgreSQL checkpointer + Zep |
| Voice Path | Hume → CLM → Pydantic | Hume → CLM → DeepAgents |
| Response Time | ~2-3s | ~1-2s (better routing) |
| Context Window | Single agent | Subagent-scoped (more focused) |

## Next Steps (Phase 4)

### Immediate
1. **Fix voice user identity** - Pass userId from Neon Auth session to VoiceInput
2. **Run coaching migration** - Execute 003_create_coaching_tables.sql on Neon
3. **Seed jobs database** - Add real job listings to jobs table

### Short-term
4. **CLM user context** - Extract user from Neon Auth session in CLM route
5. **Voice → Zep storage** - Store voice conversations to Zep for memory
6. **Error handling** - Add retry logic and graceful fallbacks

### Medium-term
7. **Profile editing** - Allow users to modify saved preferences
8. **Job matching algorithm** - Improve match scoring
9. **Coach availability** - Real-time availability checking

## Quick Commands

```bash
# Local development
cd agent && uv run python main.py          # Agent on :8123
cd frontend && npm run dev                  # Frontend on :3000

# Deploy
git add -A && git commit -m "message" && git push origin main

# Check Vercel env vars
cd frontend && vercel env ls

# Check Railway logs
railway logs -n 100
```

## Hume Dashboard Setup

For the CLM endpoint to work, configure in Hume dashboard:
- **EVI Config ID**: 5900eabb-8de1-42cf-ba18-3a718257b3e7
- **CLM URL**: https://deep-fractional-web.vercel.app/api/chat/completions
- **Method**: POST
- **Format**: OpenAI-compatible

---

*Last updated: January 2026 - Phase 3 Complete*
