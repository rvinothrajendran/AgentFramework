from __future__ import annotations
from typing import Any, Awaitable, Callable, Iterator, Optional
from agent_framework import ChatContext, ChatMiddleware
from .tool_limits import ToolLimits, ToolUsageState

class ToolLimitMiddleware(ChatMiddleware):
    """Enforces global and per-tool call limits on LLM-requested function calls.

    After each LLM turn the middleware inspects every ``function_call`` content
    item in the response, tracks how many times each tool has been called, and
    silently removes any call that breaches the configured limits.  When calls
    are suppressed the optional *on_limit_exceeded* callback is invoked.

    The middleware does **not** raise an exception; it drops the over-limit
    calls so the agent loop can continue cleanly

    Usage::

        from tool_limit_middleware import ToolLimitMiddleware
        from tool_limit_middleware.tool_limits import ToolLimits

        middleware = ToolLimitMiddleware(
            limits=ToolLimits(
                global_max=5,
                per_tool_max={"get_weather": 3},
            ),
            on_limit_exceeded=lambda info: print("Limit hit:", info),
        )

        # Retrieve counters at any time
        usage = middleware.get_current_usage()
        print(usage.total_calls, "/", usage.global_limit)

        # Reset counters for a new session
        middleware.reset()
    """

    def __init__(
        self,
        *,
        limits: Optional[ToolLimits] = None,
        on_limit_exceeded: Optional[Callable[[dict[str, Any]], Any]] = None,
    ) -> None:
        self._limits = limits or ToolLimits()
        self.on_limit_exceeded = on_limit_exceeded
        self._total_calls: int = 0
        self._tool_counts: dict[str, int] = {}       # allowed calls per tool
        self._attempted_counts: dict[str, int] = {}  # all attempted calls per tool

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _enforce(self, tool_name: str) -> bool:
        """Record one tool-call attempt and return True if the call is allowed.

        Purely synchronous — safe to call in an asyncio event loop without a
        lock because CPython's asyncio runs on a single OS thread and this
        method contains no ``await`` points.
        """
        # Always record the attempt, regardless of outcome
        self._attempted_counts[tool_name] = self._attempted_counts.get(tool_name, 0) + 1

        if self._total_calls >= self._limits.global_max:
            return False

        existing = self._tool_counts.get(tool_name, 0)
        per_max = self._limits.per_tool_max.get(tool_name)
        if per_max is not None and existing >= per_max:
            return False

        self._tool_counts[tool_name] = existing + 1
        self._total_calls += 1
        return True

    @staticmethod
    def _iter_function_calls(result: Any) -> Iterator[tuple[Any, Any]]:
        """Yield ``(message, content)`` for every ``function_call`` content in *result*."""
        for message in getattr(result, "messages", None) or []:
            for content in list(getattr(message, "contents", None) or []):
                if getattr(content, "type", None) == "function_call":
                    yield message, content

    @staticmethod
    def _remove_blocked_calls(result: Any, blocked_names: set[str]) -> None:
        """Remove all ``function_call`` contents whose tool name is in *blocked_names*."""
        messages = getattr(result, "messages", None)
        if not messages:
            return

        for message in messages:
            contents = getattr(message, "contents", None)
            if contents is None:
                continue
            to_remove = [
                c for c in contents
                if getattr(c, "type", None) == "function_call"
                and getattr(c, "name", None) in blocked_names
            ]
            for item in to_remove:
                try:
                    contents.remove(item)
                except (ValueError, AttributeError):
                    pass

        # Drop messages that became empty after removing blocked calls
        empty = [m for m in messages if not getattr(m, "contents", None)]
        for m in empty:
            try:
                messages.remove(m)
            except (ValueError, AttributeError):
                pass

    async def _fire_exceeded_callback(self, blocked_names: set[str]) -> None:
        if not self.on_limit_exceeded or not blocked_names:
            return
        payload = {
            "blocked_tools": sorted(blocked_names),
            "total_calls": self._total_calls,
            "global_limit": self._limits.global_max,
        }
        result = self.on_limit_exceeded(payload)
        if hasattr(result, "__await__"):
            await result

    # ------------------------------------------------------------------
    # ChatMiddleware contract
    # ------------------------------------------------------------------

    async def process(
        self, context: ChatContext, call_next: Callable[[], Awaitable[None]]
    ) -> None:
        if context.stream:
            await self._process_streaming(context, call_next)
        else:
            await self._process_non_streaming(context, call_next)

    async def _process_non_streaming(
        self, context: ChatContext, call_next: Callable[[], Awaitable[None]]
    ) -> None:
        await call_next()

        result = getattr(context, "result", None)
        if result is None:
            return

        blocked: set[str] = set()
        for message, content in self._iter_function_calls(result):
            tool_name = getattr(content, "name", None) or "unknown"
            if not self._enforce(tool_name):
                message.contents[:] = [
                    item for item in message.contents if item is not content
                ]
                blocked.add(tool_name)

        if blocked:
            result.messages[:] = [
                message for message in result.messages
                if getattr(message, "contents", None)
            ]
            await self._fire_exceeded_callback(blocked)

    async def _process_streaming(
        self, context: ChatContext, call_next: Callable[[], Awaitable[None]]
    ) -> None:
        blocked_tools: list[str] = []

        def _transform(update: Any) -> Any:
            contents = getattr(update, "contents", None)
            if not contents:
                return update
            to_remove = []
            for content in list(contents):
                if getattr(content, "type", None) == "function_call":
                    tool_name = getattr(content, "name", None) or "unknown"
                    if not self._enforce(tool_name):
                        to_remove.append(content)
                        blocked_tools.append(tool_name)
            for item in to_remove:
                try:
                    contents.remove(item)
                except (ValueError, AttributeError):
                    pass
            return update

        async def _on_stream_done(response: Any) -> Any:
            await self._fire_exceeded_callback(set(blocked_tools))
            return response

        context.stream_transform_hooks.append(_transform)
        context.stream_result_hooks.append(_on_stream_done)
        await call_next()

    def reset(self) -> None:
        """Reset all call counters to zero."""
        self._total_calls = 0
        self._tool_counts.clear()
        self._attempted_counts.clear()

    def get_current_usage(self) -> ToolUsageState:
        """Return a snapshot of current tool-call counters."""
        return ToolUsageState(
            total_calls=self._total_calls,
            global_limit=self._limits.global_max,
            per_tool=dict(self._attempted_counts),
            per_tool_allowed=dict(self._tool_counts),
            per_tool_limits=dict(self._limits.per_tool_max),
        )
