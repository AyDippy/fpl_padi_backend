from fastapi import APIRouter, Depends, HTTPException
from app.core.logging import logger
from app.core.security import create_access_token, decode_access_token, verify_password, get_password_hash
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.db.session import db_session
from app.models.user import User
from sqlalchemy import select
from app.schemas.auth import Token
from typing import Annotated

# router 
router = APIRouter(prefix = "/auth", tags=["auth"])



# login endpoint
@router.post("/token", response_model=Token)
async def login(db: db_session, form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if not existing_user:
        logger.info(f"user with {email} does not exist")
        raise HTTPException(
            status_code=401,
            detail= "Invalid Credentials"
        )
    
    if not verify_password(password, existing_user.hashed_password):
        logger.info("Incorrect Password")
        raise HTTPException(
            status_code=401,
            detail = "Invalid Credentials"
        )
    
    payload = {"sub": existing_user.email}
    token = create_access_token(data=payload)
    logger.info(f"User: {email} logged in successfully")

    return {
        "access_token": token,
        "token_type": "bearer"
    }




