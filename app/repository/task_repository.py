
"Task model CRUD operations"
from beanie import PydanticObjectId
import logging
from typing import Literal, Dict, Any
from pydantic import Field, BaseModel
from app.models.task_model import TaskSchema as task_schema
from app.utils.http_responses import Responses

logging.basicConfig(level=logging.INFO)

class FetchTask(BaseModel):
    task_id: PydanticObjectId = Field(alias="_id")
    chat_id: str
    task_type: str
    status: str
    metadata: Any

class TaskRepository:
    "CRUD operations for task model"

    @staticmethod
    async def get_task(task_id: str, chat_id: str):
        "Get task"
        try:
            task = await task_schema.find_one({"_id": PydanticObjectId(task_id), "chat_id": chat_id}, projection_model=FetchTask)
            fetched_task = task.model_dump()
            fetched_task['task_id'] = str(fetched_task['task_id'])
            return fetched_task
        except Exception as e:
            logging.error("Error during getting task: %s", str(e))
            return Responses.error(500, message=str(e))
            
    @staticmethod
    async def insert_task(user_id: str, chat_id: str, task_type: Literal["jd_generation","resume_parsing","rescreening","cognitive_assessment","is_assessment", "assessment_generation","sending_mail"], status: Literal["PENDING","SUCCESS","FAILED"],metadata: Dict = None):
        "Create new task"
        try:
            task = task_schema(user_id=PydanticObjectId(user_id), chat_id=chat_id, task_type=task_type, status=status, metadata=metadata)
            await task.insert()
            logging.info("Task inserted successfully: %s", str(task.id))
            return str(task.id)
        except Exception as e:
            logging.error("Error during inserting task: %s", str(e))
            return Responses.error(500, message=str(e))
        
    @staticmethod
    async def update_task(task_id: str, update_data: Dict):
        """Update task with custom data"""
        try:
            await task_schema.find_one({"_id": PydanticObjectId(task_id)}).update({"$set": update_data})
            logging.info("Task updated successfully: %s", str(task_id))
            return True
        except Exception as e:
            logging.error("Error during updating task: %s", str(e))
            return Responses.error(500, message=str(e))        
        
    @staticmethod
    async def update_task_status(task_id: str, status: Literal["PENDING","SUCCESS","FAILED"] = None):
        "Update task status"
        try:
            await task_schema.find_one({"_id": PydanticObjectId(task_id)}).update({"$set": {"status": status}})
            logging.info("Task updated successfully: %s", str(task_id))
            return True
        except Exception as e:
            logging.error("Error during updating task: %s", str(e))
            return Responses.error(500, message=str(e))
        
    @staticmethod
    async def update_task_metadata(task_id: str):
        "Update task metadata"
        try:
            await task_schema.find_one({"_id": PydanticObjectId(task_id)}).update({"$inc": {"metadata.parsed_resumes": 1}})
            logging.info("Task updated successfully: %s", str(task_id))
            return True
        except Exception as e:
            logging.error("Error during updating task: %s", str(e))
            return Responses.error(500, message=str(e))