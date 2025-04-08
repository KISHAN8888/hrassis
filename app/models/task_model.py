from typing import Literal, Optional
from beanie import Document, Link
from datetime import datetime, timezone
from pydantic import Field, BaseModel
from app.models.user_model import UserSchema

class MetaDataSchema(BaseModel):
    uploaded_resumes: int
    parsed_resumes: int

class TaskSchema(Document):
    user_id: Link[UserSchema]
    chat_id: str
    task_type: Literal["jd_generation","resume_parsing","rescreening","cognitive_assessment","is_assessment", "assessment_generation","sending_mail"]
    status: Literal["PENDING","SUCCESS","FAILED"] = "PENDING"
    metadata: Optional[MetaDataSchema] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name="taskInfo"
        indexes=['chat_id']
        is_null=False

