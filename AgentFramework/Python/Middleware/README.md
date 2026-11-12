<div align="center">

# AzureAICommunity - Agent Middleware Packages

A collection of plug-and-play middleware packages for AI agent pipelines built on the **Agent Framework**.

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![GitHub Follow](https://img.shields.io/github/followers/rvinothrajendran?label=Follow%20%40rvinothrajendran&style=social)](https://github.com/rvinothrajendran)
[![YouTube Channel](https://img.shields.io/badge/YouTube-VinothRajendran-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/@VinothRajendran)
[![YouTube Subscribers](https://img.shields.io/youtube/channel/subscribers/UCQf_yRJpsfyEiWWpt1MZ6vA?label=Subscribers&style=social)](https://www.youtube.com/@VinothRajendran)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-rvinothrajendran-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/rvinothrajendran/)

</div>

---

## Overview

This folder contains middleware packages that extend `agent-framework` pipelines with cross-cutting capabilities. Each package is independently installable and can be composed together in the same pipeline.

| Package | PyPI | Downloads | Description | Docs |
|---|---|---|---|---|
| `azureaicommunity-agent-approval` | [![PyPI](https://img.shields.io/pypi/v/azureaicommunity-agent-approval)](https://pypi.org/project/azureaicommunity-agent-approval/) | ![Downloads](https://static.pepy.tech/badge/azureaicommunity-agent-approval) | Human-in-the-loop approval gate — intercepts specific tool calls and requires user confirmation before execution | [README →](ApprovalMiddleware/README.md) |
| `azureaicommunity-agent-language-middleware` | [![PyPI](https://img.shields.io/pypi/v/azureaicommunity-agent-language-middleware)](https://pypi.org/project/azureaicommunity-agent-language-middleware/) | ![Downloads](https://static.pepy.tech/badge/azureaicommunity-agent-language-middleware) | Automatic language detection, translation, and back-translation for multi-lingual agent interactions | [README →](AzureLanguage/language_middleware/README.md) |
| `azureaicommunity-agent-pii-middleware` | [![PyPI](https://img.shields.io/pypi/v/azureaicommunity-agent-pii-middleware)](https://pypi.org/project/azureaicommunity-agent-pii-middleware/) | ![Downloads](https://static.pepy.tech/badge/azureaicommunity-agent-pii-middleware) | PII detection and blocking before sensitive data reaches the LLM | [README →](pii_middleware/README.md) |
| `azureaicommunity-agent-token-guard` | [![PyPI](https://img.shields.io/pypi/v/azureaicommunity-agent-token-guard)](https://pypi.org/project/azureaicommunity-agent-token-guard/) | ![Downloads](https://static.pepy.tech/badge/azureaicommunity-agent-token-guard) | Token usage tracking and quota enforcement per user, per period | [README →](AgentTokenGuard/README.md) |
| `agentaicommunity-agent-context-compression` | [![PyPI](https://img.shields.io/pypi/v/agentaicommunity-agent-context-compression)](https://pypi.org/project/agentaicommunity-agent-context-compression/) | ![Downloads](https://static.pepy.tech/badge/agentaicommunity-agent-context-compression) | Automatic conversation history compression when token count approaches the context-window limit | [README →](ContextCompression/README.md) |
| `agentaicommunity-agent-youtube-middleware` | [![PyPI](https://img.shields.io/pypi/v/agentaicommunity-agent-youtube-middleware)](https://pypi.org/project/agentaicommunity-agent-youtube-middleware/) | ![Downloads](https://static.pepy.tech/badge/agentaicommunity-agent-youtube-middleware) | YouTube video search tools for AI agent pipelines using the YouTube Data API v3 | [README →](YouTubeMiddleware/README.md) |

---

## 🔐 Approval Middleware

Add a **human-in-the-loop approval gate** to any tool call in your agent pipeline. You specify which tools require confirmation — all other tools run freely without interruption. Before a gated tool executes, your callback is invoked; return `True` to approve or `False`/`None` to deny. When denied, a descriptive message is returned to the LLM so it can reason about the refusal.

- Selective gating — only listed tools are intercepted; others execute freely
- Sync or async approval callbacks — console, GUI, HTTP, webhooks — any UI
- LLM-aware denial message set as the tool result on refusal
- Mirrors the C# `ApprovalMiddleware` in the AzureAICommunity Agent Framework

📦 `pip install azureaicommunity-agent-approval`  
📖 [Full documentation](ApprovalMiddleware/README.md)

---

## 🌐 Language Middleware

Automatically detects the user's language, translates incoming messages to the agent's target language, and back-translates the response — using Azure Translator with an optional LLM fallback.

- Language detection with configurable confidence threshold
- Round-trip translation (incoming + response)
- Azure Translator (100+ languages) with LLM fallback
- Fluent `create()` builder API

📦 `pip install azureaicommunity-agent-language-middleware`  
📖 [Full documentation](AzureLanguage/language_middleware/README.md)

---

## 🛡️ PII Middleware

Scans every user message for personally identifiable information (PII) and blocks it before it reaches the LLM — using Microsoft Recognizers Text with optional LLM-assisted validation.

- Detects emails, phones, IPs, credit cards, SSNs, and more
- Pre-built profiles: `strict`, `standard`, `financial`, `healthcare`
- Fluent builder API with custom block/allow lists
- Optional secondary LLM agent for edge-case validation

📦 `pip install azureaicommunity-agent-pii-middleware`  
📖 [Full documentation](pii_middleware/README.md)

---

## 🪙 Token Guard Middleware

Tracks token usage per user and enforces configurable quotas — blocking calls that exceed the limit and invoking a callback when the threshold is breached.

- Per-user token quota enforcement (daily, weekly, monthly, or custom period)
- Pluggable `QuotaStore` — in-memory or bring your own (file, Redis, database, etc.)
- `on_usage` callback with full usage record after every call
- `on_quota_exceeded` callback when a user hits their limit
- Works with any `agent-framework` compatible LLM client

📦 `pip install azureaicommunity-agent-token-guard`  
📖 [Full documentation](AgentTokenGuard/README.md)

---

## �️ Context Compression Middleware

Automatically **summarises older conversation history** when the estimated token count approaches a configurable limit — preventing context-window overflow while keeping the most recent messages intact.

- Pre-call token estimation using `tiktoken` with a configurable `trigger_ratio` (default 80 %)
- Configurable recent-message window preserved verbatim (`keep_last_messages`)
- Assistant + tool message pairs kept together during splitting
- `on_threshold_reached` callback — return `False` to block instead of compress
- Streaming support via transform/result hooks
- Works with any `agent-framework` compatible LLM client

📦 `pip install agentaicommunity-agent-context-compression`  
📖 [Full documentation](ContextCompression/README.md)

---

## � YouTube Middleware

Search YouTube videos directly from your AI agent pipeline using the **YouTube Data API v3**. Exposes a `search_youtube_videos` tool via the `YouTubeTools.create()` builder — wired into any agent as a standard `@tool`.

- Async search via YouTube Data API v3
- Configurable result count, offset (paging), and optional channel restriction
- `YouTubeConfig` builder with `api_key`, `channel_id`, `max_results`, and `default_count`
- Returns video titles, descriptions, and watch URLs

📦 `pip install agentaicommunity-agent-youtube-middleware`  
📖 [Full documentation](YouTubeMiddleware/README.md)

---

## �👤 Author

Built and maintained by **Vinoth Rajendran**.

- 🐙 GitHub: [github.com/rvinothrajendran](https://github.com/rvinothrajendran) — _follow for more projects!_
- 📺 YouTube: [youtube.com/@VinothRajendran](https://www.youtube.com/@VinothRajendran) — _subscribe for tutorials and demos!_
- 💼 LinkedIn: [linkedin.com/in/rvinothrajendran](https://www.linkedin.com/in/rvinothrajendran/) — _let's connect!_

---

## 📄 License

MIT — see individual package LICENSE files for details.
