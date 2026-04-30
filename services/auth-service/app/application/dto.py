from dataclasses import dataclass


@dataclass
class TokenPairDTO:
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"