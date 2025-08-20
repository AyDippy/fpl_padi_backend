from app.api.v1.endpoints import users, auth, chats
from fastapi import APIRouter


api_routers = APIRouter()

api_routers.include_router(users.router)
api_routers.include_router(auth.router)
api_routers.include_router(chats.router)
