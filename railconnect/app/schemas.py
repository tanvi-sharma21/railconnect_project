from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserPublic(BaseModel):
    id: int
    email: str
    role: str
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TrainCreate(BaseModel):
    train_number: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    source: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)
    departure_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    arrival_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    total_seats: int = Field(gt=0, le=1000)

class TrainPublic(BaseModel):
    id: int
    train_number: str
    name: str
    source: str
    destination: str
    departure_time: str
    arrival_time: str
    total_seats: int
    available_seats: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class BookingCreate(BaseModel):
    train_id: int
    seats: int = Field(default=1, gt=0, le=10)

class BookingPublic(BaseModel):
    id: int
    pnr: str
    user_id: int
    train_id: int
    seats: int
    status: str
    booked_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)

class MessageResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None
