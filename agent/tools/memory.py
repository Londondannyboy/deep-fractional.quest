"""
Zep Cloud memory tools for Fractional Quest.
Handles cross-session user memory and profile persistence.
"""

import os
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

try:
    from zep_cloud.client import AsyncZep
    ZEP_AVAILABLE = True
except ImportError:
    ZEP_AVAILABLE = False
    print("Warning: zep-cloud not installed. Memory features disabled.")


# Zep client (initialized on first use)
_zep_client: Optional["AsyncZep"] = None


async def get_zep_client() -> Optional["AsyncZep"]:
    """Get or create the Zep client."""
    global _zep_client
    if not ZEP_AVAILABLE:
        return None

    if _zep_client is None:
        api_key = os.getenv("ZEP_API_KEY")
        if not api_key:
            print("Warning: ZEP_API_KEY not set. Memory features disabled.")
            return None
        _zep_client = AsyncZep(api_key=api_key)

    return _zep_client


# =============================================================================
# Pydantic Schemas for Tool Inputs
# =============================================================================

class GetMemoryInput(BaseModel):
    """Input schema for get_user_memory tool."""
    user_id: str = Field(description="The user's unique identifier")


class SavePreferenceInput(BaseModel):
    """Input schema for save_user_preference tool."""
    user_id: str = Field(description="The user's unique identifier")
    preference_type: str = Field(
        description="Type of preference: role_type, engagement_type, location, industry, day_rate, availability"
    )
    value: str = Field(description="The preference value to save")


class SaveFactInput(BaseModel):
    """Input schema for save_user_fact tool."""
    user_id: str = Field(description="The user's unique identifier")
    fact: str = Field(description="A fact about the user to remember")


# =============================================================================
# Memory Tools
# =============================================================================

@tool(args_schema=GetMemoryInput)
async def get_user_memory(user_id: str) -> Dict[str, Any]:
    """Get the user's memory including preferences, experience, and facts.

    Args:
        user_id: The user's unique identifier

    Returns:
        User memory containing preferences, experience, and context
    """
    client = await get_zep_client()
    if not client:
        return {
            "user_id": user_id,
            "preferences": {},
            "facts": [],
            "is_returning": False,
            "onboarding_hints": [],
        }

    try:
        # Get user node from Zep graph
        user = await client.user.get(user_id)

        # Extract facts and preferences
        facts = []
        preferences = {
            "role_type": None,
            "engagement_type": None,
            "location": None,
            "industries": [],
            "experience_years": None,
            "day_rate_range": None,
            "availability": None,
        }
        onboarding_hints = []

        if user and hasattr(user, 'facts'):
            for fact in user.facts[:20]:  # Limit to 20 facts
                fact_text = fact.fact if hasattr(fact, 'fact') else str(fact)
                facts.append(fact_text)

                # Parse preferences from facts
                fact_lower = fact_text.lower()

                # Role preferences
                if "cto" in fact_lower or "cfo" in fact_lower or "cmo" in fact_lower or "coo" in fact_lower or "cpo" in fact_lower:
                    for role in ["cto", "cfo", "cmo", "coo", "cpo"]:
                        if role in fact_lower:
                            preferences["role_type"] = role.upper()
                            break

                # Engagement type
                if "fractional" in fact_lower:
                    preferences["engagement_type"] = "fractional"
                elif "interim" in fact_lower:
                    preferences["engagement_type"] = "interim"
                elif "advisory" in fact_lower:
                    preferences["engagement_type"] = "advisory"

                # Location
                if "based in" in fact_lower or "located in" in fact_lower or "lives in" in fact_lower:
                    # Extract location after the keyword
                    for keyword in ["based in", "located in", "lives in"]:
                        if keyword in fact_lower:
                            location = fact_text.split(keyword)[-1].strip().rstrip(".")
                            preferences["location"] = location
                            break

                # Experience
                if "years" in fact_lower and "experience" in fact_lower:
                    import re
                    years_match = re.search(r'(\d+)\s*years', fact_lower)
                    if years_match:
                        preferences["experience_years"] = int(years_match.group(1))

                # Industries
                if "industry" in fact_lower or "industries" in fact_lower or "sector" in fact_lower:
                    # Add to industries list
                    for industry in ["tech", "finance", "healthcare", "retail", "manufacturing", "saas", "fintech"]:
                        if industry in fact_lower:
                            if industry not in [i.lower() for i in preferences["industries"]]:
                                preferences["industries"].append(industry.capitalize())

        # Determine what onboarding info is missing
        if not preferences["role_type"]:
            onboarding_hints.append("Ask about their target C-level role (CTO, CFO, CMO, etc.)")
        if not preferences["engagement_type"]:
            onboarding_hints.append("Ask about fractional, interim, or advisory preference")
        if not preferences["location"]:
            onboarding_hints.append("Ask about their location and remote work preferences")
        if not preferences["experience_years"]:
            onboarding_hints.append("Ask about their years of executive experience")
        if not preferences["industries"]:
            onboarding_hints.append("Ask about their industry experience and preferences")

        return {
            "user_id": user_id,
            "preferences": preferences,
            "facts": facts,
            "is_returning": len(facts) > 0,
            "onboarding_hints": onboarding_hints,
        }

    except Exception as e:
        print(f"Error getting user memory: {e}")
        return {
            "user_id": user_id,
            "preferences": {},
            "facts": [],
            "is_returning": False,
            "onboarding_hints": ["Start fresh onboarding conversation"],
        }


@tool(args_schema=SavePreferenceInput)
async def save_user_preference(user_id: str, preference_type: str, value: str) -> Dict[str, Any]:
    """Save a user preference to memory for cross-session persistence.

    Args:
        user_id: The user's unique identifier
        preference_type: Type of preference (role_type, engagement_type, location, industry, day_rate, availability)
        value: The preference value to save

    Returns:
        Confirmation of saved preference
    """
    client = await get_zep_client()
    if not client:
        return {"success": False, "message": "Zep not configured"}

    try:
        # Format fact based on preference type
        fact_templates = {
            "role_type": f"User is seeking a {value} role.",
            "engagement_type": f"User prefers {value} engagement.",
            "location": f"User is based in {value}.",
            "industry": f"User has experience in the {value} industry.",
            "day_rate": f"User's target day rate is {value}.",
            "availability": f"User is available {value}.",
            "experience_years": f"User has {value} years of executive experience.",
            "remote_preference": f"User prefers {value} work arrangement.",
        }

        fact_text = fact_templates.get(preference_type, f"User's {preference_type} is {value}.")

        # Ensure user exists in Zep
        try:
            await client.user.add(user_id=user_id)
        except Exception:
            pass  # User may already exist

        # Add fact to user's graph
        await client.graph.add(
            user_id=user_id,
            type="text",
            data=fact_text
        )

        return {
            "success": True,
            "message": f"Saved {preference_type}: {value}",
            "user_id": user_id,
            "preference_type": preference_type,
            "value": value,
        }

    except Exception as e:
        print(f"Error saving user preference: {e}")
        return {"success": False, "message": str(e)}


@tool(args_schema=SaveFactInput)
async def save_user_fact(user_id: str, fact: str) -> Dict[str, Any]:
    """Save a general fact about the user to memory.

    Args:
        user_id: The user's unique identifier
        fact: A fact about the user to remember (e.g., "User mentioned they enjoy golf")

    Returns:
        Confirmation of saved fact
    """
    client = await get_zep_client()
    if not client:
        return {"success": False, "message": "Zep not configured"}

    try:
        # Ensure user exists in Zep
        try:
            await client.user.add(user_id=user_id)
        except Exception:
            pass  # User may already exist

        # Add fact to user's graph
        await client.graph.add(
            user_id=user_id,
            type="text",
            data=fact
        )

        return {
            "success": True,
            "message": f"Saved fact: {fact[:50]}...",
            "user_id": user_id,
        }

    except Exception as e:
        print(f"Error saving user fact: {e}")
        return {"success": False, "message": str(e)}


# =============================================================================
# Internal Functions (not tools)
# =============================================================================

async def store_conversation_turn(
    user_id: str,
    session_id: str,
    role: str,
    content: str
) -> bool:
    """Store a conversation turn in Zep (not a tool, called internally).

    Args:
        user_id: The user's unique identifier
        session_id: The session/thread identifier
        role: Message role (user or assistant)
        content: Message content

    Returns:
        True if successful, False otherwise
    """
    client = await get_zep_client()
    if not client:
        return False

    try:
        await client.memory.add(
            session_id=session_id,
            messages=[{
                "role": role,
                "content": content,
                "role_type": "user" if role == "user" else "assistant",
            }]
        )
        return True
    except Exception as e:
        print(f"Error storing conversation turn: {e}")
        return False


# Export tools list for easy import
MEMORY_TOOLS = [get_user_memory, save_user_preference, save_user_fact]
