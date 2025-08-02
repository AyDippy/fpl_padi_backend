from passlib.context import CryptContext
from app.core.logging import logger
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# oauth 2 scheme setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# pasword hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# verifies if hashed password in db rhymes with plain password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# hashes users inputed password
def get_password_hash(password):
    return pwd_context.hash(password)

# OAuth2 scheme for token authentication
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

#takes in access token and then returns the  decoded payload
def decode_access_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

# Dependency for getting users

    
