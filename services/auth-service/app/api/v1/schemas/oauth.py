from pydantic import BaseModel


class OAuthTokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"