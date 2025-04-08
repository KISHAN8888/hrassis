from pydantic import Field, BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from beanie import Document, Link
from app.models.user_model import UserSchema

class JDInputSchema(BaseModel):
    company_name: str 
    job_title: str
    department: str
    location: str
    job_type: str
    skills: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    experience: Optional[str] = None
    salary_range: Optional[str] = None
    about_url: Optional[str] = None
    tone: Optional[str] = "English"

class JDOutputSchema(BaseModel):
    job_title: str
    company_name: str
    introduction: str
    responsibilities: List[str]
    requirements: List[str]
    job_type: str
    call_to_action: str

class JDTokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class JDCost(BaseModel):
    prompt_cost: float
    completion_cost: float
    total_cost: float

class JobDescriptionSchema(Document):
    user_id: Link[UserSchema]
    chat_id: str
    jd_inputs: Optional[JDInputSchema]
    job_description: JDOutputSchema
    is_generated: bool = True
    token_usage: JDTokenUsage
    cost: JDCost
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_publish: bool = False
    rejected: Optional[List[str]] = []
    accepted: Optional[List[str]] = []
    class Settings:
        name="jobDescription"
        indexes=['chat_id']
        is_null=True
        


