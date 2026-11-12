from types import SimpleNamespace

import pytest

from tool_limit_middleware import ToolLimitMiddleware, ToolLimits


@pytest.mark.asyncio
async def test_streaming_decides_once_per_call_and_handles_name_late():
    callback_payloads = []
    middleware = ToolLimitMiddleware(
        limits=ToolLimits(global_max=1),
        on_limit_exceeded=callback_payloads.append,
    )
    context = SimpleNamespace(
        stream=True,
        stream_transform_hooks=[],
        stream_result_hooks=[],
    )

    async def call_next():
        return None

    await middleware.process(context, call_next)
    transform = context.stream_transform_hooks[0]

    def function_call(call_id, name=None):
        return SimpleNamespace(type="function_call", call_id=call_id, name=name)

    initial_fragment = function_call("allowed-call")
    initial_update = SimpleNamespace(contents=[initial_fragment])
    transform(initial_update)
    assert initial_update.contents == []

    named_fragment = function_call("allowed-call", "allowed_tool")
    named_update = SimpleNamespace(contents=[named_fragment])
    transform(named_update)
    assert named_update.contents == [initial_fragment, named_fragment]

    allowed_arguments = function_call("allowed-call")
    allowed_update = SimpleNamespace(contents=[allowed_arguments])
    transform(allowed_update)
    assert allowed_update.contents == [allowed_arguments]

    blocked_fragment = function_call("blocked-call", "blocked_tool")
    blocked_update = SimpleNamespace(contents=[blocked_fragment])
    transform(blocked_update)
    assert blocked_update.contents == []

    blocked_arguments = function_call("blocked-call")
    blocked_arguments_update = SimpleNamespace(contents=[blocked_arguments])
    transform(blocked_arguments_update)
    assert blocked_arguments_update.contents == []

    await context.stream_result_hooks[0](None)

    usage = middleware.get_current_usage()
    assert usage.total_calls == 1
    assert usage.per_tool == {"allowed_tool": 1, "blocked_tool": 1}
    assert callback_payloads[0]["blocked_tools"] == ["blocked_tool"]
