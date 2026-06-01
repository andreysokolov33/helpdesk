from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, model_validator


class TrafficDetailSendRequest(BaseModel):
    date_from: date = Field(..., description="Начало периода (включительно)")
    date_to: date = Field(..., description="Конец периода (включительно)")

    @model_validator(mode="after")
    def check_range(self) -> "TrafficDetailSendRequest":
        if self.date_to < self.date_from:
            raise ValueError("Дата окончания не может быть раньше даты начала")
        return self


class TrafficDetailSendResponse(BaseModel):
    message: str
    email: str
