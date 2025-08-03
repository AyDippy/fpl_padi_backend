from app.crud.user import create_user, get_user_details
from app.db.session import get_db, db_session
from app.core.config import settings
from app.core.logging import logger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select
from app.schemas.user import CreateUser, UserResponse
from app.models.user import User
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from typing import Annotated
from app.utils.send_email import send_notification_email

# router 
router = APIRouter(prefix="/user", tags=["users"])

#oauth 2 scheme setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

@router.post('/signup', response_model= UserResponse)
async def signup(db: db_session, user: CreateUser):
    username = user.username
    email = user.email

    # checking if user name already exists
    stmt1 = select(User).where(User.username == username)
    result1 =  await db.execute(stmt1)
    existing_username = result1.scalar_one_or_none()

    # checking if email already exists
    stmt2 = select(User).where(User.email == email)
    result2 = await db.execute(stmt2)
    existing_email = result2.scalar_one_or_none()

    if existing_email or existing_username:
        logger.info(f"User: {username} already exists")
        raise HTTPException(
            status_code=400,
            detail = "User already exists"
        )

    else:
        new_user = await create_user(db, user)
        logger.info(f"User: {username} signup completed")

        #send welcome email to user after sign up is successful
        try:
            await send_notification_email(
                email_to=new_user.email,
                subject="FPL Padi sign up successful",
                body={
                    "title": "Welcome to FPL Padi App",
                    "name": new_user.username
                }
            )
            logger.info(f"Welcome email delivered successfully to {new_user.email}")
        except Exception as e:
             logger.warning(f"Failed to send welcome email to {new_user.email}: {str(e)}")
        
        return new_user
        
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: db_session):
    try:
        payload = decode_access_token(token)
        if payload is None:
            logger.info("Invalid token: could not decode")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        email = payload.get("sub")
        if email is None:
            logger.info("Invalid token: no email found")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        stmt = select(User).where(User.email == email)
        result =  await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info(f"User {email} authenticated successfully")
            return existing_user
        else:
            logger.info(f"User with email {email} not found")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
@router.get('/me', response_model=UserResponse)
async def get_user_detail(user: Annotated[UserResponse, Depends(get_current_user)]):
    logger.info("Authenticating user")
    return user



