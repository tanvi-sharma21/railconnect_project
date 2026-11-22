import hashlib
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import jwt
from pwdlib import PasswordHash

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY or JWT_SECRET_KEY == "replace-this-with-a-long-random-secret":
    # App remains easy to run locally, but users should set their own secret in .env.
    JWT_SECRET_KEY = "local-development-only-change-me-before-deployment"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def create_access_token(user_id: int, email: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Wrong token type")
    return payload

def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
