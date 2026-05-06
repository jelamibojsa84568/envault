"""Export vault secrets to various formats (shell, docker, JSON)."""
from __future__ import annotations

import json
import shlex
from typing import Dict, Literal

ExportFormat = Literal["shell", "docker", "json"]


class UnsupportedFormatError(ValueError):
    """Raised when an unknown export format is requested."""


def _to_shell(env: Dict[str, str]) -> str:
    """Return POSIX-compatible export statements."""
    lines = []
    for key, value in sorted(env.items()):
        safe_value = shlex.quote(value)
        lines.append(f"export {key}={safe_value}")
    return "\n".join(lines) + ("\n" if lines else "")


def _to_docker(env: Dict[str, str]) -> str:
    """Return --env flags suitable for `docker run`."""
    parts = []
    for key, value in sorted(env.items()):
        safe_value = shlex.quote(f"{key}={value}")
        parts.append(f"--env {safe_value}")
    return " ".join(parts)


def _to_json(env: Dict[str, str]) -> str:
    """Return a pretty-printed JSON object."""
    return json.dumps(env, indent=2, sort_keys=True) + "\n"


def render(env: Dict[str, str], fmt: ExportFormat = "shell") -> str:
    """Render *env* dict in the requested *fmt*.

    Parameters
    ----------
    env:  Mapping of variable names to values.
    fmt:  One of ``"shell"``, ``"docker"``, ``"json"``.

    Returns
    -------
    str  Formatted string ready to write to stdout or a file.

    Raises
    ------
    UnsupportedFormatError  If *fmt* is not recognised.
    """
    if fmt == "shell":
        return _to_shell(env)
    if fmt == "docker":
        return _to_docker(env)
    if fmt == "json":
        return _to_json(env)
    raise UnsupportedFormatError(
        f"Unknown format {fmt!r}. Choose from: shell, docker, json."
    )
