# Implementation Checklist

## Phase 0: Setup - COMPLETE

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

## Phase 1: Onboarding Flow - COMPLETE

### Backend (agent/)

- [x] `agent/pyproject.toml` - UV project config
- [x] `agent/state.py` - TypedDict state schemas
- [x] `agent/tools/__init__.py`
- [x] `agent/tools/onboarding.py` - 6 tools with Pydantic schemas
  - [x] `confirm_role_preference` (with RolePreferenceInput)
  - [x] `confirm_trinity` (with TrinityInput)
  - [x] `confirm_experience` (with ExperienceInput)
  - [x] `confirm_location` (with LocationInput)
  - [x] `confirm_search_prefs` (with SearchPrefsInput)
  - [x] `complete_onboarding`
- [x] `agent/agent.py` - create_deep_agent with subagents
- [x] `agent/main.py` - FastAPI with AG-UI endpoint
- [x] `agent/.env` - Environment variables
- [x] Test agent locally (port 8123)
- [x] Deploy to Railway

### Frontend (frontend/)

- [x] `frontend/package.json` - Dependencies
- [x] `frontend/src/app/layout.tsx` - CopilotKit provider
- [x] `frontend/src/app/page.tsx` - Main UI with useDefaultTool
- [x] `frontend/src/app/api/copilotkit/route.ts` - CopilotKit runtime
- [x] `frontend/.env.local` - LANGGRAPH_DEPLOYMENT_URL
- [x] Test frontend locally (port 3000)
- [x] Deploy to Vercel

### Integration - COMPLETE

- [x] Frontend connects to backend
- [x] Tool calls visible in chat
- [x] State syncs from tools to UI
- [x] Onboarding progress updates
- [x] Full onboarding flow tested in production

## Phase 2: Production Features - IN PROGRESS

### 2.1 Pydantic Schemas - COMPLETE

- [x] Add Pydantic BaseModel for each tool input
- [x] Add args_schema to all @tool decorators
- [x] Add field_validator for normalization
- [x] Deploy to Railway

### 2.2 HITL Confirmation - IN PROGRESS

- [x] Add `interrupt_on` dict to create_deep_agent (maps tool names to interrupts)
- [x] Update frontend with useHumanInTheLoop for all 6 onboarding tools
- [x] Test HITL flow locally (both services build and start)
- [ ] Deploy HITL to production

### 2.3 Neon Persistence - PENDING

- [ ] Create `agent/persistence/neon.py`
- [ ] Create database schema (user_profile_items table)
- [ ] Update tools to call persistence layer
- [ ] Test persistence locally
- [ ] Deploy to production

### 2.4 Neon Auth - PENDING

- [ ] Provision Neon Auth via MCP
- [ ] Add auth client to frontend
- [ ] Pass userId to agent via useCopilotReadable
- [ ] Test authenticated flow
- [ ] Deploy to production

### 2.5 Job Search Agent - PENDING

- [ ] Create `agent/tools/jobs.py`
  - [ ] `search_jobs` tool
  - [ ] `match_jobs` tool
  - [ ] `save_job` tool
- [ ] Add job-search-agent to subagents
- [ ] Create jobs table in Neon
- [ ] Test job search flow

### 2.6 Coaching Agent - PENDING

- [ ] Create `agent/tools/coaching.py`
  - [ ] `find_coaches` tool
  - [ ] `schedule_session` tool
- [ ] Add coaching-agent to subagents
- [ ] Test coaching flow

## Verification Tests

- [x] Agent responds to greeting
- [x] Onboarding routes to onboarding-agent
- [x] Each tool updates state correctly
- [x] State syncs to frontend
- [x] Tool results render in chat
- [x] Onboarding completion works
- [x] Production deployment works
- [ ] HITL confirmation flow works
- [ ] Persistence saves to Neon
- [ ] Auth identifies users
