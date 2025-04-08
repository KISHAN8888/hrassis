from typing_extensions import TypedDict, Annotated, List, Dict, Optional, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

# ------------------------------------------- Main State ----------------------------------------------
class MainState(TypedDict):
    user_id: str
    chat_id: str
    summary: str
    # messages: Annotated[List[str], add_messages]
    messages: Annotated[List[BaseMessage], add_messages]
    resume_parsed: Literal[True, False, None]
    created_jd_id: str
    parsed_jd_id: str
    selected_route: Literal["jd_assistant", "rp_assistant", "general_assistant", "db_assistant", "email_assistant", "assessment_assistant"]
    task_id: Optional[str] = None
    email_type: Literal['task_link', 'task_attachment', 'offer_letter', 'rejection_letter', 'meet_link_email', 'custom_email'] = None
    email_material: str = None
    mail_attachment: Literal[True, False] = False
    db_query_result: Dict = Field(default_factory=dict)
    # Assessment specific fields
    assessment_id: Optional[str] = None
    assessment_status: Literal["pending", "processing", "completed", "published", "failed", None] = None

class MainOutputState(TypedDict):
    messages: Annotated[List[str], add_messages]
    selected_route: Literal["jd_assistant", "rp_assistant", "general_assistant", "db_assistant", "email_assistant", "assessment_assistant"]
    resume_parsed: Literal[True, False, None]
    task_id: Optional[str] = None
    created_jd_id: str
    parsed_jd_id: str
    db_query_result: Dict = Field(default_factory=dict)
    email_type: Literal['task_link', 'task_attachment', 'offer_letter', 'rejection_letter', 'meet_link_email', 'custom_email'] = None
    email_material: str = None
    mail_attachment: Literal[True, False] = False
    # Assessment specific fields
    assessment_id: Optional[str] = None
    assessment_status: Literal["pending", "processing", "completed", "published", "failed", None] = None

# ------------------------------------------- RP Node ----------------------------------------------
class RpStructuredOutput(BaseModel):
    """Always use this tool to structure your response to the user."""
    messages: str = Field(..., description="Reply for user message or weightage dict that will be used by your tool")
    resume_parsed: Literal[True, False, None] = Field(..., description="Indicating if resumes are parsed or not")

# ------------------------------------------- Email Node ----------------------------------------------
class EmailStructuredOutput(BaseModel):
    """Always use this tool to structure your response to the user."""
    messages: str = Field(..., description="Reply for user message asking the type of email to be sent")
    email_type: Literal['task_link', 'task_attachment', 'offer_letter', 'rejection_letter', 'meet_link_email', 'custom_email'] = Field(None, description="Indicating the type of email to be sent")

# ------------------------------------------- Assessment Node ----------------------------------------------
class AssessmentStructuredOutput(BaseModel):
    """Always use this tool to structure your response related to assessment tasks."""
    messages: str = Field(..., description="Reply for user message about assessment generation or customization")
    assessment_id: Optional[str] = Field(None, description="ID of the assessment task if one was generated or updated")
    assessment_status: Literal["pending", "processing", "completed", "published", "failed", None] = Field(None, description="Status of the assessment task")

# ------------------------------------------- Entry Route ----------------------------------------------
class RouterResponse(BaseModel):
    selected_route: Literal["jd_assistant", "rp_assistant", "general_assistant", "db_assistant", "email_assistant", "assessment_assistant"] = Field(..., description="The assistant to route the user to based on their message")






