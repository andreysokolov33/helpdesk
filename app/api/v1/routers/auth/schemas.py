from pydantic import BaseModel, field_validator


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
