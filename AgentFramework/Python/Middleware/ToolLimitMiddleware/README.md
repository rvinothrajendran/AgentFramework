<div align="center">

# 🛠️ AzureAICommunity - Agent - Tool Limit Middleware

Prevent **runaway tool calls** by enforcing **global and per-tool call limits** across every AI agent completion.

[![License](https://img.shields.io/github/license/rvinothrajendran/AgentFramework)](https://github.com/rvinothrajendran/AgentFramework/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-AgentFramework-181717?logo=github)](https://github.com/rvinothrajendran/AgentFramework)
[![GitHub Follow](https://img.shields.io/github/followers/rvinothrajendran?label=Follow%20%40rvinothrajendran&style=social)](https://github.com/rvinothrajendran)
[![YouTube Channel](https://img.shields.io/badge/YouTube-VinothRajendran-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/@VinothRajendran)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-rvinothrajendran-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/rvinothrajendran/)

[Getting Started](#-installation) · [Per-Tool Limits](#-per-tool-limits) · [Inspect Usage](#-inspect-usage) · [How It Works](#%EF%B8%8F-how-it-works)

</div>

---

## Overview

`azureaicommunity-agent-tool-limit` is a lightweight guard layer for AI agent pipelines built on `agent-framework`. During each completion it tracks every `function_call` content item emitted by the model and silently suppresses any calls that breach a configurable **global cap** or an optional **per-tool cap**. When calls are suppressed the optional `on_limit_exceeded` callback is invoked.

The middleware does **not** raise an exception — it drops the over-limit calls so the agent loop can continue cleanly, mirroring the behaviour of the .NET `ToolLimitMiddleware`.

---

## ✨ Features

| | Feature |
|---|---|
| 🔢 | **Global call cap** — limits the total number of tool invocations per session |
| 🔧 | **Per-tool limits** — set independent ceilings for individual tool names |
| 🔀 | **Streaming support** — works with both non-streaming and streaming responses |
| 🤫 | **Silent suppression** — over-limit calls are removed; no exception is thrown |
| 📣 | **`on_limit_exceeded` callback** — sync or async callback invoked when calls are blocked |
| 📊 | **Usage introspection** — `get_current_usage()` returns attempted vs allowed counts per tool |
| 🔄 | **Resettable** — `reset()` clears counters for a fresh session |

---

## 📦 Installation

```bash
pip install azureaicommunity-agent-tool-limit
```

Or install directly from source:

```bash
cd AgentFramework/Python/Middleware/ToolLimitMiddleware
pip install -e .
```

---

## 🚀 Quick Start

```python
import asyncio
from agent_framework import tool
from agent_framework.ollama import OllamaChatClient
from tool_limit_middleware import ToolLimitMiddleware, ToolLimits


@tool
def get_weather(location: str) -> str:
    return f"The weather in {location} is sunny with a high of 22°C."


async def main():
    client = OllamaChatClient(model="llama3.2")

    middleware = ToolLimitMiddleware(
        limits=ToolLimits(global_max=5),
    )

    agent = client.as_agent(
        name="WeatherAgent",
        instructions="You are a helpful assistant with a weather tool.",
        tools=[get_weather],
        middleware=[middleware],
    )

    response = await agent.run("What is the weather in Amsterdam?")
    print(response.text)


asyncio.run(main())
```

---

## 🔧 Per-Tool Limits

In addition to the global cap, restrict individual tools independently:

```python
middleware = ToolLimitMiddleware(
    limits=ToolLimits(
        global_max=10,
        per_tool_max={
            "get_weather":  3,
            "search_videos": 2,
        },
    ),
    on_limit_exceeded=lambda info: print("Limit hit:", info),
)
```

Any call to `get_weather` beyond 3, or to `search_videos` beyond 2, is silently removed — even if the global limit has not been reached.

---

## 📊 Inspect Usage

```python
usage = middleware.get_current_usage()

print(f"Total allowed calls: {usage.total_calls} / {usage.global_limit}")

for tool_name, attempted in usage.per_tool.items():
    allowed = usage.per_tool_allowed.get(tool_name, 0)
    limit   = usage.per_tool_limits.get(tool_name)
    limit_text = f" / {limit}" if limit is not None else ""
    print(f"  {tool_name}: attempted={attempted}  allowed={allowed}{limit_text}")

# Reset for a new session
middleware.reset()
```

---

## 🔀 Streaming Support

For **streaming** responses, a `stream_transform_hook` intercepts each `ChatResponseUpdate` as it arrives and removes over-limit function calls in real time. The `on_limit_exceeded` callback is fired once via a `stream_result_hook` after the stream completes.

```python
agent = client.as_agent(
    name="StreamingAgent",
    instructions="You are a helpful assistant.",
    tools=[get_weather],
    middleware=[middleware],
)

# Streaming usage is identical — the middleware handles both paths transparently
async for chunk in agent.run_stream("What is the weather in Amsterdam?"):
    print(chunk.text, end="", flush=True)
```

---

## ⚙️ How It Works

1. **Non-streaming** — `process()` calls `call_next()` to let the LLM complete, then inspects every `function_call` content item in `context.result.messages`. Each tool name is passed through `_enforce()`.
2. **`_enforce(tool_name)`** — Increments the *attempted* counter unconditionally, then checks:
   - `total_calls >= global_max` → blocked
   - `tool_counts[tool_name] >= per_tool_max[tool_name]` → blocked
   - Otherwise allowed: increments `total_calls` and `tool_counts[tool_name]`.
3. **Blocked calls** are removed from `message.contents`. Messages that become empty are also removed from `result.messages`.
4. **`on_limit_exceeded`** — Fires once per `process()` invocation with a payload of `blocked_tools`, `total_calls`, and `global_limit`. Supports both sync and async callbacks.
5. **Streaming** — A `stream_transform_hook` runs `_enforce()` on every update chunk as it arrives. The callback fires after the stream completes via a `stream_result_hook`.

---

