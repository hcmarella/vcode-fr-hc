import uuid

from pydantic import BaseModel, EmailStr, Field

from app.db.models.user import Role, Team


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    team: Team


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    team: Team
    role: Role

    model_config = {"from_attributes": True}
