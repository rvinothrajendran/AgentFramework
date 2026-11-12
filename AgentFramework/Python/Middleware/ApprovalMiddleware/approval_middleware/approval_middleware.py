from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from agent_framework import FunctionInvocationContext, FunctionMiddleware

ApprovalCallback = Callable[[FunctionInvocationContext], Any]
DenialMessageFactory = Callable[[FunctionInvocationContext], str]

_DEFAULT_DENIAL = "User denied the call to '{tool_name}'."


def _default_denial_message(context: FunctionInvocationContext) -> str:
    return _DEFAULT_DENIAL.format(tool_name=context.function.name)


class ApprovalMiddleware(FunctionMiddleware):
    """Approval gate for specific tool calls in an AI agent pipeline.

    Before each matching tool call is executed, the *approval_callback* is invoked.

    - ``True``         — approved; the tool executes normally via ``call_next()``.
    - ``False``/``None`` — denied; ``context.result`` is set to a denial message
      so the LLM can reason about the refusal.

    Only the tools listed in *approval_tools* are gated. All other tools
    registered on the agent execute freely without invoking the callback.

    The denial text returned to the LLM can be customised per-call via
    *denial_message_factory*. When supplied it takes precedence over the
    *denial_message* template.

    Usage::

        from approval_middleware import ApprovalMiddleware

        async def console_approve(context: FunctionInvocationContext) -> bool | None:
            answer = input(f"Approve '{context.function.name}'? [y/N] ").strip().lower()
            return answer == "y"

        def my_denial_factory(context: FunctionInvocationContext) -> str:
            return f"User refused '{context.function.name}'. Do not retry this action."

        middleware = ApprovalMiddleware(
            approval_tools=["turn_on_device", "turn_off_device"],
            approval_callback=console_approve,
            denial_message_factory=my_denial_factory,
        )

        agent = client.as_agent(
            name="HomeAssistant",
            tools=[get_status, turn_on, turn_off],
            middleware=[middleware],
        )
    """

    def __init__(
        self,
        *,
        approval_tools: list[str],
        approval_callback: ApprovalCallback,
        denial_message: str = _DEFAULT_DENIAL,
        denial_message_factory: DenialMessageFactory | None = None,
    ) -> None:
        if not approval_tools:
            raise ValueError("approval_tools must not be empty.")
        if approval_callback is None:
            raise ValueError("approval_callback must not be None.")

        self._approval_tools: frozenset[str] = frozenset(approval_tools)
        self._approval_callback = approval_callback
        self._denial_message = denial_message
        self._denial_message_factory = denial_message_factory

    async def process(
        self,
        context: FunctionInvocationContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        """Intercept the tool call and require approval when applicable.

        For tools not in *approval_tools* the middleware is a transparent pass-through.
        For gated tools the callback is invoked:
          - callback returns ``True``  → tool executes normally.
          - callback returns ``False`` or ``None`` → denial message is set as the result.
        """
        if context.function.name not in self._approval_tools:
            await call_next()
            return

        approved = self._approval_callback(context)
        if inspect.isawaitable(approved):
            approved = await approved

        if approved is True:
            await call_next()
        else:
            if self._denial_message_factory is not None:
                context.result = self._denial_message_factory(context)
            else:
                context.result = self._denial_message.format(tool_name=context.function.name)

