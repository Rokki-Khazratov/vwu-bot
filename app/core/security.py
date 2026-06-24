"""Security helpers.

Phase 1 is dev-mode: access is gated by a Telegram-id allowlist only.
The bot service-token / webhook secret machinery arrives in Phase 6.
"""

import hashlib
import json


def stable_payload_hash(payload: object) -> str:
    """Deterministic hash of a JSON-serialisable payload for idempotency."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
