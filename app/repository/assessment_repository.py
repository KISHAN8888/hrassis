import logging
from typing import Dict, Optional, List
import datetime
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from app.models.assessment_model import AssessmentTaskSchema as assessment_schema

logging.basicConfig(level=logging.INFO)


class GetAssessmentTask(BaseModel):
    """Model for retrieving assessment task data"""
    task_id: PydanticObjectId = Field(alias="_id")
    assessment_task: Dict = Field(alias="assessment_task")
    assessment_inputs: Dict = Field(alias="assessment_inputs")

class AssessmentRepository:
    """CRUD operations for assessment tasks"""
    
    @staticmethod
    async def get_assessment_by_id(task_id: str) -> Dict:
        """Get an assessment task by its ID."""
        task = await assessment_schema.find_one({"_id": PydanticObjectId(task_id)}, projection_model=GetAssessmentTask)
        if not task:
            logging.error("Assessment task not found: %s", task_id)
            return None
        assessment_task = task.model_dump()
        assessment_task['task_id'] = str(assessment_task['task_id'])
        return assessment_task
    
    @staticmethod
    async def get_assessment_by_chat_id(chat_id: str, user_id: str) -> Dict:
        """Get an assessment task by its chat ID."""
        task = await assessment_schema.find(
            assessment_schema.chat_id == chat_id, 
            assessment_schema.user_id.id == PydanticObjectId(user_id),
            projection_model=GetAssessmentTask
        ).sort(-assessment_schema.created_at).first_or_none()
        
        if not task:
            logging.error("Assessment task not found for chat ID: %s", chat_id)
            return None
        
        assessment_task = task.model_dump()
        assessment_task['task_id'] = str(assessment_task['task_id'])
        return assessment_task
    
    @staticmethod
    async def get_user_assessments(user_id: str) -> List[Dict]:
        """Get all assessment tasks by user ID."""
        logging.info("Getting all assessment tasks by user ID: %s", user_id)
        
        task_list = await assessment_schema.find(
            assessment_schema.user_id.id == PydanticObjectId(user_id),
            projection_model=GetAssessmentTask
        ).to_list()
        
        if not task_list:
            logging.info("No assessment tasks found for user ID: %s", user_id)
            return False
        
        assessment_tasks = [task.model_dump() for task in task_list]
        for task in assessment_tasks:
            task['task_id'] = str(task['task_id'])
        
        return assessment_tasks
        
    @staticmethod
    async def insert_assessment(user_id: str, chat_id: str, assessment_task: Dict, token_usage: Dict, cost: Dict, assessment_inputs: Dict) -> str:
        """Insert an assessment task into the database."""  
        try: 
            logging.info(f"Inserting assessment task for user ID: {user_id}, chat ID: {chat_id}")
            logging.info("Assessment task data: %s", assessment_task)
            logging.info("Assessment inputs data: %s", assessment_inputs)
            logging.info("Token usage data: %s", token_usage)
            logging.info("Cost data: %s", cost)
            task = assessment_schema(
                user_id=PydanticObjectId(user_id),
                chat_id=chat_id,
                assessment_task=assessment_task,
                assessment_inputs=assessment_inputs,
                token_usage=token_usage,
                cost=cost
            )

            logging.info("task isssssssss", task)
            await task.insert()
            logging.info("Assessment task inserted successfully: %s", str(task.id))
            return str(task.id)
        except Exception as e:
            logging.error("Error inserting assessment task: %s", str(e))
            return None
    
    @staticmethod
    async def update_assessment(task_id: str, assessment_task: Dict, token_usage: Dict, cost: Dict, assessment_inputs: Dict) -> str:
        """Update an existing assessment task."""
        try:
            task = await assessment_schema.find_one({"_id": PydanticObjectId(task_id)})
            if not task:
                logging.error("Assessment task not found for update: %s", task_id)
                return None
                
            task.assessment_task = assessment_task
            task.assessment_inputs = assessment_inputs
            task.token_usage = token_usage
            task.cost = cost
            task.updated_at = datetime.datetime.utcnow()
            
            await task.save()
            logging.info("Assessment task updated successfully: %s", str(task.id))
            return str(task.id)
        except Exception as e:
            logging.error("Error updating assessment task: %s", str(e))
            return None
    
    @staticmethod
    async def update_publish_status(task_id: str, chat_id: str, user_id: str) -> bool:
        """Publish an assessment task and remove other generated tasks for the same chat."""
        try:
            logging.info("Publishing assessment task: %s", task_id)
            
            # Delete other generated tasks for the same chat
            await assessment_schema.find(
                assessment_schema.chat_id == chat_id,
                assessment_schema.user_id.id == PydanticObjectId(user_id),
                assessment_schema.id != PydanticObjectId(task_id)
            ).delete()
            
            # Mark this task as published
            await assessment_schema.find_one({"_id": PydanticObjectId(task_id)}).update({"$set": {"is_published": True}})
            return True
        except Exception as e:
            logging.error("Error publishing assessment task: %s", str(e))
            return None
            
    @staticmethod
    async def delete_assessment(task_id: str) -> bool:
        """Delete an assessment task by ID."""
        try:
            task = await assessment_schema.find_one({"_id": PydanticObjectId(task_id)})
            if not task:
                logging.error("Assessment task not found for deletion: %s", task_id)
                return False
                
            await task.delete()
            logging.info("Assessment task deleted successfully: %s", task_id)
            return True
        except Exception as e:
            logging.error("Error deleting assessment task: %s", str(e))
            return False
        
        
    @staticmethod
    async def get_assessment_by_user_id(assessment_id:str,user_id: str) -> List[Dict]:
        try:
            logging.info("Getting assessment by user id: %s", user_id)
            assessment = await assessment_schema.find_one({
                "_id":PydanticObjectId(assessment_id),
                assessment_schema.user_id.id: PydanticObjectId(user_id),  
            }, projection_model=(GetAssessmentTask))
            if not assessment:
                return False
            assessment_is = assessment.model_dump()
            assessment_is['task_id'] = str(assessment_is['task_id'])
            return assessment_is
        
        except Exception as e:
            logging.error("Error in get_assessment_by_user_id: %s", str(e))
            return False
        