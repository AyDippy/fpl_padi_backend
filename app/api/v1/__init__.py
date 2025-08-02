from app.api.v1.endpoints import users, auth
from fastapi import APIRouter


api_routers = APIRouter()

api_routers.include_router(users.router)
api_routers.include_router(auth.router)