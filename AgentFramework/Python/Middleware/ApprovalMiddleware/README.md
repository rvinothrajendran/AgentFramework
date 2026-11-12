<div align="center">

# 🔐 AzureAICommunity - Agent - Approval Middleware

Add a **human-in-the-loop approval gate** to AI agent tool calls with a single middleware registration.

[![License](https://img.shields.io/github/license/rvinothrajendran/AgentFramework)](https://github.com/rvinothrajendran/AgentFramework/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-AgentFramework-181717?logo=github)](https://github.com/rvinothrajendran/AgentFramework)
[![GitHub Follow](https://img.shields.io/github/followers/rvinothrajendran?label=Follow%20%40rvinothrajendran&style=social)](https://github.com/rvinothrajendran)
[![YouTube Channel](https://img.shields.io/badge/YouTube-VinothRajendran-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/@VinothRajendran)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-rvinothrajendran-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/rvinothrajendran/)

[Getting Started](#-installation) · [Callback Contract](#-callback-contract) · [How It Works](#%EF%B8%8F-how-it-works) · [Contributing](#-contributing)

</div>

---

## Overview

`azureaicommunity-agent-approval` adds an approval gate directly into the `agent-framework` function-invocation pipeline. You pass **only the tools that need approval** — all other tools registered on the agent execute freely without interruption. Before any gated tool executes, your callback is called with the `FunctionInvocationContext`; you decide whether to approve or deny using any UI: console, desktop dialog, HTTP call to a remote approver, etc. The middleware itself contains no UI code.

This mirrors the pattern established by the C# `ApprovalMiddleware` in the AzureAICommunity Agent Framework.

---

## ✨ Features

| | Feature |
|---|---|
| 🎯 | **Selective gating** — only the tools you specify are intercepted; others run freely |
| 🔔 | **Simple callback** — receives the full `FunctionInvocationContext` with tool name and arguments |
| 💬 | **LLM-aware denial** — when denied, a descriptive message is set as the tool result so the model can reason about the refusal |
| ✏️ | **Custom denial message** — optional `denial_message_factory` for per-call denial text to the LLM |
| 🖥️ | **UI agnostic** — use any approval UI: console, GUI, HTTP, webhooks |
| 🔀 | **Sync & async callbacks** — both synchronous and asynchronous callbacks are supported |
| 🔗 | **Composable** — stacks with other `agent-framework` middleware in the same pipeline |

---

## 📦 Installation

```bash
pip install azureaicommunity-agent-approval
```

Or install directly from source:

```bash
cd AgentFramework/Python/Middleware/ApprovalMiddleware
pip install -e .
```

---

## 🚀 Quick Start

```python
import asyncio
from agent_framework import tool, FunctionInvocationContext
from agent_framework.openai import OpenAIChatCompletionClient
from approval_middleware import ApprovalMiddleware


@tool
def get_device_status(device_name: str) -> str:
    """Get the current status of a smart-home device. Does not change device state."""
    return f"{device_name} is currently OFF."


@tool
def turn_on_device(device_name: str) -> str:
    """Turn on a smart-home device."""
    return f"{device_name} is now ON."


@tool
def turn_off_device(device_name: str) -> str:
    """Turn off a smart-home device."""
    return f"{device_name} is now OFF."


async def console_approve(context: FunctionInvocationContext) -> bool | None:
    print(f"\n[Approval Required] Tool: {context.function.name}")
    answer = input("  Allow? [y/N] ").strip().lower()
    return answer == "y"


async def main():
    client = OpenAIChatCompletionClient(model="gpt-4o", api_key="...", base_url="...")

    # Only the destructive tools are gated.
    # get_device_status is intentionally omitted — it runs freely without prompting.
    def denial_factory(context: FunctionInvocationContext) -> str:
        args = context.arguments or {}
        device = (args.get("device_name", "device") if hasattr(args, "get")
                  else getattr(args, "device_name", "device"))
        if context.function.name == "turn_on_device":
            return f"User refused to turn ON '{device}'. Do not retry — suggest an alternative."
        if context.function.name == "turn_off_device":
            return f"User refused to turn OFF '{device}'. Do not retry — ask what else they want."
        return f"User refused '{context.function.name}'. Do not retry this action."

    middleware = ApprovalMiddleware(
        approval_tools=["turn_on_device", "turn_off_device"],
        approval_callback=console_approve,
        denial_message_factory=denial_factory,
    )

    agent = client.as_agent(
        name="HomeAssistant",
        instructions="You are a helpful smart-home assistant.",
        tools=[get_device_status, turn_on_device, turn_off_device],
        middleware=[middleware],
    )

    response = await agent.run(
        "Check the living room lights, then turn them on and turn off the bedroom fan."
    )
    print(response.text)


asyncio.run(main())
```

---

## 🔔 Callback Contract

The `approval_callback` receives the full `FunctionInvocationContext`.

| Return value | Effect |
|---|---|
| `True` | Approved — the tool executes and its real result is returned to the LLM |
| `False` or `None` | Denied — a denial message is set as the tool result so the LLM can reason about the refusal |

The callback can be **sync or async** — both are supported automatically:

```python
# Async callback
async def my_callback(context: FunctionInvocationContext) -> bool | None:
    # context.function.name  — tool name
    # context.arguments      — validated arguments (dict or Pydantic model)
    return True   # approve
    return False  # deny
    return None   # deny

# Sync callback
def my_callback(context: FunctionInvocationContext) -> bool | None:
    return True
```

---

## ⚙️ Configuration

### `ApprovalMiddleware`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `approval_tools` | `list[str]` | **required** | Tool names that require approval before execution |
| `approval_callback` | `Callable[[FunctionInvocationContext], bool \| None]` | **required** | Sync or async callback invoked before each gated tool call |
| `denial_message` | `str` | `"User denied the call to '{tool_name}'."` | Template string for the denial result. Use `{tool_name}` as a placeholder |
| `denial_message_factory` | `Callable[[FunctionInvocationContext], str] \| None` | `None` | Optional factory called on denial to produce per-call denial text. Takes precedence over `denial_message` when set |

#### `denial_message_factory`

When supplied, the factory is called with the `FunctionInvocationContext` of the denied call and its return value is used as the tool result sent to the LLM. This lets you return different text based on tool name or arguments:

```python
def denial_factory(context: FunctionInvocationContext) -> str:
    match context.function.name:
        case "turn_on_device":
            return f"User refused to turn ON. Do not retry."
        case "turn_off_device":
            return f"User refused to turn OFF. Do not retry."
        case _:
            return f"User refused '{context.function.name}'. Do not retry this action."
```

---

## ⚙️ How It Works

```
LLM decides to call a tool
    └─► FunctionInvocationContext intercepted by ApprovalMiddleware
            │
            ├─ tool name in approval_tools?
            │       ├─ YES → approval_callback(context) called
            │       │           ├─ returns True         → call_next()  ← tool executes normally
            │       │           └─ returns False/None   → denial_message_factory(ctx) or denial_message template
            │       │                                      └─ context.result = denial text
            │       └─ NO  → call_next()    ← tool executes freely, no approval prompt
            │
            └─ agent continues with the result
```

---

## 🤝 Contributing

Contributions are welcome! Please open an issue to discuss what you'd like to change before submitting a pull request.

📁 **Repository:** [https://github.com/rvinothrajendran/AgentFramework](https://github.com/rvinothrajendran/AgentFramework)

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 👤 Author

Built and maintained by **Vinoth Rajendran**.

- 🐙 GitHub: [github.com/rvinothrajendran](https://github.com/rvinothrajendran) — _follow for more projects!_
- 📺 YouTube: [youtube.com/@VinothRajendran](https://www.youtube.com/@VinothRajendran) — _subscribe for tutorials and demos!_
- 💼 LinkedIn: [linkedin.com/in/rvinothrajendran](https://www.linkedin.com/in/rvinothrajendran/) — _let's connect!_

---

## 📄 License

MIT
