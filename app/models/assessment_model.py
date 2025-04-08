import datetime
from typing import Dict, Optional, List
from beanie import Document, Link
from pydantic import Field
from app.models.user_model import UserSchema

class AssessmentTaskSchema(Document):
    """Schema for assessment tasks in MongoDB"""
    user_id: Link[UserSchema] = Field(...)
    chat_id: str = Field(...)
    assessment_task: Dict = Field(...)
    assessment_inputs: Dict = Field(...)
    token_usage: Dict = Field(...)
    cost: Dict = Field(...)
    is_published: bool = Field(default=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    
    class Settings:
        name = "assessment_tasks"
        
    class Config:
        arbitrary_types_allowed = True