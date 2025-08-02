from app.core.logging import logger
from app.core.config import settings
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import CreateUser
from app.core.security import get_password_hash
from app.models.user import User
from sqlalchemy import select
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from fastapi import Depends
from app.schemas.auth import Token
from app.core.security import decode_access_token
from jwt.exceptions import InvalidTokenError



# create a new user
async def create_user(db: AsyncSession, user: CreateUser):
    name = user.name
    username = user.username
    email = user.email
    hashed_password = get_password_hash(user.password)

    user = User(
        name= name,
        hashed_password = hashed_password,
        email = email,
        username = username
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User: {user.username} successfully created")
    return user


#get user details by email
async def get_user_details(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        logger.info(f"User found: {user.username}")
        return user
    else:
        logger.info(f"No user with {email} found")
        return None


