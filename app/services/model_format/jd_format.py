from pydantic import BaseModel, Field
from typing import List

class JobDescription(BaseModel):
    job_title: str = Field(description="Clear, professional title for the position being advertised")
    company_name: str = Field(description="Name of the company offering the position")
    introduction: str = Field(description="Brief overview of the company and the role, highlighting key selling points")
    responsibilities: List[str] = Field(description="Detailed list of job duties and expectations for the role")
    requirements: List[str] = Field(description="List of necessary qualifications, skills, experience, and education needed")
    job_type: str = Field(description="Employment type such as full-time, part-time, contract, remote, etc.")
    call_to_action: str = Field(description="Clear instructions on how to apply and next steps in the hiring process")

    class Config:
        extra = "forbid"
