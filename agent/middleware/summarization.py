"""
Summarization Middleware for Deep Agents.

Automatically trims conversation history to reduce token usage
when it exceeds configured thresholds. This prevents context overflow and
reduces API costs for long conversations.

Pattern based on LangChain 1.0 middleware architecture.
"""

from typing import Any, Callable, Awaitable, Optional, Sequence
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.messages.utils import trim_messages
from langchain_core.tools import BaseTool
from langchain.agents.middleware import AgentMiddleware


def count_tokens_approximately(messages: list[BaseMessage]) -> int:
    """
    Approximate token count for a list of messages.

    Uses a simple heuristic: ~4 characters per token (English average).
    Good enough for trimming decisions without API calls.
    """
    total_chars = 0
    for msg in messages:
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        total_chars += len(content)

        # Account for tool calls if present
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                total_chars += len(str(tc.get('args', {})))

    return total_chars // 4


class SummarizationMiddleware(AgentMiddleware):
    """
    Middleware that trims message history to stay within token limits.

    Uses LangChain's trim_messages utility with 'last' strategy to keep
    the most recent messages while removing older ones when thresholds
    are exceeded.

    Configuration:
    - max_tokens: Maximum tokens allowed in message history (default: 8000)
    - keep_system_message: Whether to always keep the system message (default: True)
    - keep_recent_messages: Minimum number of recent messages to keep (default: 6)

    Usage:
        from middleware import SummarizationMiddleware

        agent = create_deep_agent(
            model=llm,
            tools=tools,
            middleware=[
                SummarizationMiddleware(max_tokens=8000),
                CopilotKitMiddleware(),
            ],
        )
    """

    # Required by AgentMiddleware
    tools: Sequence[BaseTool] = []

    def __init__(
        self,
        max_tokens: int = 8000,
        keep_system_message: bool = True,
        keep_recent_messages: int = 6,
    ):
        """
        Initialize the SummarizationMiddleware.

        Args:
            max_tokens: Maximum token budget for messages (default 8000 for Gemini)
            keep_system_message: Always preserve the first system message
            keep_recent_messages: Minimum recent messages to keep (ensures context)
        """
        self.max_tokens = max_tokens
        self.keep_system_message = keep_system_message
        self.keep_recent_messages = keep_recent_messages
        self._trim_count = 0  # Track how many times we've trimmed

    @property
    def name(self) -> str:
        return "SummarizationMiddleware"

    def _trim_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """
        Trim messages to fit within token budget.

        Uses 'last' strategy: keeps the most recent messages.
        Always preserves system message if configured.
        Ensures tool messages stay paired with their AI messages.
        """
        if not messages:
            return messages

        # Check if trimming is needed
        current_tokens = count_tokens_approximately(messages)
        if current_tokens <= self.max_tokens:
            return messages

        self._trim_count += 1
        print(f"[SUMMARIZATION] Trimming messages: {current_tokens} tokens -> target {self.max_tokens}")

        # Extract system message if present
        system_message = None
        remaining_messages = messages

        if self.keep_system_message and messages and isinstance(messages[0], SystemMessage):
            system_message = messages[0]
            remaining_messages = messages[1:]

        # Calculate token budget for trimmed messages
        system_tokens = count_tokens_approximately([system_message]) if system_message else 0
        available_tokens = self.max_tokens - system_tokens

        # Use LangChain's trim_messages with 'last' strategy
        trimmed = trim_messages(
            remaining_messages,
            strategy="last",
            token_counter=count_tokens_approximately,
            max_tokens=available_tokens,
            start_on="human",  # Ensure we start on a human message
            end_on=("human", "tool"),  # End on valid message types
            include_system=False,  # We handle system message separately
        )

        # Ensure we keep at least some recent messages
        if len(trimmed) < self.keep_recent_messages and len(remaining_messages) >= self.keep_recent_messages:
            trimmed = remaining_messages[-self.keep_recent_messages:]

        # Rebuild message list
        result = []
        if system_message:
            result.append(system_message)
        result.extend(trimmed)

        new_tokens = count_tokens_approximately(result)
        print(f"[SUMMARIZATION] Trimmed to {len(result)} messages, ~{new_tokens} tokens")

        return result

    def before_model(self, state: dict, runtime: Any) -> Optional[dict]:
        """
        Trim messages before they're sent to the model.

        Returns state updates with trimmed messages.
        """
        messages = state.get('messages', [])
        if not messages:
            return None

        trimmed = self._trim_messages(messages)

        # Only return updates if we actually trimmed
        if len(trimmed) < len(messages):
            # Return a special key that tells the model to use trimmed messages
            # but doesn't modify the persisted state
            return {"llm_input_messages": trimmed}

        return None

    async def abefore_model(self, state: dict, runtime: Any) -> Optional[dict]:
        """Async version of before_model."""
        return self.before_model(state, runtime)

    def after_model(self, state: dict, runtime: Any) -> Optional[dict]:
        """Called after model returns. No-op for this middleware."""
        return None

    async def aafter_model(self, state: dict, runtime: Any) -> Optional[dict]:
        """Async version of after_model."""
        return None

    def wrap_tool_call(self, request: Any, handler: Callable) -> Any:
        """Pass through tool calls without modification."""
        return handler(request)

    async def awrap_tool_call(self, request: Any, handler: Callable) -> Any:
        """Async pass through for tool calls."""
        return await handler(request)

    def get_stats(self) -> dict:
        """Return statistics about middleware usage."""
        return {
            "trim_count": self._trim_count,
            "max_tokens": self.max_tokens,
        }
