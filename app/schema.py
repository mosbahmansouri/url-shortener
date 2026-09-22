



from pydantic import BaseModel, EmailStr, HttpUrl


class ShortenIn(BaseModel):
    url: HttpUrl

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginUser(BaseModel):
    email: EmailStr
    password: str


