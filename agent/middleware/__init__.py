"""
Middleware for Fractional Quest agent.

Contains production-safety middleware:
- ToolCallLimitMiddleware: Prevents runaway costs from tool loops

Note: Summarization is handled by deepagents' built-in SummarizationMiddleware
which uses an LLM to create intelligent summaries of old messages.
"""

from .tool_limit import ToolCallLimitMiddleware, MaxToolCallsExceeded

__all__ = ["ToolCallLimitMiddleware", "MaxToolCallsExceeded"]
