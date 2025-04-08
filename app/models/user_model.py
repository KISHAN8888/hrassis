from pydantic import Field, BaseModel
from datetime import datetime, timezone
from typing import Optional, List, Dict
from beanie import Document
from enum import Enum


class ExternalService(str, Enum):
    GOOGLE_AUTH = "google_auth"
    GMAIL = "gmail"
    CALENDAR = "calendar"
    CONTACTS = "contacts"
    SLACK = "slack"
    NOTION = "notion"
    DOCUSIGN = "docusign"

class user_role_enum(str, Enum):
    candidate = "candidate"
    hr = "hr"
    admin = "admin"
    interviewer = "interviewer"


class UserTokenUsage(BaseModel):
    jd_tokens: int = 0
    chat_tokens: int = 0
    resume_tokens: int = 0
    conversation_tokens: int = 0
    assessment_tokens: int = 0
    total_tokens: int = 0

class UserCost(BaseModel):
    jd_cost: float = 0.0
    chat_cost: float = 0.0
    resume_cost: float = 0.0
    conversation_cost: float = 0.0
    assessment_cost: float = 0.0
    total_cost: float = 0.0

class UserSchema(Document):
    email: str
    name: str
    phone: Optional[str] = None  
    company_name: Optional[str] = None
    password: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    chats: List[str] = []
    contacts: List[Dict[str, Optional[str]]] = []
    organization_users: List[Dict[str, Optional[str]]] = []
    token_usage: UserTokenUsage = Field(default_factory=UserTokenUsage)
    cost: UserCost = Field(default_factory=UserCost)
    enabled_services: List[ExternalService] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    credits: float = 100000
    role: Optional[user_role_enum] = "hr"

    class Settings:
        name = "users"
        indexes = ["email"]

