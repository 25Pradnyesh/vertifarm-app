from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

class SchemaBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class UserProfile(SchemaBase):
    id: str
    name: str
    role: str = "Farm Owner"
    farmName: str = "Greenhouse 1"
    email: str
    avatarUrl: Optional[str] = None

class AuthUser(UserProfile):
    authProvider: Optional[str] = "google"
    googleId: Optional[str] = None
    accessToken: Optional[str] = None
    idToken: Optional[str] = None
    createdAt: Optional[str] = None

class UserUpdate(SchemaBase):
    name: Optional[str] = None
    role: Optional[str] = None
    farmName: Optional[str] = None
    avatarUrl: Optional[str] = None
