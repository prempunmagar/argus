from pydantic import BaseModel
from typing import Optional


# ── Request bodies only — both endpoints return 204 No Content ─────────────────
# The virtual card is issued server-side and stored in virtual_cards table.
# The shopping agent retrieves it via GET /transactions/{id}/status polling.

class ApproveRequest(BaseModel):
    note: Optional[str] = None   # e.g. "Looks good, go ahead"


class DenyRequest(BaseModel):
    note: Optional[str] = None   # e.g. "Too expensive, find something cheaper"
