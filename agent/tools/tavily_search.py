"""
Tavily web search integration for real-time job discovery.

Implements hybrid search pattern:
1. Query database first (instant, free)
2. Query Tavily for fresh results (1-2 sec, costs credits)
3. Auto-save Tavily results to database for future queries
"""

import os
import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Tavily API configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_SEARCH_URL = "https://api.tavily.com/search"

# Job board domains to exclude (we want direct company postings)
EXCLUDED_DOMAINS = [
    "linkedin.com/jobs",
    "indeed.com",
    "glassdoor.com",
    "monster.com",
    "ziprecruiter.com",
    "careerbuilder.com",
    "dice.com",
    "simplyhired.com",
]


class TavilyJobResult(BaseModel):
    """Parsed job result from Tavily search."""
    title: str
    company: str
    url: str
    description: str
    location: Optional[str] = None
    source: str = "tavily"
    score: float = 0.0


async def search_tavily(
    query: str,
    max_results: int = 10,
    include_answer: bool = False,
    search_depth: str = "advanced",
) -> Dict[str, Any]:
    """
    Search Tavily for job postings.

    Args:
        query: Search query (e.g., "fractional CTO jobs London")
        max_results: Maximum results to return (1-20)
        include_answer: Include AI-generated summary
        search_depth: "basic" or "advanced" (advanced is more thorough)

    Returns:
        Dict with results, answer, and metadata
    """
    if not TAVILY_API_KEY:
        return {
            "success": False,
            "error": "TAVILY_API_KEY not configured",
            "results": []
        }

    # Build search query optimized for job postings
    job_query = f"{query} job posting hiring apply"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": job_query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": include_answer,
        "topic": "general",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TAVILY_SEARCH_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            # Filter out job board aggregators
            filtered_results = []
            for result in data.get("results", []):
                url = result.get("url", "").lower()
                is_job_board = any(domain in url for domain in EXCLUDED_DOMAINS)
                if not is_job_board:
                    filtered_results.append(result)

            return {
                "success": True,
                "query": query,
                "results": filtered_results,
                "answer": data.get("answer"),
                "response_time": data.get("response_time"),
                "total_found": len(data.get("results", [])),
                "after_filter": len(filtered_results),
            }

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"Tavily API error: {e.response.status_code}",
            "results": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tavily search failed: {str(e)}",
            "results": []
        }


def parse_job_from_tavily(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a Tavily search result into a job-like structure.

    Args:
        result: Raw Tavily result with title, url, content, score

    Returns:
        Normalized job dict matching our database schema
    """
    title = result.get("title", "")
    content = result.get("content", "")
    url = result.get("url", "")

    # Try to extract company from title (common patterns)
    # "Senior CTO at Acme Corp" -> company = "Acme Corp"
    # "Fractional CFO - TechStartup" -> company = "TechStartup"
    company = "Unknown"
    if " at " in title:
        parts = title.split(" at ")
        if len(parts) > 1:
            company = parts[-1].strip()
    elif " - " in title:
        parts = title.split(" - ")
        if len(parts) > 1:
            company = parts[-1].strip()
    elif " | " in title:
        parts = title.split(" | ")
        if len(parts) > 1:
            company = parts[-1].strip()

    # Extract job title (first part before company separator)
    job_title = title
    for sep in [" at ", " - ", " | "]:
        if sep in title:
            job_title = title.split(sep)[0].strip()
            break

    return {
        "title": job_title,
        "company": company,
        "url": url,
        "description": content[:500] if content else "",  # Truncate long descriptions
        "source": "tavily",
        "tavily_score": result.get("score", 0),
        "raw_title": title,  # Keep original for debugging
    }


async def search_and_save_jobs(
    query: str,
    role_type: Optional[str] = None,
    location: Optional[str] = None,
    engagement_type: Optional[str] = None,
    max_results: int = 10,
    neon_client = None,
) -> Dict[str, Any]:
    """
    Search Tavily for jobs and optionally save to database.

    This is the main function for hybrid search:
    1. Builds optimized query from parameters
    2. Searches Tavily
    3. Parses results into job format
    4. Saves new jobs to database (if client provided)

    Args:
        query: Base search query
        role_type: C-level role (cto, cfo, etc.)
        location: City or "Remote"
        engagement_type: fractional, interim, advisory
        max_results: Max Tavily results
        neon_client: Optional NeonClient for saving

    Returns:
        Dict with parsed jobs and metadata
    """
    # Build optimized search query
    query_parts = []

    if role_type:
        role_map = {
            "cto": "Chief Technology Officer CTO",
            "cfo": "Chief Financial Officer CFO",
            "cmo": "Chief Marketing Officer CMO",
            "coo": "Chief Operating Officer COO",
            "cpo": "Chief Product Officer CPO",
        }
        query_parts.append(role_map.get(role_type.lower(), role_type))

    if engagement_type:
        query_parts.append(engagement_type)

    if location:
        query_parts.append(location)

    if query:
        query_parts.append(query)

    full_query = " ".join(query_parts) if query_parts else "fractional executive jobs"

    # Search Tavily
    tavily_results = await search_tavily(
        query=full_query,
        max_results=max_results,
        include_answer=True,
        search_depth="advanced",
    )

    if not tavily_results.get("success"):
        return tavily_results

    # Parse results into job format
    parsed_jobs = []
    for result in tavily_results.get("results", []):
        job = parse_job_from_tavily(result)
        # Add search context
        job["role_type"] = role_type
        job["engagement_type"] = engagement_type
        job["location"] = location
        parsed_jobs.append(job)

    # Save to database if client provided
    saved_count = 0
    if neon_client and parsed_jobs:
        for job in parsed_jobs:
            try:
                # Check if URL already exists to avoid duplicates
                existing = await neon_client.get_job_by_url(job["url"])
                if not existing:
                    await neon_client.create_job(
                        title=job["title"],
                        company=job["company"],
                        description=job["description"],
                        url=job["url"],
                        role_type=job.get("role_type"),
                        engagement_type=job.get("engagement_type"),
                        location=job.get("location"),
                        source="tavily",
                    )
                    saved_count += 1
            except Exception as e:
                print(f"[TAVILY] Failed to save job: {e}")

    return {
        "success": True,
        "query": full_query,
        "jobs": parsed_jobs,
        "count": len(parsed_jobs),
        "saved_to_db": saved_count,
        "answer": tavily_results.get("answer"),
        "response_time": tavily_results.get("response_time"),
        "source": "tavily",
    }
