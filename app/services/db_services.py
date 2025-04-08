import os, json
import asyncio
import logging
from datetime import datetime # Don't remove these imports
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.helpers.ai_helper import OpenAIClient
from app.services.prompts.db_prompts import FETCH_JD_USER_PROMPT, FETCH_JD_SYSTEM_PROMPT, FETCH_RP_USER_PROMPT, FETCH_RP_SYSTEM_PROMPT
from app.services.model_format.db_format import FetchDB
from app.repository.user_repository import UserRepository as user_db
from app.config.env_config import env_config

logging.basicConfig(level=logging.INFO)

class UserQuery:
    def __init__(self, message, chat_id, type, user_id):
        self.message = message
        self.chat_id = chat_id
        self.type = type
        self.user_id = user_id
        self.openai_client = OpenAIClient()

        self.client = AsyncIOMotorClient(env_config.db.db_url)
        self.db = self.client[env_config.db.db_name]

    async def _generate_query(self, system_prompt, user_prompt):
        try:
            logging.info("Generating query for %s collection", self.type)
            formatted_prompt = user_prompt.format(message=self.message, chat_id=self.chat_id)
            response, token_usage, cost = await self.openai_client.openai_model_response(system_prompt, formatted_prompt, FetchDB, "o3-mini")
            logging.info(response)
            await user_db.update_user_token_cost(self.user_id, token_usage["total_tokens"], cost['total_cost'], "chat")
            return json.loads(response)
        except Exception as e:
            logging.error("Error generating query: %s", e)
            return None

    async def fetch_data(self):
        try:
            data = list()
            if self.type == "job_description":
                collection = self.db.jobDescription
                query = await self._generate_query(FETCH_JD_SYSTEM_PROMPT, FETCH_JD_USER_PROMPT)
            elif self.type == "resume":
                collection = self.db.resumeData
                query = await self._generate_query(FETCH_RP_SYSTEM_PROMPT, FETCH_RP_USER_PROMPT)
            else:
                raise ValueError(f"Unknown collection: {self.type}")
            
            mongodb_response = eval(query['mongodb_query'])
            
            def convert_objectid(item):
                if isinstance(item, dict):
                    return {k: str(v) if isinstance(v, ObjectId) else v for k, v in item.items()}
                return item
            
            if hasattr(mongodb_response, 'to_list'):
                data = await mongodb_response.to_list(length=500)
                data = [convert_objectid(item) for item in data]
            else:
                result = await mongodb_response
                result = convert_objectid(result)
                data = [result] if result else []
    
            return data
        except Exception as e:
            logging.error("Error fetching data: %s", e)
            return []

# --------------- TESTING THE USER QUERY ---------------
# async def main():
#     user_query = UserQuery(
#         message="fetch me previously created job description", 
#         chat_id="67caa422936b9b70dd6404d5",
#         type="job_description",
#         user_id="673080808080808080808080"
#     )
#     data = await user_query.fetch_data()
#     print(data)

# if __name__ == "__main__":
#     asyncio.run(main())