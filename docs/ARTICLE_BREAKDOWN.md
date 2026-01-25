# Article Breakdown: LangChain Deep Agents + CopilotKit

Reference: https://dev.to/copilotkit/how-to-build-a-frontend-for-langchain-deep-agents-with-copilotkit-52kd
Example Repo: https://github.com/CopilotKit/copilotkit-deepagents

---

## 1. Agent Setup (`create_deep_agent()`)

```python
from deepagents import create_deep_agent
from copilotkit import CopilotKitMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

def build_agent():
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)

    tools = [
        internet_search,
        update_jobs_list,
        finalize,
    ]

    subagents = [
        {
            "name": "job-search-agent",
            "description": "Finds relevant jobs",
            "system_prompt": JOB_SEARCH_PROMPT,
            "tools": [internet_search],
        },
    ]

    agent_graph = create_deep_agent(
        model=llm,
        system_prompt=MAIN_SYSTEM_PROMPT,
        tools=tools,
        subagents=subagents,
        middleware=[CopilotKitMiddleware()],  # KEY: Enables real-time sync
        checkpointer=MemorySaver(),
    )

    return agent_graph.with_config({"recursion_limit": 100})
```

**Key Points:**
- Use `create_deep_agent()` NOT manual StateGraph
- `CopilotKitMiddleware()` in middleware list
- Subagents defined as dicts with name/description/prompt/tools
- `MemorySaver()` for state persistence

---

## 2. Tool Definitions

```python
from langchain.tools import tool
from typing import List, Dict, Any

@tool
def update_jobs_list(jobs_json: str) -> Dict[str, Any]:
    """Send jobs list to UI state."""
    jobs = json.loads(jobs_json)
    return {"jobs_list": jobs}  # This becomes readable by frontend

@tool
def finalize() -> dict:
    """Signal completion."""
    return {"status": "done"}
```

**Key Points:**
- Use `@tool` decorator from `langchain.tools`
- Return `Dict[str, Any]` for state updates
- No Pydantic `args_schema` required (simpler approach)
- String JSON input for complex data structures

---

## 3. FastAPI Main.py

```python
from fastapi import FastAPI
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from agent import build_agent

app = FastAPI()

agent_graph = build_agent()

add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="fractional_quest",          # Must match frontend
        description="Career assistant",
        graph=agent_graph,
    ),
    path="/",                             # AG-UI endpoint at root
)

@app.get("/healthz")
async def health():
    return {"status": "healthy"}
```

**Key Points:**
- `add_langgraph_fastapi_endpoint()` handles AG-UI protocol
- Agent name must match frontend `agent` prop
- Path `/` for root endpoint
- Add health check for deployment monitoring

---

## 4. Frontend: CopilotKit Provider

```typescript
// app/layout.tsx
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <CopilotKit
          runtimeUrl="/api/copilotkit"
          agent="fractional_quest"  // Must match backend
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
```

---

## 5. Frontend: API Route

```typescript
// app/api/copilotkit/route.ts
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const runtime = new CopilotRuntime({
  agents: {
    fractional_quest: new LangGraphHttpAgent({
      url: process.env.LANGGRAPH_DEPLOYMENT_URL || "http://localhost:8123",
    }),
  },
});

export const POST = async (req) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
```

---

## 6. Frontend: Tool Capture Hook

```typescript
// components/ChatPanel.tsx
import { useDefaultTool, useCopilotReadable } from "@copilotkit/react-core";

export function ChatPanel() {
  const [onboarding, setOnboarding] = useState({});
  const processedKeyRef = useRef<string | null>(null);

  // Capture tool results
  useDefaultTool({
    render: ({ name, status, args, result }) => {
      // Update state when tool completes
      if (name === "confirm_role_preference" && status === "complete") {
        const key = JSON.stringify({ name, result });
        if (processedKeyRef.current !== key) {
          processedKeyRef.current = key;
          queueMicrotask(() => {
            setOnboarding(prev => ({ ...prev, role: result.role }));
          });
        }
      }

      return (
        <details className="tool-call">
          <summary>{status === "complete" ? `Called ${name}` : `Calling ${name}`}</summary>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </details>
      );
    },
  });

  // Make state readable to agent
  useCopilotReadable({
    description: "User onboarding progress",
    value: onboarding,
  });

  return <CopilotChat />;
}
```

**Key Points:**
- `useDefaultTool()` intercepts ALL tool calls
- Dedupe with `useRef` and JSON key
- `queueMicrotask()` for batched updates
- `useCopilotReadable()` syncs frontend → agent

---

## 7. Dependencies

**Backend (pyproject.toml):**
```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "copilotkit>=0.1.76",
    "deepagents>=0.3.5",
    "fastapi>=0.115.14",
    "langchain>=1.2.4",
    "langchain-google-genai>=4.2.0",
    "python-dotenv>=1.2.1",
    "uvicorn[standard]>=0.40.0",
]
```

**Frontend (package.json):**
```json
{
  "dependencies": {
    "@copilotkit/react-core": "^1.51.0",
    "@copilotkit/react-ui": "^1.51.0",
    "@copilotkit/runtime": "^1.51.0",
    "next": "^15.0.0",
    "react": "^19.0.0"
  }
}
```

---

## Adaptation for Fractional Quest

| Article Pattern | Our Adaptation |
|-----------------|----------------|
| Job search with Tavily | Onboarding flow (no search API) |
| `update_jobs_list` tool | `confirm_role_preference`, `confirm_trinity`, etc. |
| Resume upload | N/A (conversational) |
| Single search agent | Multiple subagents (onboarding, jobs, coaching) |
| GPT-4 | Gemini 2.0 Flash |

---

## Success Criteria

- [ ] Agent responds via CopilotChat
- [ ] Tool calls visible in `useDefaultTool()` render
- [ ] State syncs from tool results to UI
- [ ] `useCopilotReadable()` data accessible to agent
- [ ] Deploy: Railway (agent) + Vercel (frontend)
