from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

def utc_now():
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    hashed_password: str
    role: str = Field(default="user", max_length=20)
    created_at: datetime = Field(default_factory=utc_now)

class Train(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    train_number: str = Field(index=True, unique=True, max_length=20)
    name: str = Field(max_length=120)
    source: str = Field(index=True, max_length=100)
    destination: str = Field(index=True, max_length=100)
    departure_time: str = Field(max_length=10, description="24-hour time, e.g. 18:30")
    arrival_time: str = Field(max_length=10, description="24-hour time, e.g. 23:15")
    total_seats: int = Field(gt=0)
    available_seats: int = Field(gt=0)
    is_active: bool = True

class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pnr: str = Field(index=True, unique=True, max_length=20)
    user_id: int = Field(foreign_key="user.id", index=True)
    train_id: int = Field(foreign_key="train.id", index=True)
    seats: int = Field(gt=0)
    status: str = Field(default="CONFIRMED", max_length=20)
    booked_at: datetime = Field(default_factory=utc_now)

class PasswordReset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token_hash: str = Field(index=True, unique=True)
    expires_at: datetime
    used: bool = False
