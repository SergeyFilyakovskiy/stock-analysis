from uuid import UUID
from pydantic import BaseModel


class ProfileResponse(BaseModel):
    id:          UUID
    email:       str
    role:        str
    first_name:  str | None
    last_name:   str | None
    bio:         str | None
    avatar_url:  str | None
    is_verified: bool
    full_name:   str | None