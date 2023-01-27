# security.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt as jose_jwt
from pydantic import BaseModel
from typing import List
import passlib
import passlib.context
from schemas import TokenData
from models import User
import bcrypt
import time



# Secret key for JWT
SECRET_KEY = "secretkey"
ALGORITHM = "HS256"
access_expires = 900  # 15 minutes
refresh_expires = 7200  # 2 hours
pwd_context = passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")


# Use OAuth2PasswordBearer for token validation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def verify_password(password: str, hashed_password: str) -> bool:
    """Verify the password using bcrypt library"""
    password_bytes = password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def hash_password(password: str) -> str:
    """Hash the password using bcrypt library"""
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_password.decode()
# def create_access_token(data: dict):
#     """Create a new access token"""
#     to_encode = data
#     to_encode.update({"exp": access_expires})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


def create_access_token(data: dict):
    """Create a new access token"""
    to_encode = data
    to_encode.update({"exp": time.time() + 900})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a new refresh token"""
    to_encode = data
    to_encode.update({"exp": time.time()+7200})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def validate_token(token: str):
    """Validate token and return the user ID"""
   
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        company_id: int = payload.get("company_id")
        if email is None:
            raise credentials_exception
        # check if user exists in database
        user = User.query.filter_by(email=email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        token_data = TokenData(email=email, company_id=company_id)
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def create_token(sender_id: int, receiver_email: str, survey_id: str, sending_time: str,language: str):
    """Create a new token"""
    to_encode = {
        "sender_id": sender_id,
        "receiver_email": receiver_email,
        "survey_id": survey_id,
        "sending_time": sending_time,
        "language": language
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt