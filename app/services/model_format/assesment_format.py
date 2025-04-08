from pydantic import BaseModel, Field
from typing import List

class RoleDetail(BaseModel):
    key: str = Field(description="Key describing the aspect of the role (e.g., 'company', 'title', 'focus')")
    value: str = Field(description="Value providing details about the aspect")

class Task(BaseModel):
    name: str = Field(description="Name of the assessment task")
    difficulty_level: str = Field(description="Difficulty level of the task (e.g., 'Beginner to Intermediate')")
    objective: str = Field(description="Concise statement of what the candidate needs to build/demonstrate")
    requirements: List[str] = Field(description="Detailed list of task requirements with technical specifics")
    deliverables: List[str] = Field(description="List of expected outputs from the candidate")
    timeline: str = Field(description="Reasonable timeframe for completion (e.g., '1 Week')")

class AssessmentTask(BaseModel):
    role_overview: List[RoleDetail] = Field(description="Overview of the role including company, role title, focus, and required skills")
    tasks: List[Task] = Field(description="List of assessment tasks with different difficulty levels")
    
    class Config:
        extra = "forbid"