from pydantic import BaseModel


class User(BaseModel):
    name: str
    img_b64: str

class SearchQuery(BaseModel):
    img_b64: str

class VerifyQuery(BaseModel):
    img1_b64: str
    img2_b64: str

class AccountUser(BaseModel):
    username: str
    email: str
    password: str