"""
Coaching tools for connecting users with executive coaches.

Provides find_coaches, get_coach_details, and schedule_session functionality.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import tool

from persistence.neon import get_neon_client


# =============================================================================
# Input Schemas
# =============================================================================

class FindCoachesInput(BaseModel):
    """Input for finding coaches."""
    specialty: Optional[str] = Field(
        default=None,
        description="Coach specialty (leadership, career_transition, executive_presence, strategy, etc.)"
    )
    industry: Optional[str] = Field(
        default=None,
        description="Industry expertise (tech, finance, healthcare, retail, etc.)"
    )
    min_rating: Optional[float] = Field(
        default=None,
        description="Minimum rating (1.0-5.0)"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of coaches to return"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalized recommendations"
    )


class GetCoachInput(BaseModel):
    """Input for getting coach details."""
    coach_id: str = Field(description="The coach's unique identifier")


class ScheduleSessionInput(BaseModel):
    """Input for scheduling a coaching session."""
    coach_id: str = Field(description="The coach's unique identifier")
    session_type: str = Field(
        description="Type of session: intro_call (free 15min), coaching_session (60min), strategy_deep_dive (90min)"
    )
    preferred_date: Optional[str] = Field(
        default=None,
        description="Preferred date in ISO format (YYYY-MM-DD)"
    )
    preferred_time: Optional[str] = Field(
        default=None,
        description="Preferred time slot (morning, afternoon, evening)"
    )
    topic: Optional[str] = Field(
        default=None,
        description="Topic or challenge to discuss"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for booking"
    )


class GetSessionsInput(BaseModel):
    """Input for getting user's sessions."""
    user_id: str = Field(description="User ID")
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: scheduled, completed, cancelled"
    )


class CancelSessionInput(BaseModel):
    """Input for cancelling a session."""
    session_id: str = Field(description="Session ID to cancel")
    user_id: str = Field(description="User ID for verification")
    reason: Optional[str] = Field(
        default=None,
        description="Cancellation reason"
    )


# =============================================================================
# Tools
# =============================================================================

@tool(args_schema=FindCoachesInput)
async def find_coaches(
    specialty: Optional[str] = None,
    industry: Optional[str] = None,
    min_rating: Optional[float] = None,
    limit: int = 5,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Find executive coaches based on specialty, industry, and rating.

    Returns a list of coaches matching the criteria, ordered by rating
    and relevance. Use this when users want to explore coaching options.
    """
    try:
        client = get_neon_client()
        coaches = await client.search_coaches(
            specialty=specialty,
            industry=industry,
            min_rating=min_rating,
            limit=limit,
        )

        if not coaches:
            return {
                "success": True,
                "coaches": [],
                "message": "No coaches found matching your criteria. Try broadening your search.",
                "suggestions": [
                    "Try removing the specialty filter",
                    "Consider coaches from related industries",
                    "Lower the minimum rating requirement"
                ]
            }

        return {
            "success": True,
            "coaches": coaches,
            "count": len(coaches),
            "message": f"Found {len(coaches)} coach(es) matching your criteria"
        }

    except Exception as e:
        print(f"[COACHING] Error finding coaches: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to search coaches. Please try again."
        }


@tool(args_schema=GetCoachInput)
async def get_coach_details(coach_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific coach.

    Returns full coach profile including bio, credentials, availability,
    and session pricing. Use this when users want to learn more about
    a specific coach before booking.
    """
    try:
        client = get_neon_client()
        coach = await client.get_coach(coach_id)

        if not coach:
            return {
                "success": False,
                "error": "Coach not found",
                "message": f"No coach found with ID {coach_id}"
            }

        return {
            "success": True,
            "coach": coach,
            "message": f"Details for {coach.get('name', 'coach')}"
        }

    except Exception as e:
        print(f"[COACHING] Error getting coach {coach_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to get coach details. Please try again."
        }


@tool(args_schema=ScheduleSessionInput)
async def schedule_session(
    coach_id: str,
    session_type: str,
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
    topic: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Schedule a coaching session with a coach.

    Session types:
    - intro_call: Free 15-minute introductory call
    - coaching_session: Standard 60-minute coaching session
    - strategy_deep_dive: Extended 90-minute strategy session

    HITL: Requires user confirmation before booking.
    """
    if not user_id:
        return {
            "success": False,
            "error": "Not authenticated",
            "message": "Please sign in to schedule a coaching session."
        }

    try:
        client = get_neon_client()

        # Get coach info for confirmation
        coach = await client.get_coach(coach_id)
        if not coach:
            return {
                "success": False,
                "error": "Coach not found",
                "message": f"No coach found with ID {coach_id}"
            }

        # Create session
        session = await client.create_coaching_session(
            user_id=user_id,
            coach_id=coach_id,
            session_type=session_type,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            topic=topic,
        )

        if not session:
            return {
                "success": False,
                "error": "Booking failed",
                "message": "Unable to create session. Please try again."
            }

        return {
            "success": True,
            "session": session,
            "coach_name": coach.get("name"),
            "session_type": session_type,
            "message": f"Session request submitted with {coach.get('name')}! They will confirm your preferred time shortly."
        }

    except Exception as e:
        print(f"[COACHING] Error scheduling session: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to schedule session. Please try again."
        }


@tool(args_schema=GetSessionsInput)
async def get_my_sessions(
    user_id: str,
    status: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get user's coaching sessions.

    Returns all scheduled, completed, and cancelled sessions.
    Filter by status to see only specific session types.
    """
    try:
        client = get_neon_client()
        sessions = await client.get_user_sessions(
            user_id=user_id,
            status=status,
        )

        if not sessions:
            return {
                "success": True,
                "sessions": [],
                "message": "You don't have any coaching sessions yet. Would you like to find a coach?"
            }

        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
            "message": f"Found {len(sessions)} session(s)"
        }

    except Exception as e:
        print(f"[COACHING] Error getting sessions: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to retrieve sessions. Please try again."
        }


@tool(args_schema=CancelSessionInput)
async def cancel_session(
    session_id: str,
    user_id: str,
    reason: Optional[str] = None,
) -> dict[str, Any]:
    """
    Cancel a scheduled coaching session.

    HITL: Requires user confirmation before cancelling.
    Note: Cancellations within 24 hours may incur fees.
    """
    try:
        client = get_neon_client()
        result = await client.cancel_coaching_session(
            session_id=session_id,
            user_id=user_id,
            reason=reason,
        )

        if not result:
            return {
                "success": False,
                "error": "Cancellation failed",
                "message": "Unable to cancel session. It may already be cancelled or completed."
            }

        return {
            "success": True,
            "session_id": session_id,
            "message": "Session cancelled successfully."
        }

    except Exception as e:
        print(f"[COACHING] Error cancelling session: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Unable to cancel session. Please try again."
        }


# =============================================================================
# Export
# =============================================================================

COACHING_TOOLS = [
    find_coaches,
    get_coach_details,
    schedule_session,
    get_my_sessions,
    cancel_session,
]
