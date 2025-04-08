from typing import List
from pydantic import BaseModel, Field

class AttributeScores(BaseModel):
    skills_score: float = Field(description="The score for the skills attribute according")
    skills_reason: str = Field(description="The reason for the score for the skills attribute")
    experience_score: float = Field(description="The score for the experience attribute")
    experience_reason: str = Field(description="The reason for the score for the experience attribute")
    qualifications_score: float = Field(description="The score for the qualifications attribute")
    qualifications_reason: str = Field(description="The reason for the score for the qualifications attribute")
    relatedProjects_score: float = Field(description="The score for the related projects attribute")
    relatedProjects_reason: str = Field(description="The reason for the score for the related projects attribute")
    overall_reason: str = Field(description="Overall analysis of the resume as per the criteria given...")
    overall_summary: str = Field(description="The summary of the overall reason")

class Resume(BaseModel):
    Name: str = Field(description="The name of the candidate. Provide in title case.")
    Email: str = Field(description="The email of the candidate")
    Phone: str = Field(description="The phone number of the candidate. Mention country code.")
    location: str = Field(description="The location of the candidate")
    summary: str = Field(description="The summary of the candidate mentioned in the resume. edit any typos or errors in the summary.")
    experienceRoles: List[str] = Field(description="The roles of the candidate. edit any typos or errors in the roles.")
    experienceCompanies: List[str] = Field(description="The companies the candidate has worked at. edit any typos or errors in the companies.")
    experienceTimePeriods: List[str] = Field(description="List of time periods in 'Month Year' format, e.g., 'Sep 2014 - Jun 2018', if not mentioned, output '-'")
    experienceYears: float = Field(description="The total years of experience of the candidate- calculate total experience in years based on experienceTimePeriods, add months e.g., 3, 0.5")
    educationInstitutes: List[str] = Field(description="The institutes the candidate has studied at. edit any typos or errors in the institutes.")
    degrees: List[str] = Field(description="The degrees the candidate has obtained. edit any typos or errors in the degrees.")
    educationTimePeriods: List[str] = Field(description="List of time periods in 'Month Year' format, e.g., 'Sep 2014 - Jun 2018', if not mentioned, output '-'")
    educationYears: float = Field(description="The total years of education of the candidate- calculate total Education in years based on educationTimePeriods, add months e.g., 3, 0.5")
    skills: List[str] = Field(description="The skills of the candidate. edit any typos or errors in the skills.")
    projects: List[str] = Field(description="The projects the candidate has worked on. edit any typos or errors in the projects.")
    certificationsOrAchievements: List[str] = Field(description="The certifications or achievements of the candidate. edit any typos or errors in the certifications or achievements.")
    links: List[str] = Field(description="The links of the candidate. edit any typos or errors in the links.")

class ParsedResume(BaseModel):
    parsed_resume: Resume
    attribute_scores: AttributeScores

class WeightageDict(BaseModel):
    skills_score: float = Field(description="The weightage for the skills attribute as per the criteria mentioned in the prompt")
    experience_score: float = Field(description="The weightage for the experience attribute as per the criteria mentioned in the prompt")
    qualifications_score: float = Field(description="The weightage for the qualifications attribute as per the criteria mentioned in the prompt")
    project_score: float = Field(description="The weightage for the project attribute as per the criteria mentioned in the prompt")

class RescreeningResume(BaseModel):
    attribute_scores: AttributeScores
    weightage_dict: WeightageDict
