from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PasswordResetStateResponse(BaseModel):
    has_ppp_sessions: bool
    active_code: Optional[str] = None
    expires_at: Optional[datetime] = None
    can_generate: bool = True
    code_id: Optional[int] = None


class PasswordResetGenerateResponse(BaseModel):
    code: str
    expires_at: datetime
    code_id: int
    message: str = "Код сгенерирован"


class PasswordResetPollResponse(BaseModel):
    code_used: bool = False
    code_expired: bool = False
    active_code: Optional[str] = None
    expires_at: Optional[datetime] = None
    code_id: Optional[int] = None
