import logging
from typing import Dict, List
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from app.models.jd_model import JobDescriptionSchema as jd_schema

logging.basicConfig(level=logging.INFO)


class GetJobDescription(BaseModel):
    jd_id: PydanticObjectId = Field(alias="_id")
    job_description: Dict = Field(alias="job_description")

class GetCandidateStatus(BaseModel):
    jd_id: PydanticObjectId = Field(alias="_id")
    rejected: list = Field(alias="rejected")
    accepted: list = Field(alias="accepted")

class JobDescriptionRepository:
    "CRUD operations for job descriptions"
    @staticmethod
    async def get_jd_by_id(jd_id: str) -> Dict:
        "Get a job description by its ID."
        jd = await jd_schema.find_one({"_id": PydanticObjectId(jd_id)}, projection_model=GetJobDescription)
        if not jd:
            logging.error("Job description not found: %s", jd_id)
            return None
        job_description = jd.model_dump()
        job_description['jd_id'] = str(job_description['jd_id'])
        return job_description
    
    @staticmethod
    async def get_jd_by_chat_id(chat_id: str, user_id: str) -> Dict:
        "Get a job description by its chat ID."
        jd = await jd_schema.find(jd_schema.chat_id == chat_id, jd_schema.user_id.id == PydanticObjectId(user_id), projection_model=GetJobDescription).sort(-jd_schema.created_at).first_or_none()
        if not jd:
            logging.error("Job description not found: %s", chat_id)
            return None
        job_description = jd.model_dump()
        job_description['jd_id'] = str(job_description['jd_id'])
        return job_description
    
    @staticmethod
    async def get_all_jd(user_id: str) -> Dict:
        "Get all job descriptions by their user ID."
        logging.info("Getting all job descriptions by user ID: %s", user_id)
        jd_list = await jd_schema.find(jd_schema.user_id.id == PydanticObjectId(user_id), projection_model=GetJobDescription).to_list()
        if not jd_list:
            logging.error("Job description not found for user ID: %s", user_id)
            return None
        job_descriptions = [jd.model_dump() for jd in jd_list]
        for jd in job_descriptions:
            jd['jd_id'] = str(jd['jd_id'])
        return job_descriptions
        
    @staticmethod
    async def insert_jd(user_id: str, chat_id: str, job_description: Dict, token_usage: Dict, cost: Dict, jd_inputs: Dict = None, is_generated: bool = True) -> str:
        "Insert a job description into the database."  
        try: 
            jd = jd_schema(user_id=PydanticObjectId(user_id), chat_id=chat_id, jd_inputs=jd_inputs, job_description=job_description, token_usage=token_usage, cost=cost, is_generated=is_generated)
            await jd.insert()
            logging.info("Job description inserted successfully: %s", str(jd.id))
            return str(jd.id)
        except Exception as e:
            logging.error("Error inserting job description: %s", str(e))
            return None
        

    @staticmethod
    async def update_publish_status(jd_id: str, chat_id: str, user_id: str) -> Dict:
        "Updating job description."
        try:
            logging.info("Publishing job description: %s", jd_id)
            await jd_schema.find(jd_schema.chat_id == chat_id, jd_schema.user_id.id == PydanticObjectId(user_id), jd_schema.is_generated == True, jd_schema.id != PydanticObjectId(jd_id)).delete()
            await jd_schema.find_one({"_id": PydanticObjectId(jd_id)}).update({"$set": {"is_publish": True}})
            return True
        except Exception as e:
            logging.error("Error publishing job description: %s", str(e))
            return None
        
        
    @staticmethod
    async def update_candidate_status(jd_id: str, chat_id: str, user_id: str, status: str, resume_ids: List[str]) -> Dict:
        "Updating job description."
        try:
            await jd_schema.find(jd_schema.chat_id == chat_id, jd_schema.user_id.id == PydanticObjectId(user_id), jd_schema.is_generated == True, jd_schema.id != PydanticObjectId(jd_id)).delete()
            if(status == "ACCEPTED"):
                await jd_schema.find_one({"_id": PydanticObjectId(jd_id)}).update({"$addToSet": {"accepted": {"$each": [PydanticObjectId(resume_id) for resume_id in resume_ids]}}})
                return True
            elif(status == "REJECTED"):
                print("resume_id", resume_ids)
                await jd_schema.find_one({"_id": PydanticObjectId(jd_id)}).update({"$addToSet": {"rejected": {"$each": [PydanticObjectId(resume_id) for resume_id in resume_ids]}}})
                return True
            else:
                return False
        except Exception as e:
            logging.error("Error publishing job description: %s", str(e))
            return None

    @staticmethod
    async def get_candidate_status_by_jd_id(jd_id: str) -> Dict:
        "Get a job description by its ID."
        jd = await jd_schema.find_one({"_id": PydanticObjectId(jd_id)}, projection_model=GetCandidateStatus)
        if not jd:
            logging.error("Job description not found: %s", jd_id)
            return None
        job_description = jd.model_dump()
        job_description['jd_id'] = str(job_description['jd_id'])
        return job_description