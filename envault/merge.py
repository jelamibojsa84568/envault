"""Merge strategies for combining env variable sets."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class MergeStrategy(str, Enum):
    OURS = "ours"       # local values win on conflict
    THEIRS = "theirs"   # remote values win on conflict
    UNION = "union"     # keep all keys; local wins on conflict (same as OURS but explicit)


class MergeConflictError(Exception):
    """Raised when a conflict is found and strategy is not set to resolve it."""


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, local, remote)
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        lines: List[str] = []
        if self.added:
            lines.append(f"  Added   : {', '.join(sorted(self.added))}")
        if self.removed:
            lines.append(f"  Removed : {', '.join(sorted(self.removed))}")
        if self.conflicts:
            lines.append(f"  Conflicts ({len(self.conflicts)}):")
            for key, local, remote in self.conflicts:
                lines.append(f"    {key}: local={local!r} remote={remote!r}")
        if not lines:
            lines.append("  No changes.")
        return "\n".join(lines)


def merge(
    local: Dict[str, str],
    remote: Dict[str, str],
    strategy: MergeStrategy = MergeStrategy.OURS,
) -> MergeResult:
    """Merge *remote* into *local* using the given strategy.

    Parameters
    ----------
    local:    The current (local) env mapping.
    remote:   The incoming (remote) env mapping.
    strategy: How to resolve key conflicts.

    Returns
    -------
    MergeResult with the merged mapping and metadata.
    """
    merged: Dict[str, str] = {}
    conflicts: List[Tuple[str, str, str]] = []
    added: List[str] = []
    removed: List[str] = []

    all_keys = set(local) | set(remote)

    for key in sorted(all_keys):
        in_local = key in local
        in_remote = key in remote

        if in_local and not in_remote:
            merged[key] = local[key]
        elif in_remote and not in_local:
            merged[key] = remote[key]
            added.append(key)
        else:
            # present in both
            if local[key] == remote[key]:
                merged[key] = local[key]
            else:
                conflicts.append((key, local[key], remote[key]))
                if strategy in (MergeStrategy.OURS, MergeStrategy.UNION):
                    merged[key] = local[key]
                else:  # THEIRS
                    merged[key] = remote[key]

    # keys in local but not remote are implicitly kept; detect keys only in remote as "added"
    # keys only in local that are missing from remote
    removed = [k for k in local if k not in remote]

    return MergeResult(merged=merged, conflicts=conflicts, added=added, removed=removed)
