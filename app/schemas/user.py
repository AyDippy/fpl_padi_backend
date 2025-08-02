from pydantic import BaseModel


class CreateUser(BaseModel):
    name: str
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    name: str
    username: str
    email: str
    