from pydantic import BaseModel
from typing import Optional, List


class ProfileResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: str


class ProfilesListResponse(BaseModel):
    profiles: List[ProfileResponse]


class CreateProfileRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
