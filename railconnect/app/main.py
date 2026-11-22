import os
import secrets
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from dotenv import load_dotenv

from app.database import create_db_and_tables, get_session
from app.models import User, Train, Booking, PasswordReset
from app.schemas import (
    SignupRequest, LoginRequest, UserPublic, TokenResponse, TrainCreate,
    TrainPublic, BookingCreate, BookingPublic, ForgotPasswordRequest,
    ResetPasswordRequest, MessageResponse
)
from app.security import (
    hash_password, verify_password, create_access_token, decode_access_token,
    hash_reset_token
)

load_dotenv()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@railconnect.local").strip().lower()
RESET_TOKEN_EXPIRE_MINUTES = 15
bearer_scheme = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="RailConnect API",
    description="Railway train search and ticket booking backend",
    version="1.0.0",
    lifespan=lifespan,
)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@app.get("/")
def root():
    return {"message": "Welcome to RailConnect API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/signup", response_model=UserPublic, status_code=201)
def signup(data: SignupRequest, session: Session = Depends(get_session)):
    email = str(data.email).lower()
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered")
    role = "admin" if email == ADMIN_EMAIL else "user"
    user = User(email=email, hashed_password=hash_password(data.password), role=role)
    session.add(user)
    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Email is already registered")
    return user

@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    email = str(data.email).lower()
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_access_token(user.id, user.email, user.role),
            "token_type": "bearer"}

@app.get("/auth/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user)):
    # JWT is stateless in this starter: the client should discard the token.
    # It remains valid until expiry; server-side revocation is not implemented.
    return {"message": "Logged out locally. Discard the access token on the client; it expires automatically."}

@app.post("/auth/forgot-password", response_model=MessageResponse)
def forgot_password(data: ForgotPasswordRequest, session: Session = Depends(get_session)):
    email = str(data.email).lower()
    user = session.exec(select(User).where(User.email == email)).first()
    # Generic response avoids revealing whether an account exists.
    response = {"message": "If the account exists, a reset token has been generated."}
    if not user:
        return response
    raw_token = secrets.token_urlsafe(32)
    reset = PasswordReset(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
        used=False,
    )
    session.add(reset)
    session.commit()
    # Development simulation only: return token for testing; in production email it instead.
    response["reset_token"] = raw_token
    return response

@app.post("/auth/reset-password")
def reset_password(data: ResetPasswordRequest, session: Session = Depends(get_session)):
    token_hash = hash_reset_token(data.token)
    reset = session.exec(select(PasswordReset).where(
        PasswordReset.token_hash == token_hash
    )).first()
    if not reset or reset.used:
        raise HTTPException(status_code=400, detail="Invalid or already-used reset token")
    expires = reset.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= expires:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    user = session.get(User, reset.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    user.hashed_password = hash_password(data.new_password)
    reset.used = True
    session.add(user)
    session.add(reset)
    session.commit()
    return {"message": "Password reset successfully. The token can only be used once."}

@app.post("/admin/trains", response_model=TrainPublic, status_code=201)
def add_train(
    data: TrainCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    if data.source.strip().casefold() == data.destination.strip().casefold():
        raise HTTPException(status_code=422, detail="Source and destination must differ")
    train = Train(
        train_number=data.train_number.strip(),
        name=data.name.strip(),
        source=data.source.strip(),
        destination=data.destination.strip(),
        departure_time=data.departure_time,
        arrival_time=data.arrival_time,
        total_seats=data.total_seats,
        available_seats=data.total_seats,
    )
    session.add(train)
    try:
        session.commit()
        session.refresh(train)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Train number already exists")
    return train

@app.get("/trains", response_model=list[TrainPublic])
def search_trains(
    source: str,
    destination: str,
    session: Session = Depends(get_session),
):
    if source.strip().casefold() == destination.strip().casefold():
        raise HTTPException(status_code=422, detail="Source and destination must differ")
    trains = session.exec(select(Train).where(
        Train.is_active == True,
        Train.source.ilike(source.strip()),
        Train.destination.ilike(destination.strip()),
    )).all()
    return trains

@app.get("/trains/{train_id}", response_model=TrainPublic)
def get_train(train_id: int, session: Session = Depends(get_session)):
    train = session.get(Train, train_id)
    if not train or not train.is_active:
        raise HTTPException(status_code=404, detail="Train not found")
    return train

@app.get("/trains/{train_id}/seats")
def check_seats(train_id: int, session: Session = Depends(get_session)):
    train = session.get(Train, train_id)
    if not train or not train.is_active:
        raise HTTPException(status_code=404, detail="Train not found")
    return {"train_id": train.id, "train_number": train.train_number,
            "available_seats": train.available_seats, "total_seats": train.total_seats}

@app.post("/bookings", response_model=BookingPublic, status_code=201)
def create_booking(
    data: BookingCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    train = session.get(Train, data.train_id)
    if not train or not train.is_active:
        raise HTTPException(status_code=404, detail="Train not found")
    if train.available_seats < data.seats:
        raise HTTPException(status_code=409, detail="Not enough seats available")
    train.available_seats -= data.seats
    pnr = secrets.token_hex(5).upper()
    booking = Booking(pnr=pnr, user_id=current_user.id, train_id=train.id, seats=data.seats)
    session.add(train)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking

@app.get("/bookings", response_model=list[BookingPublic])
def my_bookings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(select(Booking).where(
        Booking.user_id == current_user.id
    ).order_by(Booking.id.desc())).all()

@app.get("/bookings/{pnr}", response_model=BookingPublic)
def get_booking(
    pnr: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    booking = session.exec(select(Booking).where(Booking.pnr == pnr.upper())).first()
    if not booking or (booking.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.post("/bookings/{pnr}/cancel", response_model=BookingPublic)
def cancel_booking(
    pnr: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    booking = session.exec(select(Booking).where(Booking.pnr == pnr.upper())).first()
    if not booking or (booking.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == "CANCELLED":
        raise HTTPException(status_code=409, detail="Booking is already cancelled")
    train = session.get(Train, booking.train_id)
    if train:
        train.available_seats = min(train.total_seats, train.available_seats + booking.seats)
        session.add(train)
    booking.status = "CANCELLED"
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
