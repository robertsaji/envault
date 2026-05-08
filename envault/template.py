"""Template rendering: substitute .env values into a template file."""

from __future__ import annotations

import re
import string
from pathlib import Path
from typing import Dict, Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def _parse_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE pairs from *text*, ignoring comments and blank lines."""
    env: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            env[key] = value
    return env


def render_template(
    template_path: Path,
    env_path: Path,
    output_path: Optional[Path] = None,
    *,
    strict: bool = True,
) -> str:
    """Render *template_path* by substituting variables from *env_path*.

    Parameters
    ----------
    template_path:
        Path to a template file that may contain ``${VAR}`` or ``$VAR``
        placeholders.
    env_path:
        Path to a ``.env`` file whose key/value pairs are used as the
        substitution mapping.
    output_path:
        If given, the rendered text is written to this path in addition to
        being returned.
    strict:
        When *True* (default) raise :class:`TemplateError` for any
        placeholder that has no corresponding key in the env file.  When
        *False*, unresolved placeholders are left as-is.

    Returns
    -------
    str
        The fully rendered template text.
    """
    if not template_path.exists():
        raise TemplateError(f"Template file not found: {template_path}")
    if not env_path.exists():
        raise TemplateError(f"Env file not found: {env_path}")

    env = _parse_env(env_path.read_text(encoding="utf-8"))
    template_text = template_path.read_text(encoding="utf-8")

    if strict:
        missing = {
            m.group(1) or m.group(2)
            for m in _PLACEHOLDER_RE.finditer(template_text)
            if (m.group(1) or m.group(2)) not in env
        }
        if missing:
            raise TemplateError(
                "Template references undefined variables: "
                + ", ".join(sorted(missing))
            )

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1) or match.group(2)
        return env.get(key, match.group(0))

    rendered = _PLACEHOLDER_RE.sub(_replace, template_text)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

    return rendered
