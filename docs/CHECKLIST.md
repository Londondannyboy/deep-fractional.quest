# Implementation Checklist

## Phase 0: Setup

- [x] Create GitHub repo
- [x] Clone repo locally
- [x] Create directory structure
- [x] Create CLAUDE.md
- [x] Create docs/ARTICLE_BREAKDOWN.md
- [x] Create docs/ARCHITECTURE.md
- [x] Create docs/PRD.md
- [x] Create docs/CHECKLIST.md
- [x] Set up UV project for agent/
- [x] Set up Next.js for frontend/
- [x] Initial commit and push

## Phase 1: Onboarding Flow

### Backend (agent/)

- [x] `agent/pyproject.toml` - UV project config
- [x] `agent/state.py` - TypedDict state schemas
- [x] `agent/tools/__init__.py`
- [x] `agent/tools/onboarding.py` - 6 HITL tools
  - [x] `confirm_role_preference`
  - [x] `confirm_trinity`
  - [x] `confirm_experience`
  - [x] `confirm_location`
  - [x] `confirm_search_prefs`
  - [x] `complete_onboarding`
- [x] `agent/agent.py` - create_deep_agent with subagents
- [x] `agent/main.py` - FastAPI with AG-UI endpoint
- [x] `agent/.env` - Environment variables
- [x] Test agent locally (port 8123)

### Frontend (frontend/)

- [x] `frontend/package.json` - Dependencies
- [x] `frontend/src/app/layout.tsx` - CopilotKit provider
- [x] `frontend/src/app/page.tsx` - Main UI (includes chat, progress, profile)
- [x] `frontend/src/app/api/copilotkit/route.ts` - CopilotKit runtime
- [ ] `frontend/src/components/ChatPanel.tsx` - Chat with tool capture (integrated in page.tsx)
- [ ] `frontend/src/components/OnboardingProgress.tsx` - Step indicator (integrated in page.tsx)
- [ ] `frontend/src/components/ProfileCard.tsx` - Profile display (integrated in page.tsx)
- [x] `frontend/.env.local` - LANGGRAPH_DEPLOYMENT_URL
- [x] Test frontend locally (port 3000)

### Integration

- [ ] Frontend connects to backend
- [ ] Tool calls visible in chat
- [ ] State syncs from tools to UI
- [ ] Onboarding progress updates
- [ ] Profile card updates

## Phase 2: Job Search

- [ ] `agent/tools/jobs.py` - search_jobs, match_jobs, save_job
- [ ] Add job-search-agent to subagents
- [ ] `frontend/src/components/JobCard.tsx`
- [ ] `frontend/src/components/JobsList.tsx`
- [ ] Test job search flow

## Phase 3: Coaching

- [ ] `agent/tools/coaching.py` - find_coaches, schedule_session
- [ ] Add coaching-agent to subagents
- [ ] `frontend/src/components/CoachCard.tsx`
- [ ] Test coaching flow

## Phase 4: Database Integration

- [ ] Neon connection in agent
- [ ] Persist user profiles
- [ ] Persist job saves
- [ ] Session recovery

## Phase 5: Deployment

- [ ] Create Railway project
- [ ] Deploy agent to Railway
- [ ] Set Railway environment variables
- [ ] Create Vercel project
- [ ] Deploy frontend to Vercel
- [ ] Set Vercel environment variables
- [ ] Test production deployment
- [ ] Verify state sync in production

## Verification Tests

- [ ] Agent responds to greeting
- [ ] Onboarding routes to onboarding-agent
- [ ] Each tool updates state correctly
- [ ] State syncs to frontend
- [ ] Tool results render in chat
- [ ] Progress stepper advances
- [ ] Profile card updates
- [ ] Onboarding completion works
- [ ] Post-onboarding routes correctly
- [ ] Production deployment works
