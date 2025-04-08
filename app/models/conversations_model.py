from pydantic import Field, BaseModel
from beanie import Document, UnionDoc, Link
from datetime import datetime, timezone
from typing import List, Literal
from app.models.user_model import UserSchema

# --------------------------- Conversation Between HR and Candidate ---------------------------
class MessageSchema(BaseModel):
    message_id: str
    subject: str
    content: str
    status: bool = False
    sent_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversationSchema(Document):
    user_id: Link[UserSchema]
    chat_id: str
    user_email: str
    candidate_email: str
    mode: Literal['Email','WhatsApp']
    type: str
    messages: List[MessageSchema] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name="conversations"
        indexes=['chat_id']
    
# --------------------------- AI Analysis and Replies of Candidate ---------------------------
class ConversationTokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ConversationCost(BaseModel):
    prompt_cost: float
    completion_cost: float
    total_cost: float

class AIConversationSchema(UnionDoc):
    user_id: Link[UserSchema]
    chat_is: str
    canidate_email: str
    token_usuage: ConversationTokenUsage
    total_cost: ConversationCost
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    class Settings: 
        name='aiReplies'
        class_id="_class_id"
        indexes=[('chat_id',1),('candidate_email',1)]

class SentimentSchema(Document):
    sentiment: Literal["Approved","Disapproved","Pending"]
    reason: str
    ai_reply: str
    ai_reply_summary: str
    class Settings:
        name="sentiment"
        union_doc=AIConversationSchema

class TaskExtractionSchema(Document):
    task_info: str
    project_links: List[str]
    class Settings:
        name="task_extraction"
        union_doc=AIConversationSchema
    
class ReplySchema(Document):
    email_summary: str
    ai_reply: str
    ai_reply_summary: str
    class Settings:
        name="reply"
        union_doc=AIConversationSchema

