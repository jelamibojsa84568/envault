"""Lint .env files for common issues before pushing to the vault."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LintIssue:
    line: int
    key: str
    code: str
    message: str
    severity: str  # "error" | "warning"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


_VALID_KEY_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_abcdefghijklmnopqrstuvwxyz"
)


def _check_key(lineno: int, key: str, issues: List[LintIssue]) -> None:
    if not key:
        issues.append(LintIssue(lineno, key, "E001", "Empty key name", "error"))
        return
    if key[0].isdigit():
        issues.append(
            LintIssue(lineno, key, "E002", "Key must not start with a digit", "error")
        )
    if not all(c in _VALID_KEY_CHARS for c in key):
        issues.append(
            LintIssue(
                lineno, key, "E003",
                "Key contains invalid characters (use A-Z, a-z, 0-9, _)",
                "error",
            )
        )
    if key != key.upper():
        issues.append(
            LintIssue(lineno, key, "W001", "Key is not uppercase", "warning")
        )


def _check_value(lineno: int, key: str, value: str, issues: List[LintIssue]) -> None:
    if value == "":
        issues.append(
            LintIssue(lineno, key, "W002", "Value is empty", "warning")
        )
    if len(value) > 4096:
        issues.append(
            LintIssue(lineno, key, "W003", "Value exceeds 4096 characters", "warning")
        )


def lint(env: Dict[str, str]) -> LintResult:
    """Lint a parsed env dict. Keys are assumed to be in insertion order."""
    result = LintResult()
    seen: Dict[str, int] = {}
    for lineno, (key, value) in enumerate(env.items(), start=1):
        if key in seen:
            result.issues.append(
                LintIssue(
                    lineno, key, "E004",
                    f"Duplicate key (first seen on line {seen[key]})",
                    "error",
                )
            )
        else:
            seen[key] = lineno
        _check_key(lineno, key, result.issues)
        _check_value(lineno, key, value, result.issues)
    return result
