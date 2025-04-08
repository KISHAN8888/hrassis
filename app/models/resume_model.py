from pydantic import Field, BaseModel
from typing import Literal, List
from datetime import datetime, timezone
from beanie import Document, Link
from app.models.user_model import UserSchema
from app.models.jd_model import JobDescriptionSchema

class ParsedResumeSchema(BaseModel):
    Name: str
    Email: str
    Phone: str
    location: str
    summary: str
    experienceRoles: List[str]
    experienceCompanies: List[str]
    experienceTimePeriods: List[str]
    experienceYears: float
    educationInstitutes: List[str]
    degrees: List[str]
    educationTimePeriods: List[str]
    educationYears: float
    skills: List[str]
    projects: List[str]
    certificationsOrAchievements: List[str]
    links: List[str]

class AttributeScoreSchema(BaseModel):
    skills_score: float
    skills_reason: str
    experience_score: float
    experience_reason: str
    qualifications_score: float
    qualifications_reason: str
    relatedProjects_score: float
    relatedProjects_reason: str
    overall_score: float
    overall_reason: str
    overall_summary: str

class ResumeTokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ResumeCost(BaseModel):
    prompt_cost: float
    completion_cost: float
    total_cost: float

class ResumeSchema(Document):
    user_id: Link[UserSchema]
    chat_id: str
    jd_id: Link[JobDescriptionSchema]
    parsed_resume: ParsedResumeSchema
    attribute_scores: AttributeScoreSchema
    candidate_resume: str
    token_usage: ResumeTokenUsage
    cost: ResumeCost
    status: Literal["ACCEPTED","REJECTED","PENDING"] = "PENDING"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name="resumeData"
        indexes=['chat_id']
