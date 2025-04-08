from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import logging
from app.config.env_config import env_config
from beanie import init_beanie

logging.basicConfig(level=logging.INFO)

async def start_db():
    logging.info("Starting database connection to %s", env_config.db.db_name) 
    logging.info("Connected to the DB URL:%s",env_config.db.db_url)
    client = AsyncIOMotorClient(env_config.db.db_url)
    await init_beanie(
        database=client[env_config.db.db_name],
        document_models=[
            "app.models.conversations_model.ConversationSchema", "app.models.jd_model.JobDescriptionSchema",
            "app.models.resume_model.ResumeSchema", "app.models.task_model.TaskSchema",
            "app.models.user_model.UserSchema", "app.models.order_model.OrderSchema",
            "app.models.assessment_model.AssessmentTaskSchema",
        ]
    )

def chat_db():
    logging.info("Chat database connection to %s", env_config.db.db_name)
    client = MongoClient(env_config.db.db_url)
    db = client[env_config.db.db_name]
    return db

def close_db():
    client = AsyncIOMotorClient(env_config.db.db_url)
    client.close()