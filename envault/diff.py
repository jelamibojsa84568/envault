"""Utilities for comparing two sets of env variables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class EnvDiff:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple[str, str]] = field(default_factory=dict)  # key -> (old, new)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def summary_lines(self) -> List[str]:
        lines: List[str] = []
        for key in sorted(self.added):
            lines.append(f"  + {key}")
        for key in sorted(self.removed):
            lines.append(f"  - {key}")
        for key in sorted(self.changed):
            lines.append(f"  ~ {key}")
        return lines


def compute_diff(old: Dict[str, str], new: Dict[str, str]) -> EnvDiff:
    """Return an EnvDiff describing what changed from *old* to *new*."""
    old_keys = set(old)
    new_keys = set(new)

    added = {k: new[k] for k in new_keys - old_keys}
    removed = {k: old[k] for k in old_keys - new_keys}
    changed = {
        k: (old[k], new[k])
        for k in old_keys & new_keys
        if old[k] != new[k]
    }
    return EnvDiff(added=added, removed=removed, changed=changed)


def format_diff(diff: EnvDiff, *, show_values: bool = False) -> str:
    """Return a human-readable diff string."""
    if diff.is_empty:
        return "No changes."

    parts: List[str] = []
    for key in sorted(diff.added):
        val = f"={diff.added[key]!r}" if show_values else ""
        parts.append(f"+ {key}{val}")
    for key in sorted(diff.removed):
        val = f"={diff.removed[key]!r}" if show_values else ""
        parts.append(f"- {key}{val}")
    for key in sorted(diff.changed):
        old_val, new_val = diff.changed[key]
        if show_values:
            parts.append(f"~ {key}: {old_val!r} -> {new_val!r}")
        else:
            parts.append(f"~ {key}")
    return "\n".join(parts)
