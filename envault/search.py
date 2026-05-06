"""Search and filter environment variables across the vault."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SearchResult:
    key: str
    value: str
    matched_by: str  # 'key', 'value', or 'both'


@dataclass
class SearchSummary:
    query: str
    results: List[SearchResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.results)

    @property
    def is_empty(self) -> bool:
        return len(self.results) == 0


def _match(pattern: str, text: str, use_regex: bool, case_sensitive: bool) -> bool:
    """Return True if *pattern* matches *text*."""
    if not case_sensitive:
        text = text.lower()
        pattern = pattern.lower()
    if use_regex:
        try:
            return bool(re.search(pattern, text))
        except re.error:
            return False
    return fnmatch.fnmatch(text, f"*{pattern}*")


def search(
    env: Dict[str, str],
    query: str,
    *,
    search_keys: bool = True,
    search_values: bool = False,
    use_regex: bool = False,
    case_sensitive: bool = False,
) -> SearchSummary:
    """Search *env* for *query* and return a :class:`SearchSummary`.

    Parameters
    ----------
    env:
        Mapping of variable names to values.
    query:
        The search string or regex pattern.
    search_keys:
        Whether to match against variable names (default ``True``).
    search_values:
        Whether to match against variable values (default ``False``).
    use_regex:
        Treat *query* as a regular expression.
    case_sensitive:
        Perform a case-sensitive match.
    """
    summary = SearchSummary(query=query)

    for key, value in sorted(env.items()):
        key_hit = search_keys and _match(query, key, use_regex, case_sensitive)
        val_hit = search_values and _match(query, value, use_regex, case_sensitive)

        if key_hit and val_hit:
            matched_by = "both"
        elif key_hit:
            matched_by = "key"
        elif val_hit:
            matched_by = "value"
        else:
            continue

        summary.results.append(SearchResult(key=key, value=value, matched_by=matched_by))

    return summary
