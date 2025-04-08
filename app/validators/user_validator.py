from pydantic import BaseModel
from typing import Optional

class SignUpValidator(BaseModel):
    email: str
    name: str
    company_name: Optional[str] = None
    password: str
    
class SignInValidator(BaseModel):
    email: str
    password: str