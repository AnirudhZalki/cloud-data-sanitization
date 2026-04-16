from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class FileRecordCreate(BaseModel):
    file_id: str
    original_filename: str
    original_url: str
    sanitized_url: str
    file_type: str

class FileRecordResponse(BaseModel):
    id: int
    user_id: int
    file_id: str
    original_filename: str
    original_url: str
    sanitized_url: str
    file_type: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
