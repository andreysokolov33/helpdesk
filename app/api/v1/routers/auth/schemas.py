from pydantic import BaseModel, field_validator


class AuthMeResponse(BaseModel):
    user_id: int
    role: str | None = None
    level: int | None = None
    login: str | None = None
    full_name: str | None = None
    is_support_admin: bool = False


class LoginRequest(BaseModel):
    login: str
    password: str

    @field_validator("login")
    @classmethod
    def login_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Login cannot be empty")
        return v
