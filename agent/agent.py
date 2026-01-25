"""
Deep Agents graph for Fractional Quest.

Uses create_deep_agent with CopilotKitMiddleware for
real-time state sync with the frontend.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from deepagents import create_deep_agent
from copilotkit import CopilotKitMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.onboarding import ONBOARDING_TOOLS


# =============================================================================
# System Prompts
# =============================================================================

ORCHESTRATOR_PROMPT = """You are the main orchestrator for Fractional Quest, a platform helping fractional executives (CTO, CFO, CMO, etc.) find roles.

## Your Role
You route conversations to the appropriate specialist and maintain context. Be warm, professional, and helpful.

## Routing Rules

1. **Onboarding First**: If the user hasn't completed onboarding, guide them through the 6-step process:
   - Step 1: What C-level role are they seeking? → use confirm_role_preference
   - Step 2: Fractional, Interim, or Advisory preference? → use confirm_trinity
   - Step 3: Years of experience and industries? → use confirm_experience
   - Step 4: Location and remote preferences? → use confirm_location
   - Step 5: Compensation and availability? → use confirm_search_prefs
   - Step 6: Complete onboarding → use complete_onboarding

2. **After Onboarding**:
   - Job questions → delegate to job-search-agent
   - Coaching questions → delegate to coaching-agent
   - General questions → answer directly

## Important Behavior

When a user first says hello:
- Warmly greet them
- Briefly explain Fractional Quest helps fractional executives find roles
- Ask what type of C-level role they're looking for (to start onboarding)

When the user provides information, use the appropriate tool to confirm it.

## Tone
- Professional but warm
- Concise but thorough
- Encouraging and supportive

Always acknowledge what you know about the user rather than re-asking.
"""

ONBOARDING_PROMPT = """You are the onboarding specialist for Fractional Quest.

Your job is to guide users through building their profile in 6 steps:
1. Role preference (CTO, CFO, CMO, COO, CPO)
2. Engagement type (Fractional, Interim, Advisory)
3. Experience (years and industries)
4. Location and remote preferences
5. Compensation and availability
6. Complete onboarding

Use the appropriate tool for each step. Be conversational and helpful.
Extract information naturally from the conversation.
"""

JOB_SEARCH_PROMPT = """You are the job search specialist for Fractional Quest.

Help users find relevant job opportunities based on their profile.
Use search_jobs to find matches, match_jobs to score them, and save_job for saves.
"""

COACHING_PROMPT = """You are the coaching specialist for Fractional Quest.

Help users connect with executive coaches.
Use find_coaches to discover matches and schedule_session to book.
"""


# =============================================================================
# Agent Builder
# =============================================================================

def build_agent():
    """Build the Deep Agents graph with CopilotKit middleware."""

    # Get API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set")

    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=os.environ.get("GOOGLE_MODEL", "gemini-2.0-flash"),
        temperature=0.7,
        google_api_key=api_key,
    )

    # Define tools available to orchestrator
    tools = ONBOARDING_TOOLS

    # Define subagents
    subagents = [
        {
            "name": "onboarding-agent",
            "description": "Guides users through the 6-step profile building process",
            "system_prompt": ONBOARDING_PROMPT,
            "tools": ONBOARDING_TOOLS,
        },
        # Phase 2: Add job-search-agent
        # Phase 3: Add coaching-agent
    ]

    # Define tools that require HITL confirmation
    # Users should confirm before their profile data is saved
    interrupt_on = {
        "confirm_role_preference": True,
        "confirm_trinity": True,
        "confirm_experience": True,
        "confirm_location": True,
        "confirm_search_prefs": True,
        "complete_onboarding": True,
    }

    # Create the Deep Agents graph
    agent_graph = create_deep_agent(
        model=llm,
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=tools,
        subagents=subagents,
        middleware=[CopilotKitMiddleware()],
        checkpointer=MemorySaver(),
        interrupt_on=interrupt_on,  # HITL: pause for user confirmation
    )

    print("[AGENT] Deep Agents graph created")
    print(f"[AGENT] Tools: {[t.name for t in tools]}")
    print(f"[AGENT] Subagents: {[s['name'] for s in subagents]}")

    return agent_graph.with_config({"recursion_limit": 100})


# For direct import
if __name__ == "__main__":
    graph = build_agent()
    print(graph)
