"""Safe prompt-template rendering.

Replaces ``{key}`` placeholders for provided keys only, leaving any other braces
untouched (candidate text / JSON examples never break rendering).
"""

from __future__ import annotations

import re


def render_template(template: str, variables: dict[str, object]) -> str:
    def repl(match: re.Match) -> str:
        key = match.group(1)
        if key in variables:
            return str(variables[key])
        return match.group(0)

    return re.sub(r"\{(\w+)\}", repl, template)
