"""Simple .env file parser and serialiser for envault."""

import re
from typing import Dict

_LINE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)\s*$"
)


def parse(content: str) -> Dict[str, str]:
    """Parse a .env file string into a dictionary.

    Supports:
    - KEY=VALUE pairs
    - Quoted values (single or double quotes are stripped)
    - Inline comments after a ``#`` outside quotes
    - Blank lines and comment-only lines are ignored
    """
    result: Dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _LINE_RE.match(stripped)
        if not match:
            continue
        key = match.group("key")
        value = match.group("value")
        # Strip inline comments (only outside quotes)
        if not (value.startswith('"') or value.startswith("'")):
            value = value.split(" #")[0].strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def serialise(env: Dict[str, str]) -> str:
    """Serialise a dictionary back to .env file format.

    Values containing spaces or special characters are double-quoted.
    """
    lines = []
    for key, value in env.items():
        if any(c in value for c in (" ", "\t", "#", "'", '"')):
            value = '"{}"'.format(value.replace('"', '\\"'))
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n" if lines else ""
