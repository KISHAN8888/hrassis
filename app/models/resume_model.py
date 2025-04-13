from pydantic import Field, BaseModel
from typing import Literal, List, Optional
from datetime import datetime, timezone
from beanie import Document, Link
from app.models.user_model import UserSchema
from app.models.jd_model import JobDescriptionSchema
from app.models.assessment_model import AssessmentTaskSchema

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

class InterviewRoundSchema(BaseModel):
    round_number: int  # Field for the round number
    shortlisted: bool = False
    stage: Literal["NOT_SCHEDULED", "SCHEDULED", "COMPLETED", "CANCELLED"] = "NOT_SCHEDULED"
    scheduled_at: Optional[datetime]
    interview_link: Optional[str]
    interview_score: int = 0
    interview_remarks: Optional[str] = None
    interview_accepted: Optional[bool] = False

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
    user_id: Optional[Link[UserSchema]] = None
    chat_id: Optional[str] = None
    jd_id: Optional[Link[JobDescriptionSchema]] = None
    parsed_resume: Optional[ParsedResumeSchema] = None
    attribute_scores: Optional[AttributeScoreSchema] = None
    candidate_resume: Optional[str] = None
    token_usage: Optional[ResumeTokenUsage] = None
    cost: Optional[ResumeCost] = None
    status: Optional[Literal["ACCEPTED", "REJECTED", "PENDING"]] = "PENDING"

    assessment_id: Optional[Link[AssessmentTaskSchema]] = None
    assessment_link: Optional[str] = None
    assessment_score: Optional[float] = None
    assessment_status: Optional[Literal["PENDING", "COMPLETED", "FAILED"]] = "PENDING"

    interview_rounds: List[InterviewRoundSchema] = Field(default_factory=list)

    final_status: Optional[Literal["REJECTED", "SELECTED", "HOLD", "WITHDRAWN"]] = "HOLD"

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name="resumeData"
        indexes=['chat_id']