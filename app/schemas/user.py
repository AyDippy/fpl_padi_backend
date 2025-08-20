from pydantic import BaseModel, EmailStr


class CreateUser(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr
    