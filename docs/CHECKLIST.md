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
- [ ] Set up UV project for agent/
- [ ] Set up Next.js for frontend/
- [ ] Initial commit and push

## Phase 1: Onboarding Flow

### Backend (agent/)

- [ ] `agent/pyproject.toml` - UV project config
- [ ] `agent/state.py` - TypedDict state schemas
- [ ] `agent/tools/__init__.py`
- [ ] `agent/tools/onboarding.py` - 6 HITL tools
  - [ ] `confirm_role_preference`
  - [ ] `confirm_trinity`
  - [ ] `confirm_experience`
  - [ ] `confirm_location`
  - [ ] `confirm_search_prefs`
  - [ ] `complete_onboarding`
- [ ] `agent/agent.py` - create_deep_agent with subagents
- [ ] `agent/main.py` - FastAPI with AG-UI endpoint
- [ ] `agent/.env` - Environment variables
- [ ] Test agent locally (port 8123)

### Frontend (frontend/)

- [ ] `frontend/package.json` - Dependencies
- [ ] `frontend/src/app/layout.tsx` - CopilotKit provider
- [ ] `frontend/src/app/page.tsx` - Main UI
- [ ] `frontend/src/app/api/copilotkit/route.ts` - CopilotKit runtime
- [ ] `frontend/src/components/ChatPanel.tsx` - Chat with tool capture
- [ ] `frontend/src/components/OnboardingProgress.tsx` - Step indicator
- [ ] `frontend/src/components/ProfileCard.tsx` - Profile display
- [ ] `frontend/.env.local` - LANGGRAPH_DEPLOYMENT_URL
- [ ] Test frontend locally (port 3000)

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
