"""
Job search tools for Fractional Quest.

Provides tools for searching, matching, and saving job opportunities.
Uses Pydantic schemas for input validation (args_schema).
Persists to Neon PostgreSQL when user_id is provided.
"""

import asyncio
from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
import json


# Persistence helper (lazy import to avoid startup issues)
_neon_client = None


def _get_neon_client():
    """Lazy load Neon client to avoid import errors if not configured."""
    global _neon_client
    if _neon_client is None:
        try:
            from persistence.neon import get_neon_client
            _neon_client = get_neon_client()
        except Exception as e:
            print(f"[JOBS] Neon client not available: {e}")
            return None
    return _neon_client


def _run_async(coro):
    """Run async coroutine and return result."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create a new task and return a placeholder
            # In production, this would need proper async handling
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=10)
        else:
            return loop.run_until_complete(coro)
    except Exception as e:
        print(f"[JOBS] Async error: {e}")
        return None


# Valid values for validation
VALID_ROLES = ["cto", "cfo", "cmo", "coo", "cpo", "other"]
VALID_ENGAGEMENT = ["fractional", "interim", "advisory", "open"]
VALID_REMOTE = ["remote", "hybrid", "onsite", "flexible"]
VALID_SAVE_STATUS = ["saved", "applied", "interviewing", "rejected", "accepted"]


# =============================================================================
# Pydantic Input Schemas
# =============================================================================

class SearchJobsInput(BaseModel):
    """Input schema for search_jobs tool."""
    role_type: Optional[str] = Field(
        default=None,
        description="C-level role type to search for: cto, cfo, cmo, coo, cpo"
    )
    engagement_type: Optional[str] = Field(
        default=None,
        description="Engagement type: fractional, interim, advisory"
    )
    location: Optional[str] = Field(
        default=None,
        description="Location to search in (city or 'Remote')"
    )
    remote_preference: Optional[str] = Field(
        default=None,
        description="Remote work preference: remote, hybrid, onsite, flexible"
    )
    min_day_rate: Optional[int] = Field(
        default=None,
        description="Minimum day rate in GBP"
    )
    max_day_rate: Optional[int] = Field(
        default=None,
        description="Maximum day rate in GBP"
    )
    industries: Optional[str] = Field(
        default=None,
        description="Comma-separated list of industries to filter by"
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results to return",
        ge=1,
        le=50
    )

    @field_validator("role_type")
    @classmethod
    def normalize_role(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.lower().strip()
        return v

    @field_validator("engagement_type")
    @classmethod
    def normalize_engagement(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.lower().strip()
        return v


class MatchJobsInput(BaseModel):
    """Input schema for match_jobs tool."""
    user_id: str = Field(
        description="User ID to match jobs against their profile"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of matched jobs to return",
        ge=1,
        le=20
    )


class SaveJobInput(BaseModel):
    """Input schema for save_job tool."""
    user_id: str = Field(
        description="User ID saving the job"
    )
    job_id: str = Field(
        description="UUID of the job to save"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes about the job"
    )


class GetSavedJobsInput(BaseModel):
    """Input schema for get_saved_jobs tool."""
    user_id: str = Field(
        description="User ID to get saved jobs for"
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: saved, applied, interviewing, rejected, accepted"
    )

    @field_validator("status")
    @classmethod
    def normalize_status(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.lower().strip()
        return v


class UpdateJobStatusInput(BaseModel):
    """Input schema for update_job_status tool."""
    user_id: str = Field(
        description="User ID who saved the job"
    )
    job_id: str = Field(
        description="UUID of the saved job"
    )
    status: str = Field(
        description="New status: saved, applied, interviewing, rejected, accepted"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes to add/update"
    )

    @field_validator("status")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        return v.lower().strip()


class GetJobDetailsInput(BaseModel):
    """Input schema for get_job_details tool."""
    job_id: str = Field(
        description="UUID of the job to get details for"
    )


# =============================================================================
# Tools with Pydantic Schemas
# =============================================================================

@tool(args_schema=SearchJobsInput)
def search_jobs(
    role_type: Optional[str] = None,
    engagement_type: Optional[str] = None,
    location: Optional[str] = None,
    remote_preference: Optional[str] = None,
    min_day_rate: Optional[int] = None,
    max_day_rate: Optional[int] = None,
    industries: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search for job opportunities based on filters.

    Args:
        role_type: C-level role type (cto, cfo, cmo, coo, cpo)
        engagement_type: Engagement type (fractional, interim, advisory)
        location: City or "Remote"
        remote_preference: Remote preference (remote, hybrid, onsite, flexible)
        min_day_rate: Minimum day rate in GBP
        max_day_rate: Maximum day rate in GBP
        industries: Comma-separated industries
        limit: Max results (default 10)

    Returns:
        List of matching jobs
    """
    # Parse industries
    industry_list = None
    if industries:
        industry_list = [i.strip() for i in industries.split(",") if i.strip()]

    client = _get_neon_client()
    if not client:
        return {
            "success": False,
            "error": "Database not available",
            "jobs": []
        }

    # Run async search
    jobs = _run_async(client.search_jobs(
        role_type=role_type,
        engagement_type=engagement_type,
        location=location,
        remote_preference=remote_preference,
        min_day_rate=min_day_rate,
        max_day_rate=max_day_rate,
        industries=industry_list,
        limit=limit
    ))

    if jobs is None:
        jobs = []

    return {
        "success": True,
        "count": len(jobs),
        "jobs": jobs,
        "filters_applied": {
            "role_type": role_type,
            "engagement_type": engagement_type,
            "location": location,
            "remote_preference": remote_preference,
            "min_day_rate": min_day_rate,
            "max_day_rate": max_day_rate,
            "industries": industry_list
        },
        "message": f"Found {len(jobs)} matching opportunities."
    }


@tool(args_schema=MatchJobsInput)
def match_jobs(user_id: str, limit: int = 5) -> Dict[str, Any]:
    """
    Find jobs that match a user's profile.

    Args:
        user_id: User ID to match against
        limit: Max results (default 5)

    Returns:
        List of matched jobs with match scores
    """
    client = _get_neon_client()
    if not client:
        return {
            "success": False,
            "error": "Database not available",
            "jobs": []
        }

    # Get user profile first
    profile = _run_async(client.get_profile(user_id))
    if not profile:
        return {
            "success": False,
            "error": "User profile not found. Please complete onboarding first.",
            "jobs": []
        }

    # Find matching jobs based on profile
    matches = _run_async(client.match_jobs_to_profile(user_id, limit))
    if matches is None:
        matches = []

    return {
        "success": True,
        "count": len(matches),
        "jobs": matches,
        "profile_summary": {
            "role": profile.get("role_preference"),
            "engagement": profile.get("trinity"),
            "location": profile.get("location"),
            "industries": profile.get("industries", [])
        },
        "message": f"Found {len(matches)} jobs matching your profile."
    }


@tool(args_schema=SaveJobInput)
def save_job(user_id: str, job_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Save a job to user's saved list.

    Args:
        user_id: User ID saving the job
        job_id: UUID of the job to save
        notes: Optional notes about the job

    Returns:
        Confirmation of saved job
    """
    client = _get_neon_client()
    if not client:
        return {
            "success": False,
            "error": "Database not available"
        }

    result = _run_async(client.save_job(user_id, job_id, notes))
    if result is None:
        return {
            "success": False,
            "error": "Failed to save job. It may already be saved or not exist."
        }

    return {
        "success": True,
        "saved_job": result,
        "message": "Job saved successfully! You can view it in your saved jobs."
    }


@tool(args_schema=GetSavedJobsInput)
def get_saved_jobs(user_id: str, status: Optional[str] = None) -> Dict[str, Any]:
    """
    Get user's saved jobs.

    Args:
        user_id: User ID to get saved jobs for
        status: Optional status filter

    Returns:
        List of saved jobs
    """
    client = _get_neon_client()
    if not client:
        return {
            "success": False,
            "error": "Database not available",
            "jobs": []
        }

    jobs = _run_async(client.get_saved_jobs(user_id, status))
    if jobs is None:
        jobs = []

    return {
        "success": True,
        "count": len(jobs),
        "jobs": jobs,
        "status_filter": status,
        "message": f"You have {len(jobs)} saved jobs" + (f" with status '{status}'" if status else "") + "."
    }


@tool(args_schema=UpdateJobStatusInput)
def update_job_status(
    user_id: str,
    job_id: str,
    status: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the status of a saved job.

    Args:
        user_id: User ID who saved the job
        job_id: UUID of the saved job
        status: New status (saved, applied, interviewing, rejected, accepted)
        notes: Optional notes to add/update

    Returns:
        Updated saved job
    """
    if status not in VALID_SAVE_STATUS:
        return {
            "success": False,
            "error": f"Invalid status. Choose from: {', '.join(VALID_SAVE_STATUS)}"
        }

    client = _get_neon_client()
    if not client:
        return {
            "success": False,
            "error": "Database not available"
        }

    result = _run_async(client.update_saved_job_status(user_id, job_id, status, notes))
    if result is None:
        return {
            "success": False,
            "error": "Failed to update job status. Job may not be in your saved list."
        }

    return {
        "success": True,
        "updated_job": result,
        "message": f"Job status updated to '{status}'."
    }


@tool(args_schema=GetJobDetailsInput)
def get_job_details(job_id: str) -> Dict[str, Any]:
    """
    Get full details for a specific job.

    Args:
        job_id: UUID of the job

    Returns:
        Full job details
    """
    client = _get_neon_client()
    if not client:
        return {
            "success": False,
            "error": "Database not available"
        }

    job = _run_async(client.get_job(job_id))
    if job is None:
        return {
            "success": False,
            "error": "Job not found"
        }

    return {
        "success": True,
        "job": job,
        "message": f"Details for {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}"
    }


# Export all tools as a list
JOB_TOOLS = [
    search_jobs,
    match_jobs,
    save_job,
    get_saved_jobs,
    update_job_status,
    get_job_details,
]
