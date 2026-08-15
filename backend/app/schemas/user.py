import uuid

from pydantic import BaseModel, EmailStr, Field

from app.db.models.user import Role, Team


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    team: Team
    # Excludes admin deliberately -- self-signup must never be able to grant
    # admin. Enforced again in the endpoint itself (app/api/auth.py), not
    # just by this being the schema default; a client could still send
    # role=admin in the request body.
    role: Role = Role.DEVELOPER


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
