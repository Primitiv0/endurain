from pydantic import BaseModel


class GarminLogin(BaseModel):
    username: str
    password: str


class MFARequest(BaseModel):
    mfa_code: str
