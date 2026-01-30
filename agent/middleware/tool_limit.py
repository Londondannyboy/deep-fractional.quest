"""
Tool Call Limit Middleware for Deep Agents.

Prevents runaway costs by limiting the number of tool calls
in a single agent run. Essential for production safety.

Raises MaxToolCallsExceeded when limit is reached.
"""

from typing import Any, Callable, Awaitable, Optional, Sequence
from langchain_core.tools import BaseTool
from langchain.agents.middleware import AgentMiddleware


class MaxToolCallsExceeded(Exception):
    """Raised when tool call limit is exceeded."""

    def __init__(self, limit: int, current: int):
        self.limit = limit
        self.current = current
        super().__init__(
            f"Tool call limit exceeded: {current} calls (limit: {limit}). "
            "This prevents runaway costs. Consider breaking your task into smaller steps."
        )


class ToolCallLimitMiddleware(AgentMiddleware):
    """
    Middleware that limits the number of tool calls per agent run.

    This is a critical production safety feature that prevents:
    - Infinite loops in agent reasoning
    - Runaway API costs from tool call storms
    - Resource exhaustion from misconfigured agents

    Configuration:
    - max_calls: Maximum tool calls allowed per run (default: 50)
    - warn_at_percentage: Percentage at which to log warning (default: 80%)

    Usage:
        from middleware import ToolCallLimitMiddleware

        agent = create_deep_agent(
            model=llm,
            tools=tools,
            middleware=[
                ToolCallLimitMiddleware(max_calls=50),
                CopilotKitMiddleware(),
            ],
        )

    Behavior:
    - Counts tool calls across all messages in state
    - Logs warning when approaching limit
    - Raises MaxToolCallsExceeded when limit is hit
    - Resets count for each new conversation thread
    """

    # Required by AgentMiddleware
    tools: Sequence[BaseTool] = []

    def __init__(
        self,
        max_calls: int = 50,
        warn_at_percentage: int = 80,
    ):
        """
        Initialize the ToolCallLimitMiddleware.

        Args:
            max_calls: Maximum tool calls before raising exception (default 50)
            warn_at_percentage: Log warning when this % of limit is reached
        """
        self.max_calls = max_calls
        self.warn_at_percentage = warn_at_percentage
        self._current_thread: Optional[str] = None
        self._call_count = 0
        self._warned = False

    @property
    def name(self) -> str:
        return "ToolCallLimitMiddleware"

    def _count_tool_calls(self, messages: list) -> int:
        """Count total tool calls in message history."""
        count = 0
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                count += len(msg.tool_calls)
        return count

    def _check_limit(self, state: dict, runtime: Any) -> None:
        """
        Check if tool call limit has been exceeded.

        Tracks calls per thread (conversation) and resets when thread changes.
        """
        # Get current thread ID from runtime config if available
        thread_id = 'default'
        if hasattr(runtime, 'config') and runtime.config:
            thread_id = runtime.config.get('configurable', {}).get('thread_id', 'default')

        # Reset counter if thread changed
        if thread_id != self._current_thread:
            self._current_thread = thread_id
            self._call_count = 0
            self._warned = False

        # Count tool calls in current state
        messages = state.get('messages', [])
        self._call_count = self._count_tool_calls(messages)

        # Check warning threshold
        warn_threshold = int(self.max_calls * self.warn_at_percentage / 100)
        if self._call_count >= warn_threshold and not self._warned:
            self._warned = True
            print(
                f"[TOOL_LIMIT] Warning: {self._call_count}/{self.max_calls} tool calls used "
                f"({self.warn_at_percentage}% threshold reached)"
            )

        # Check hard limit
        if self._call_count >= self.max_calls:
            print(f"[TOOL_LIMIT] ERROR: Limit exceeded! {self._call_count}/{self.max_calls}")
            raise MaxToolCallsExceeded(self.max_calls, self._call_count)

    def before_model(self, state: dict, runtime: Any) -> Optional[dict]:
        """Check tool call limits before each model invocation."""
        self._check_limit(state, runtime)
        return None

    async def abefore_model(self, state: dict, runtime: Any) -> Optional[dict]:
        """Async version of before_model."""
        return self.before_model(state, runtime)

    def after_model(self, state: dict, runtime: Any) -> Optional[dict]:
        """Called after model returns. Recheck limits."""
        # Recount after model returns with new tool calls
        messages = state.get('messages', [])
        self._call_count = self._count_tool_calls(messages)
        return None

    async def aafter_model(self, state: dict, runtime: Any) -> Optional[dict]:
        """Async version of after_model."""
        return self.after_model(state, runtime)

    def wrap_tool_call(self, request: Any, handler: Callable) -> Any:
        """
        Intercept tool calls to increment counter and check limits.
        """
        self._call_count += 1

        # Check if we've hit the limit
        if self._call_count >= self.max_calls:
            print(f"[TOOL_LIMIT] ERROR: Limit exceeded during tool call! {self._call_count}/{self.max_calls}")
            raise MaxToolCallsExceeded(self.max_calls, self._call_count)

        # Check warning threshold
        warn_threshold = int(self.max_calls * self.warn_at_percentage / 100)
        if self._call_count >= warn_threshold and not self._warned:
            self._warned = True
            print(
                f"[TOOL_LIMIT] Warning: {self._call_count}/{self.max_calls} tool calls used "
                f"({self.warn_at_percentage}% threshold reached)"
            )

        return handler(request)

    async def awrap_tool_call(self, request: Any, handler: Callable) -> Any:
        """Async version of wrap_tool_call."""
        self._call_count += 1

        # Check if we've hit the limit
        if self._call_count >= self.max_calls:
            print(f"[TOOL_LIMIT] ERROR: Limit exceeded during tool call! {self._call_count}/{self.max_calls}")
            raise MaxToolCallsExceeded(self.max_calls, self._call_count)

        # Check warning threshold
        warn_threshold = int(self.max_calls * self.warn_at_percentage / 100)
        if self._call_count >= warn_threshold and not self._warned:
            self._warned = True
            print(
                f"[TOOL_LIMIT] Warning: {self._call_count}/{self.max_calls} tool calls used "
                f"({self.warn_at_percentage}% threshold reached)"
            )

        return await handler(request)

    def get_stats(self) -> dict:
        """Return statistics about middleware usage."""
        return {
            "current_thread": self._current_thread,
            "call_count": self._call_count,
            "max_calls": self.max_calls,
            "limit_percentage": round(self._call_count / self.max_calls * 100, 1) if self.max_calls else 0,
        }

    def reset(self) -> None:
        """Manually reset the counter (useful for testing)."""
        self._call_count = 0
        self._warned = False
        self._current_thread = None
