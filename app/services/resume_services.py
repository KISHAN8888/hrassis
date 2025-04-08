import logging, json
from typing import Dict, List, Any
from app.helpers.ai_helper import OpenAIClient
from app.helpers.resume_helper import ResumeHelper as resume_helper
from app.services.prompts.resume_prompts import RP_SYSTEM_PROMPT, RP_USER_PROMPT, RS_SYSTEM_PROMPT, RS_USER_PROMPT
from app.services.model_format.resume_format import ParsedResume, RescreeningResume
from app.repository.resume_repository import ResumeRepository as resume_db
from app.repository.user_repository import UserRepository as user_db
from app.repository.jd_repository import JobDescriptionRepository as jd_db

logging.basicConfig(level=logging.INFO)

class ResumeService:
    "Parse and scores resumes against the job descriptions"
    def __init__(self, user_id: str, chat_id: str, jd_id: str, resume_file: str):
        self.user_id = user_id
        self.chat_id = chat_id
        self.jd_id = jd_id
        self.resume_file = resume_file
        self.client = OpenAIClient()
        
    async def parse_resume(self) -> Dict:
        "Parse the resume and return the candidate's name and _id"
        try:
            logging.info("Starting resume parsing for %s", self.resume_file)
            job_description = await jd_db.get_jd_by_id(self.jd_id)
            candidate_resume = resume_helper.extract_text_from_file_path(self.resume_file)
            if not candidate_resume:
                logging.error("Resume text is empty for %s", self.resume_file)
                return None
            
            logging.info("Sending resume to AI model for parsing and scoring")
            user_prompt = RP_USER_PROMPT.format(candidate_resume=candidate_resume, job_description=job_description['job_description'])
            response, token_usage, cost = await self.client.openai_model_response(RP_SYSTEM_PROMPT, user_prompt, ParsedResume, model="o3-mini")
            result = json.loads(response)
            attribute_scores = result['attribute_scores']
            attribute_scores['overall_score'] = resume_helper.calculate_overall_score(attribute_scores, {"skills_score": 25, "experience_score": 25, "qualifications_score": 25, "project_score": 25})

            resume_id = await resume_db.insert_resume(self.user_id, self.chat_id, self.jd_id, result['parsed_resume'], attribute_scores, candidate_resume, token_usage, cost, "PENDING")
            await user_db.update_user_token_cost(self.user_id, token_usage['total_tokens'], cost['total_cost'], "resume")
            logging.info("Resume parsed and saved in db successfully: %s", resume_id)
            return {"name": result['parsed_resume']['Name'], "resume_id": resume_id}
        except Exception as e:
            logging.error("Error parsing resume: %s", e)
            return None
        
class RescreeningService:
    "Rescreening the resumes against the job descriptions"
    def __init__(self, user_id: str, resume_id: str, jd_id: str, custom_parameters: List[str], candidate_resume: Any):
        self.user_id = user_id
        self.resume_id = resume_id
        self.jd_id = jd_id
        self.custom_parameters = custom_parameters
        self.candidate_resume = candidate_resume
        self.client = OpenAIClient()
        
    async def rescreen_resume(self):
        "Parse the resume and return the candidate's name and _id"
        try:
            if not self.candidate_resume:
                logging.error("Candidate resumes are empty")
                return None
            
            logging.info("Sending resume to AI model for rescreening candidate...")
            job_description = await jd_db.get_jd_by_id(self.jd_id)
            user_prompt = RS_USER_PROMPT.format(candidate_resume=self.candidate_resume, custom_parameters=self.custom_parameters, job_description=job_description['job_description'])
            response, token_usage, cost = await self.client.openai_model_response(RS_SYSTEM_PROMPT, user_prompt, RescreeningResume, model="o3-mini")
            rescreening_result = json.loads(response)
            attribute_scores = rescreening_result['attribute_scores']
            attribute_scores['overall_score'] = resume_helper.calculate_overall_score(attribute_scores, rescreening_result['weightage_dict'])

            await resume_db.update_resume(self.resume_id, attribute_scores, token_usage, cost)
            await user_db.update_user_token_cost(self.user_id, token_usage['total_tokens'], cost['total_cost'], "resume")
            logging.info("Resume rescreened and saved in db successfully: %s", self.resume_id)
            return {"resume_id": self.resume_id}
        except Exception as e:
            logging.error("Error parsing resume: %s", e)
            return None
     
# ----------------- TESTING -----------------
# import os
# import asyncio
# from motor.motor_asyncio import AsyncIOMotorClient
# from app.config import start_db

# async def main():
#     try:
#         await start_db()
#         # Read job description from file (synchronously for simplicity)
#         file_path = "/Users/aastharathi/Downloads/Chatur_1.0/resumes/CVADV.AASHISH.pdf"

#         # Create ResumeParser instance asynchronously.
#         parser = ResumeService("67d44a9e90a12565210d0a2a", "chat_id_example", "67d7de5cadbb6d9ec209273e", file_path)
#         candidate_name = await parser.parse_resume()
#         logging.info(f"Candidate name: {candidate_name}")

#     except Exception as e:
#         logging.error(f"Error occurred in main: {e}")


# async def rescreen_resume():
#     await start_db()
#     user_id = "67d44a9e90a12565210d0a2a"
#     resume_id = "67d7e40337ca57afca2cd8bc"
#     jd_id = "67d7de5cadbb6d9ec209273e"
#     custom_parameters = ["candidate have supreme court experience"]
#     candidate_resume = "Hieeee"
#     parser = RescreeningService(user_id, resume_id, jd_id, custom_parameters, candidate_resume)
#     resume_id = await parser.parse_resume()
#     logging.info(f"Resume ID: {resume_id}")


# if __name__ == "__main__":
#     asyncio.run(rescreen_resume())