from typing import Literal, Optional
from beanie import Link,Document
from datetime import datetime, timezone
from pydantic import Field, BaseModel
from app.models.user_model import UserSchema

# 5 dollar = 1M gpt-token
class OrderSchema(Document):
    user_id: Link[UserSchema]
    credit: Optional[float]
    amount: float
    status: Literal["pending", "success", "failed"] = "pending"
    order_id: str
    payment_source:str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name="order"
        indexes=['order_id']
    

