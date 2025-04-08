"Resume model CRUD operations - Only inserted implemented as of now..."
from typing import Literal, Dict, List, Any
import logging
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from datetime import datetime, timezone
from app.models.resume_model import ResumeSchema as resume_schema
from app.utils.http_responses import Responses
from bson import DBRef
logging.basicConfig(level=logging.INFO)

class GetResumesByChatId(BaseModel):
    resume_id: PydanticObjectId = Field(alias="_id")
    chat_id: str
    parsed_resume: Dict
    attribute_scores: Dict
    status: str

class ResumeRepository:
    "Resume model CRUD operations"
    @staticmethod
    async def get_resumes_by_chat_id(chat_id: str, user_id: str) -> List[Dict]:
        "Get all resumes by chat ID"
        logging.info("Getting resumes by chat ID: %s", chat_id)
        resumes = await resume_schema.find(resume_schema.chat_id == chat_id, resume_schema.user_id.id == PydanticObjectId(user_id), projection_model=GetResumesByChatId, fetch_links=True).to_list()
        resumes_list = [resume.model_dump() for resume in resumes]
        for resume in resumes_list:
            resume['resume_id'] = str(resume['resume_id'])
            # resume['jd_id'] = str(resume['jd_id'])
        return resumes_list
    
    @staticmethod
    async def insert_resume(user_id: str, chat_id: str, jd_id: str, parsed_resume: Dict, attribute_scores: Dict, candidate_resume: str, token_usage: Dict, cost: Dict, status: Literal["ACCEPTED","REJECTED","PENDING"] = "PENDING"):
        "Create a resume"
        resume = resume_schema(user_id=PydanticObjectId(user_id), chat_id=chat_id, jd_id=PydanticObjectId(jd_id), parsed_resume=parsed_resume, attribute_scores=attribute_scores, candidate_resume=candidate_resume, token_usage=token_usage, cost=cost, status=status)
        await resume.insert()
        logging.info("Resume inserted successfully: %s", str(resume.id))
        return str(resume.id)
    
    @staticmethod
    async def update_resume(resume_id: str, attribute_scores: Dict, token_usage: Dict, cost: Dict):
        "Update a rescreened resume"
        try:
            update_query = {"$set": {"attribute_scores": attribute_scores}, 
                            "$inc": {"token_usage.prompt_tokens": token_usage['prompt_tokens'], "token_usage.completion_tokens": token_usage['completion_tokens'], "token_usage.total_tokens": token_usage['total_tokens'],
                                     "cost.prompt_cost": cost['prompt_cost'], "cost.completion_cost": cost['completion_cost'], "cost.total_cost": cost['total_cost']}}
            resume = await resume_schema.find_one({"_id": PydanticObjectId(resume_id)}).update(update_query)
            if not resume:
                logging.error("Resume not found for ID: %s", resume_id)
                return Responses.error(404, message="Resume not found")
            
            logging.info("Resume updated successfully: %s", resume_id)
            return True
        except Exception as e:
            logging.error("Error updating resume: %s", str(e))
            return Responses.error(500, message=str(e))
        
    @staticmethod
    async def update_resume_status(status: Literal["ACCEPTED", "REJECTED", "PENDING"], user_id: str, jd_id: str, resume_id: str):
        """Update a rescreened resume"""
        try:
            updated_resume = await resume_schema.find_one({"_id": PydanticObjectId(resume_id)}).update({"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}})
            if not updated_resume:
                logging.error("Job description not found: %s", resume_id)
                return None
            updated_resume = await resume_schema.find_one({"_id": PydanticObjectId(resume_id)},fetch_links=True)
            updated_resume = updated_resume.model_dump()
            return updated_resume
        except Exception as e:
            logging.error("Error updating resume: %s", str(e))
            return Responses.error(500, message=str(e))                

    
    @staticmethod
    async def get_resume_by_id(resume_id: str):
        "Get a resume by its ID."
        resume = await resume_schema.find_one({"_id": PydanticObjectId(resume_id)},fetch_links=True,nesting_depth=1)
        if not resume:
            logging.error("Resume not found: %s", resume_id)
            return None
        resume = resume.model_dump()
        # print("Resumesss:DBAgain",resume)
        return resume
    

    @staticmethod
    async def get_resumes_by_ids(resume_ids: List[str]) -> List[Dict]:
       
        try:
            print("resume_ids", resume_ids)
            resume_ids_object_ids = [PydanticObjectId(resume_id) for resume_id in resume_ids]
            pipeline = [
                {
                    "$match": {
                        "_id": {"$in": resume_ids_object_ids}  
                    }
                },
                {
                    "$project": {
                            "_id": 0,
                            "Name": "$parsed_resume.Name",
                            "Email": "$parsed_resume.Email"
                        }
                }
            ]

            result = await resume_schema.aggregate(pipeline).to_list()
            for item in result:
                if '_id' in item:
                    item['_id'] = str(item['_id'])  # Convert ObjectId to string

            return result

        except Exception as e:
            logging.error("Error retrieving resumes: %s", str(e))
            return False
        
        
    async def get_accepted_resume(jd_id: str, user_id: str) -> Dict:
        try:
            resumes = await resume_schema.find(resume_schema.jd_id.id== PydanticObjectId(jd_id), resume_schema.user_id.id==PydanticObjectId(user_id), {"status":"ACCEPTED"}, projection_model=GetResumesByChatId).to_list()
            if not resumes:
                logging.error("Resume not found: %s", jd_id)
                return None
            
            resumes_list = [resume.model_dump() for resume in resumes]
            for resume in resumes_list:
                resume['resume_id'] = str(resume['resume_id'])
                # resume['jd_id'] = str(resume['jd_id'])
            return resumes_list
            
        except Exception as e:
            logging.error("Error retrieving accepted resume: %s", str(e))
            return False