from pydantic import BaseModel, Field
from typing import Literal, List

class SentimentReceiveResponse(BaseModel):
    sentiment: Literal["Approved","Disapproved","Pending"]
    reason: str = Field(description= "Short summary of candidate's last email")
    ai_reply: str = Field(description= "Full professional email response or empty if insufficient info")
    ai_reply_summary: str = Field(description= "2-3 line summary of the reply or mention insufficient info")

class TaskAttachmentReceiveResponse(BaseModel):
    task_info: str = Field(description= "Any relevant text information from the email content focusing explicitly on explaining the given task. If nothing relevant is found, return an empty string.")
    project_links: List[str] = Field(description= "A list of URLs related to the candidate's projects. If no links are found, return an empty list")

class ReplyEmailResponse(BaseModel):
    email_summary: str = Field(description= "Short summary of candidate's last email")
    ai_reply: str = Field(description= "Full professional email response or empty if insufficient info")
    ai_reply_summary: str = Field(description= "2-3 line summary of the reply or mention insufficient info")