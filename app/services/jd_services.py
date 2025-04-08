"AI file for creating job description and editing one in structure format, if uploaded one at the time of resume parsing"
import logging
from typing import Dict
import json
from app.services.model_format.jd_format import JobDescription
from app.services.prompts.jd_prompts import JD_SYSTEM_PROMPT, JD_USER_PROMPT
from app.services.prompts.jd_prompts import EDIT_JD_SYSTEM_PROMPT, EDIT_JD_USER_PROMPT
from app.helpers.ai_helper import OpenAIClient
from app.repository.jd_repository import JobDescriptionRepository as jd_db
from app.repository.user_repository import UserRepository as user_db
from app.utils.http_responses import Responses

logging.basicConfig(level=logging.INFO)

class JobDescriptionGenerator:
    '''
    Generates job description given input data, to undertand dataTypes look in pydantic Schema in models[jobDescription] - 
        job_title - Required
        company_name -  Required
        department -  Required
        location - Required
        Job_type - Literal["Online", "Offline", "Hybrid"] - Required
        skills - Optional
        qualifications - Optional
        experience - Optional
        salary_range - Optional
        tone - Optional
        about_url - Optional
        language - Required
    '''
    def __init__(self, input_data: Dict, user_id: str, chat_id: str):
        self.input_data = input_data
        self.user_id = user_id
        self.chat_id = chat_id
        self.client = OpenAIClient()

    async def generate(self) -> str:
        """
        Asynchronously generates a job description using a `o3-mini` model.
        Returns: Tuple containing the job description, token usage, and cost.
        """
        try:
            # Generation
            logging.debug("Sending request to LLM model")
            formatted_prompt = JD_USER_PROMPT.format(**self.input_data)
            response, token_usage, cost = await self.client.openai_model_response(JD_SYSTEM_PROMPT, formatted_prompt, JobDescription, "o3-mini")
            logging.info("Successfully generated job description")
            job_description = json.loads(response)
            jd_id = await jd_db.insert_jd(user_id=self.user_id, chat_id=self.chat_id, job_description=job_description, token_usage=token_usage, cost=cost, jd_inputs=self.input_data)
            await user_db.update_user_token_cost(self.user_id, token_usage['total_tokens'], cost['total_cost'], "jd")
            logging.info("Successfully inserted job description and updated user token cost")
            return jd_id
        except Exception as e:
            logging.error("Error generating job description: %s", str(e))
            return Responses.error(500, "Error generating job description")

class JobDescriptionOptimiser:
    "To change the structe of job description received during resume parsing"
    def __init__(self, job_description: str, user_id: str, chat_id: str):
        self.job_description = job_description
        self.user_id = user_id
        self.chat_id = chat_id
        self.client = OpenAIClient()

    async def optimise(self) -> str:
        """
        Asynchronously optimises a job description using a `gpt-4o-mini` model.
        Returns: Tuple containing the optimised job description, token usage, and cost.
        """
        try:
            # Generation
            logging.debug("Sending request to LLM model")
            formatted_prompt = EDIT_JD_USER_PROMPT.format(job_description=self.job_description)
            response, token_usage, cost = await self.client.openai_model_response(EDIT_JD_SYSTEM_PROMPT, formatted_prompt, JobDescription, "gpt-4o-mini")
            logging.info("Successfully generated job description")
            job_description = json.loads(response)
            jd_id = await jd_db.insert_jd(user_id=self.user_id, chat_id=self.chat_id, job_description=job_description, token_usage=token_usage, cost=cost, is_generated=False)
            await user_db.update_user_token_cost(self.user_id, token_usage['total_tokens'], cost['total_cost'], "jd")
            logging.info("Successfully inserted job description and updated user token cost")
            return jd_id
        except Exception as e:
            logging.error("Error optimising job description: %s", str(e))
            return Responses.error(500, "Error optimising job description")

# -------------------- Testing --------------------
# from app.config import start_db
# async def main_1():
#     "TESTING JOB DESCRIPTION OPTIMISER"
#     await start_db()
#     job_description = "Software Engineer"
#     job_description_generator = JobDescriptionOptimiser(job_description, "67d44a9e90a12565210d0a2a", "456")
#     jd_id = await job_description_generator.optimise()
#     pprint(jd_id)

# async def main_2():

#     "TESTING JOB DESCRIPTION GENERATOR"
#     await start_db()

#     input_data = {
#         "company_name": "Zomato",
#         "job_title": "law Associate",
#         "department": "Legal",
#         "location": "Mumbai",
#         "skills": ["Law"],
#         "qualifications": ["Bachelor's Degree in Law"],
#         "experience": "Fresher",
#         "job_type": " Offline",
#         "about_url": "https://www.zomato.com/who-we-are",
#         "language": "Hindi",
#         "salary_range": "100000-150000",
#         "tone": "Casual"}
    
#     # Create the generator asynchronously.
#     generator = JobDescriptionGenerator(input_data, "67d44a9e90a12565210d0a2a", "456")
#     jd_id = await generator.generate()
#     print(jd_id)

# if __name__ == "__main__":
#     asyncio.run(main_1())