from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolLimits:
    """Configuration for tool call limits.

    Attributes:
        global_max: Maximum total tool calls allowed across all tools.
        per_tool_max: Optional per-tool call limits keyed by tool name.
    """

    global_max: int = 10
    per_tool_max: dict[str, int] = field(default_factory=dict)


@dataclass
class ToolUsageState:
    """Snapshot of current tool call counters.

    Attributes:
        total_calls:      Total tool calls that were allowed through.
        global_limit:     Configured global maximum.
        per_tool:         All attempted calls per tool, including blocked ones.
        per_tool_allowed: Calls that were actually allowed per tool.
        per_tool_limits:  Configured per-tool limits.
    """

    total_calls: int
    global_limit: int
    per_tool: dict[str, int]
    per_tool_allowed: dict[str, int]
    per_tool_limits: dict[str, int]
