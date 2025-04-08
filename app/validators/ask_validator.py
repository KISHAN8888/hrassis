from pydantic import BaseModel

class AskValidator(BaseModel):
    message: str
    chat_id: str