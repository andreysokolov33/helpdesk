from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

FastCheckStatus = Literal["pass", "fail", "warn", "skip"]


class ManagerContact(BaseModel):
    full_name: Optional[str] = None
    phones: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)


class FastCheckStep(BaseModel):
    test_code: str
    variant: int = 0
    check_label: str
    status: FastCheckStatus
    detail: Optional[str] = None
    actions_html: Optional[str] = None
    stop_chain: bool = False


class FastCheckResponse(BaseModel):
    steps: list[FastCheckStep] = Field(default_factory=list)
    stopped_at: Optional[str] = None  # название шага (check_label), на котором остановились
    manager_contacts: list[ManagerContact] = Field(default_factory=list)
