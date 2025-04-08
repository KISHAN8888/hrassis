import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class AIConfig(BaseSettings):
    openai_key: str = os.getenv("OPENAI_API_KEY")

class DatabaseConfig(BaseSettings):
    if os.getenv("MODE") == "STAGING":
        db_url: str = os.getenv("MONGODB_URL_STAGING")
        db_name: str = os.getenv("MONGODB_DB_NAME_STAGING")
    else:
        db_url: str = os.getenv("MONGODB_URL")
        db_name: str = os.getenv("MONGODB_DB_NAME")
            
class OAuthConfig(BaseSettings):
    client_id: str = os.getenv("OAUTH_CLIENT_ID")
    client_secret: str = os.getenv("OAUTH_CLIENT_SECRET")
    redirect_url: str = os.getenv("OAUTH_REDIRECT_URI")
    fe_redirect_url: str = os.getenv("FE_REDIRECT_URI")

class AuthConfig(BaseSettings):
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_expiration_hours: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24").strip('"'))

class ResumeConfig(BaseSettings):
    resume_path: str = os.getenv("RESUME_UPLOAD_DIR")

class Settings(BaseSettings):
    ai: AIConfig = AIConfig()
    db: DatabaseConfig = DatabaseConfig()
    oauth: OAuthConfig = OAuthConfig()
    auth: AuthConfig = AuthConfig()
    resume: ResumeConfig = ResumeConfig()
        
env_config = Settings()