from pydantic import BaseModel
from typing import Optional

# User
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# Project
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    figma_url: Optional[str] = None