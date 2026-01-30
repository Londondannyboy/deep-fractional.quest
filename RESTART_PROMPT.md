# Deep Fractional - Phase 4 Session Restart Plan

## Mission

Production-ready fractional executive career platform using CopilotKit + LangGraph Deep Agents (Christian Bromann's patterns) with voice interface.

## Current Status: Phase 4.1 In Progress (70% Complete)

**Assessment Score: 6/10** (up from 5/10 at session start)

**Live URLs:**
- Frontend: https://deep-fractional-web.vercel.app
- Agent: https://agent-production-ccb0.up.railway.app
- GitHub: https://github.com/Londondannyboy/deep-fractional.quest
- Neon Project: `sweet-hat-02969611`
- Neon SQL Editor: https://console.neon.tech/app/projects/sweet-hat-02969611/sql-editor

---

## Session Progress Summary (January 30, 2026)

### Completed This Session

| Item | Files Modified | Status |
|------|---------------|--------|
| Voice + User Identity | `VoiceInput.tsx`, `route.ts (CLM)`, `agent.py`, `state.py` | DONE |
| Google OAuth Fix | `providers.tsx` (new), `layout.tsx` | DONE |
| Voice to CopilotKit Sync | `VoiceInput.tsx` (msgId tracking) | DONE |
| Zep Context Integration | `api/zep-context/route.ts` (new) | DONE |
| HITL Countdown Timer | `HITLCard.tsx` (new), `page.tsx` | DONE |
| Profile Sidebar Visualization | `ProfileSidebar.tsx` (new), `page.tsx` | DONE |

### In Progress

| Item | Status | Notes |
|------|--------|-------|
| Summarization Middleware | STARTED | Research phase - custom implementation needed |

### Remaining Phase 4 Tasks

| Item | Priority | Estimated Complexity |
|------|----------|---------------------|
| Summarization Middleware | HIGH | Medium - Python middleware in agent.py |
| Tool Call Limit Middleware | HIGH | Low - Simple counter in middleware |
| Voice/Chat Context Sharing | MEDIUM | Medium - Sync thread IDs or Zep bridge |
| Voice HITL Announcements | LOW | Low - Audio cue when confirmation needed |
| Update Remaining HITL Hooks | LOW | Low - Replace inline with HITLCard |

---

## Architecture (Christian's CopilotKit Pattern)

```
                         FRONTEND (Vercel)
  +------------------+    +------------------+    +------------------+
  |   CopilotChat    |<---|   VoiceInput     |    |  NeonAuthUI      |
  |   (sidebar)      |    |   (Hume EVI)     |    |  (Google OAuth)  |
  |                  |    |                  |    |                  |
  | useHumanInTheLoop|    | appendMessage()  |    | useSession()     |
  | ProfileSidebar   |    | Zep context      |    |                  |
  | HITLCard         |    |                  |    |                  |
  +--------+---------+    +--------+---------+    +--------+---------+
           |                       |                       |
           v                       v                       v
  +------------------+    +------------------+              |
  | /api/copilotkit  |    | /api/hume-token  |              |
  | (AG-UI route)    |    | /api/zep-context |              |
  +--------+---------+    +------------------+              |
           |                                                |
           v                                                v
+-----------------------------------------------+   +------------------+
|        DeepAgents (Railway)                   |   | Neon PostgreSQL  |
|                                               |   |                  |
|  +----------------------------------------+  |   | user_profiles    |
|  |           ORCHESTRATOR                 |  |   | jobs             |
|  |   (routes to subagents)                |  |   | saved_jobs       |
|  |   user_id in state (top-level)         |  |   | coaches          |
|  +------------------+---------------------+  |   | coaching_sessions|
|                     |                        |   | checkpoint_*     |
|        +------------+------------+           |   | neon_auth.*      |
|        v            v            v           |   +------------------+
|   +--------+   +--------+   +----------+     |
|   |Onboard |   | Jobs   |   | Coaching |     |   +------------------+
|   | Agent  |   | Agent  |   |  Agent   |     |   |   Zep Cloud      |
|   +---+----+   +---+----+   +----+-----+     |   | (cross-session   |
|       |            |             |           |   |  memory/facts)   |
|       v            v             v           |   +------------------+
|    6 tools      6 tools       5 tools        |
|    + HITL       + HITL        + HITL         |   +------------------+
|                                              |   |  Hume EVI Cloud  |
|  CopilotKitMiddleware                        |<--| (voice interface)|
|  AsyncPostgresSaver (checkpointer)           |   +------------------+
|  Gemini 2.0 Flash                            |
+----------------------------------------------+
```

---

## Key Data Architecture Clarification

**Neon (Database) = Confirmed Data**
- `user_profiles` table stores HITL-confirmed preferences
- Data here is authoritative and persisted
- Example: User confirms "CTO" role via HITL -> saved to Neon

**Zep (Knowledge Graph) = Mentioned Facts**
- Stores facts/preferences mentioned in conversation
- Cross-session memory for context
- Example: User says "I'm interested in fintech" -> stored in Zep
- Used to enrich voice prompts and provide context

---

## New Components Created This Session

### 1. `frontend/src/components/HITLCard.tsx`
Reusable HITL confirmation card with:
- 15-second countdown timer
- Pause on hover
- Auto-cancel by default
- Multiple color schemes
- Children slot for custom content

```typescript
<HITLCard
  title="Confirm Role"
  description="Save CTO as your target role?"
  confirmLabel="Yes, confirm"
  cancelLabel="Not yet"
  onConfirm={() => resolve("confirmed")}
  onCancel={() => resolve("rejected")}
  countdownSeconds={15}
  autoAction="cancel"
  colorScheme="purple"
/>
```

### 2. `frontend/src/components/ProfileSidebar.tsx`
Shows confirmed database state with:
- Progress bar (completedSteps / 5)
- Visual status for each field (confirmed, current, pending)
- "DB checkmark" badge for confirmed fields
- User name and ID display

### 3. `frontend/src/components/providers.tsx`
Correct NeonAuthUIProvider configuration with Google OAuth:
```typescript
<NeonAuthUIProvider
  authClient={authClient as any}
  redirectTo="/"
  social={{ providers: ['google'] }}  // Key fix
>
```

### 4. `frontend/src/app/api/zep-context/route.ts`
Fetches user memory from Zep knowledge graph:
- Categorizes facts (role, location, skill, interest, experience)
- Returns structured context for voice prompts
- Uses `ZEP_GRAPH` env var (fractional-jobs-graph)

---

## Key Code Changes This Session

### Voice + User Identity Flow
```typescript
// frontend/src/app/api/chat/completions/route.ts
const rawUserId = sessionPart?.replace('deep_fractional_', '') || '';
const isAuthenticated = rawUserId && !rawUserId.startsWith('anon_');
const userId = isAuthenticated ? rawUserId : '';

// State now includes user_id at top level
state: {
  user_id: userId || null,
  user_name: firstName || null,
  // ... rest of state
}
```

### Voice Message Sync Fix
```typescript
// frontend/src/components/VoiceInput.tsx
// Changed from array index tracking to message ID tracking
const lastSentMsgId = useRef<string | null>(null);

const msgId = lastMsg?.id || `${conversationMsgs.length}-${lastMsg?.message?.content?.slice(0, 20)}`;
if (lastMsg?.message?.content && msgId !== lastSentMsgId.current) {
  lastSentMsgId.current = msgId;
  onMessage(lastMsg.message.content, isUser ? "user" : "assistant");
}
```

### Agent State Schema
```python
# agent/state.py
class AgentState(TypedDict, total=False):
    user_id: Optional[str]      # NEW - top level
    user_name: Optional[str]    # NEW - top level
    messages: List[BaseMessage]
    onboarding: OnboardingState
    # ... rest
```

---

## Next Steps for Fresh Session

### Immediate Priority: Summarization Middleware

**Goal:** 75% token reduction for long conversations

**Implementation Location:** `agent/agent.py`

**Approach:**
```python
# agent/middleware/summarization.py
class SummarizationMiddleware:
    def __init__(self, max_messages: int = 20, summary_threshold: int = 15):
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold

    async def __call__(self, state, config):
        messages = state.get("messages", [])
        if len(messages) > self.summary_threshold:
            # Summarize older messages
            to_summarize = messages[:-5]  # Keep last 5
            summary = await self._summarize(to_summarize, config)
            state["messages"] = [SystemMessage(content=f"Previous conversation summary: {summary}")] + messages[-5:]
        return state

    async def _summarize(self, messages, config):
        # Use LLM to create summary
        ...
```

### Then: Tool Call Limit Middleware

**Goal:** Prevent runaway costs from loops

```python
# agent/middleware/tool_limit.py
class ToolCallLimitMiddleware:
    def __init__(self, max_calls: int = 50):
        self.max_calls = max_calls
        self.call_count = 0

    async def __call__(self, state, config):
        self.call_count += 1
        if self.call_count > self.max_calls:
            raise MaxToolCallsExceeded(f"Exceeded {self.max_calls} tool calls")
        return state
```

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
ZEP_GRAPH=fractional-jobs-graph
```

### Railway (agent)
```bash
GOOGLE_API_KEY=<Gemini API key>
GOOGLE_MODEL=gemini-2.0-flash
DATABASE_URL=<Neon PostgreSQL connection string>
ZEP_API_KEY=<from Zep Cloud>
ZEP_GRAPH=fractional-jobs-graph
```

---

## Key File Reference

### New/Modified Files (This Session)

| File | Status | Purpose |
|------|--------|---------|
| `frontend/src/components/HITLCard.tsx` | NEW | Countdown timer HITL card |
| `frontend/src/components/ProfileSidebar.tsx` | NEW | Confirmed DB state display |
| `frontend/src/components/providers.tsx` | NEW | NeonAuthUIProvider with Google |
| `frontend/src/app/api/zep-context/route.ts` | NEW | Zep memory fetch endpoint |
| `frontend/src/components/VoiceInput.tsx` | MODIFIED | Zep context, msgId tracking |
| `frontend/src/app/api/chat/completions/route.ts` | MODIFIED | user_id extraction |
| `frontend/src/app/layout.tsx` | MODIFIED | Use Providers component |
| `frontend/src/app/page.tsx` | MODIFIED | HITLCard, ProfileSidebar |
| `agent/agent.py` | MODIFIED | User identity prompt section |
| `agent/state.py` | MODIFIED | user_id at top level |

### Core Files Reference

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
| `frontend/src/app/page.tsx` | ~700 | Main UI + HITL hooks + ProfileSidebar |
| `frontend/src/components/VoiceInput.tsx` | ~350 | Hume EVI component |

---

## Christian's Patterns Implementation Status

| Pattern | CopilotKit Reference | Status |
|---------|---------------------|--------|
| **Deep Agents** | `create_deep_agent()` | DONE |
| **HITL via interrupt_on** | `useHumanInTheLoop` | DONE (11 hooks) |
| **HITL Countdown Timer** | Custom | DONE (HITLCard) |
| **State Sync** | `useCopilotReadable` | DONE |
| **Profile Visualization** | Custom | DONE (ProfileSidebar) |
| **Zep Memory Integration** | Custom | DONE |
| **Summarization Middleware** | Custom | IN PROGRESS |
| **Tool Call Limit** | Custom | PENDING |
| **Agent State Render** | `useCoAgentStateRender` | PENDING |
| **Custom Interrupts** | `useLangGraphInterrupt` | PENDING |
| **Emit Intermediate State** | `copilotkitEmitState` | PENDING |
| **Selective Emission** | `copilotkitCustomizeConfig` | PENDING |

---

## Quick Commands

```bash
# Local development
cd agent && uv run python main.py          # Agent on :8123
cd frontend && npm run dev                  # Frontend on :3000

# Deploy
git add -A && git commit -m "message" && git push origin main

# Check Railway logs
railway logs -n 100

# Run Neon migration
# Open: https://console.neon.tech/app/projects/sweet-hat-02969611/sql-editor
```

---

## Git Commits This Session

```
33da6ff Add ProfileSidebar showing confirmed database state
8233b0c Add HITL countdown timer component
986356d Fix voice->CopilotKit message forwarding
8d059d4 Phase 4.1: Auth + Voice + User Identity
b153fb4 docs: comprehensive Phase 4 restart plan with Christian's patterns
```

---

## Session Restart Instructions

1. **Read this file first** - It contains all context from the previous session

2. **Check current todo list:**
   - Summarization Middleware (75% token reduction) - IN PROGRESS
   - Tool Call Limit Middleware - PENDING
   - Voice/Chat context sharing - PENDING
   - Voice HITL announcements - PENDING
   - Update remaining HITL hooks with HITLCard - PENDING

3. **Continue with Summarization Middleware:**
   - Create `agent/middleware/` directory
   - Implement `SummarizationMiddleware` class
   - Add to `create_deep_agent()` middleware list
   - Test with long conversations

4. **Reference the PRD:** `docs/PRD.md` for validation values and user journey

5. **Reference the Architecture:** `docs/ARCHITECTURE.md` for detailed system design

---

*Last updated: January 30, 2026 - Phase 4.1 at 70%*
