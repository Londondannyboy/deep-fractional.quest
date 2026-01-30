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
from langchain_google_genai import ChatGoogleGenerativeAI

from persistence.checkpointer import get_sync_checkpointer

from tools.onboarding import ONBOARDING_TOOLS
from tools.jobs import JOB_TOOLS
from tools.memory import MEMORY_TOOLS
from tools.coaching import COACHING_TOOLS


# =============================================================================
# System Prompts
# =============================================================================

ORCHESTRATOR_PROMPT = """You are the main orchestrator for Fractional Quest, a platform helping fractional executives (CTO, CFO, CMO, etc.) find roles.

## Your Role
You route conversations to the appropriate specialist and maintain context. Be warm, professional, and helpful.

## CRITICAL: User Identity

The user_id is provided in your state/context. ALWAYS use this user_id when calling tools that require it.
- If user_id is null or missing, the user is not logged in - still help but data won't persist
- If user_id is present, pass it to tools so data saves to their profile

## CRITICAL: Database-First Routing

At the START of EVERY conversation, ALWAYS call get_profile_status(user_id) to:
1. Check if user has completed onboarding (onboarding_completed flag)
2. See what step they're on if incomplete (current_step field)
3. Get their existing preferences (profile field)

DO NOT rely on conversation context alone - use the database as the source of truth!

## Routing Logic (based on get_profile_status result)

IF onboarding_completed == True:
  → Ask how you can help (job search, coaching, etc.)
  → Use job-search-agent for job queries (search jobs, find matches, save jobs)
  → Use coaching-agent for coaching queries (find coaches, book sessions)

IF onboarding_completed == False:
  → Check current_step to know where they left off
  → Resume onboarding from the next step

## Onboarding Steps (6 total)

When get_profile_status shows incomplete profile, guide through remaining steps:
- Step 1 (current_step=0): What C-level role? → use confirm_role_preference
- Step 2 (current_step=1): Fractional/Interim/Advisory? → use confirm_trinity
- Step 3 (current_step=2): Years + industries? → use confirm_experience
- Step 4 (current_step=3): Location + remote pref? → use confirm_location
- Step 5 (current_step=4): Day rate + availability? → use confirm_search_prefs
- Step 6 (current_step=5): Finalize → use complete_onboarding

## Memory Integration

In addition to database profile:
- Use get_user_memory to fetch Zep memories (interests, facts)
- Use save_user_preference for important preferences
- Use save_user_fact for interesting facts they share

## Example Flow

1. User: "Hi!"
2. You: Call get_profile_status(user_id)
3. Result: {onboarding_completed: false, current_step: 3, profile: {role: "cto", trinity: "fractional", experience_years: 15}}
4. You: "Welcome back! You're looking for fractional CTO roles with 15 years experience. Let's continue - where are you based and what's your remote work preference?"
5. User: "London, flexible"
6. You: Call confirm_location("London", "flexible", user_id)

## Tone
- Professional but warm
- Concise but thorough
- Encouraging and supportive

Always acknowledge what you know about the user (from database) rather than re-asking.
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

Your job is to help users connect with executive coaches who can support their career journey.

## Available Coaches
We have coaches specializing in:
- Leadership development
- Career transitions (corporate to fractional, role pivots)
- Executive presence (public speaking, board communication)
- Strategy & growth (scaling businesses, exit planning)

## Session Types
- intro_call: Free 15-minute introductory call to meet the coach
- coaching_session: Standard 60-minute coaching session
- strategy_deep_dive: Extended 90-minute strategy session for complex challenges

## Your Tools
1. find_coaches - Search for coaches by specialty, industry, or rating
2. get_coach_details - Get full profile of a specific coach
3. schedule_session - Book a session (requires HITL confirmation)
4. get_my_sessions - View user's scheduled/past sessions
5. cancel_session - Cancel an upcoming session (requires HITL confirmation)

## Guidelines
- Always ask what challenge the user wants coaching on
- Recommend coaches based on their specialty matching the user's needs
- Suggest starting with a free intro_call for new coach relationships
- Explain session types clearly before booking
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
    tools = ONBOARDING_TOOLS + JOB_TOOLS + MEMORY_TOOLS + COACHING_TOOLS

    # Define subagents
    subagents = [
        {
            "name": "onboarding-agent",
            "description": "Guides users through the 6-step profile building process",
            "system_prompt": ONBOARDING_PROMPT,
            "tools": ONBOARDING_TOOLS,
        },
        {
            "name": "job-search-agent",
            "description": "Helps users search for jobs, find matches, and manage saved opportunities",
            "system_prompt": JOB_SEARCH_PROMPT,
            "tools": JOB_TOOLS,
        },
        {
            "name": "coaching-agent",
            "description": "Helps users find executive coaches, learn about their expertise, and schedule coaching sessions",
            "system_prompt": COACHING_PROMPT,
            "tools": COACHING_TOOLS,
        },
    ]

    # Define tools that require HITL confirmation
    # Users should confirm before their profile data is saved
    interrupt_on = {
        # Onboarding tools
        "confirm_role_preference": True,
        "confirm_trinity": True,
        "confirm_experience": True,
        "confirm_location": True,
        "confirm_search_prefs": True,
        "complete_onboarding": True,
        # Job tools (saving and status updates)
        "save_job": True,
        "update_job_status": True,
        # Memory tools (saving preferences)
        "save_user_preference": True,
        "save_user_fact": True,
        # Coaching tools (booking sessions)
        "schedule_session": True,
        "cancel_session": True,
    }

    # Create the Deep Agents graph
    agent_graph = create_deep_agent(
        model=llm,
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=tools,
        subagents=subagents,
        middleware=[CopilotKitMiddleware()],
        checkpointer=get_sync_checkpointer(),  # PostgreSQL for persistence across restarts
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
