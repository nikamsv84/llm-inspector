import json
from .security_context import SecurityContext

ATTACKABLE_HEADERS = ["X-Model-Override", "X-Force-Model", "X-Preferred-Model"]


def has_model_override_conflict(context: SecurityContext) -> None:
    try:
        body_dict = json.loads(context.body)
    except json.JSONDecodeError:
        return

    declared_model = body_dict.get("model")

    for header in ATTACKABLE_HEADERS:
        if header in context.headers:
            if context.headers[header] != declared_model:
                context.is_combined_attack = True
                context.risk_score = 1.0
                context.flags["combined_model_override"] = True
                return