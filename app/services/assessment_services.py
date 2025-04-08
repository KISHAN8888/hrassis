import logging
import json
import time
from typing import Dict, Tuple
from app.services.model_format.assesment_format import AssessmentTask
from app.services.prompts.assesment_prompts import ASSESSMENT_SYSTEM_PROMPT, ASSESSMENT_USER_PROMPT
from app.helpers.ai_helper import OpenAIClient
from app.repository.assessment_repository import AssessmentRepository as assessment_db
from app.repository.user_repository import UserRepository as user_db
from app.utils.http_responses import Responses

logging.basicConfig(level=logging.INFO)

class AssessmentTaskGenerator:
    '''
    Generates assessment tasks for hiring candidates based on job description
    Input data structure:
        job_description: str - Required (full job description text)
        company_name: str - Required
        job_title: str - Required
        employment_type: str - Optional (defaults to "Full-Time")
        seniority_level: str - Optional (used to adjust task difficulty)
    '''
    def __init__(self, input_data: Dict, user_id: str, chat_id: str):
        self.input_data = input_data
        self.user_id = user_id
        self.chat_id = chat_id
        self.client = OpenAIClient()

    async def generate(self) -> str:
        """
        Asynchronously generates assessment tasks using the specified model.
        Returns: Task ID if successful, error response if unsuccessful
        """
        try:
            # Generation
            logging.debug("Sending request to LLM model for assessment task generation")
            formatted_prompt = ASSESSMENT_USER_PROMPT.format(**self.input_data)
            response, token_usage, cost = await self.client.openai_model_response(
                ASSESSMENT_SYSTEM_PROMPT, 
                formatted_prompt, 
                AssessmentTask, 
                "gpt-4o-mini"
            )
            
            logging.info("Successfully generated assessment tasks")
            assessment_task = json.loads(response)
            
            # Store in database
            task_id = await assessment_db.insert_assessment(
                user_id=self.user_id, 
                chat_id=self.chat_id, 
                assessment_task=assessment_task, 
                token_usage=token_usage, 
                cost=cost, 
                assessment_inputs=self.input_data
            )

            logging.info(f'stored in the db {task_id}')
            
            # Update user token usage
            await user_db.update_user_token_cost(
                self.user_id, 
                token_usage['total_tokens'], 
                cost['total_cost'], 
                "assessment"
            )
            
            logging.info("Successfully inserted assessment task and updated user token cost")
            return task_id
            
        except Exception as e:
            logging.error("Error generating assessment task: %s", str(e))
            return Responses.error(500, "Error generating assessment task")
            
    async def customize_task(self, task_id: str, customization_data: Dict) -> str:
        """
        Customizes an existing assessment task with new parameters
        Returns: Updated task ID if successful, error response if unsuccessful
        """
        try:
            # Get existing task
            existing_task = await assessment_db.get_assessment_by_id(task_id)
            if not existing_task:
                return Responses.error(404, "Assessment task not found")
                
            # Merge existing data with customization
            merged_data = {**existing_task['assessment_inputs'], **customization_data}
            
            # Generate updated task
            formatted_prompt = ASSESSMENT_USER_PROMPT.format(**merged_data)
            response, token_usage, cost = await self.client.openai_model_response(
                ASSESSMENT_SYSTEM_PROMPT, 
                formatted_prompt, 
                AssessmentTask, 
                "gpt-4o-mini"
            )
            
            assessment_task = json.loads(response)
            
            # Update in database
            updated_task_id = await assessment_db.update_assessment(
                task_id=task_id,
                assessment_task=assessment_task,
                token_usage=token_usage,
                cost=cost,
                assessment_inputs=merged_data
            )
            
            # Update user token usage
            await user_db.update_user_token_cost(
                self.user_id, 
                token_usage['total_tokens'], 
                cost['total_cost'], 
                "assessment_update"
            )
            
            logging.info("Successfully updated assessment task")
            return updated_task_id
            
        except Exception as e:
            logging.error("Error updating assessment task: %s", str(e))
            return Responses.error(500, "Error updating assessment task")
            
    async def publish_task(self, task_id: str) -> bool:
        """
        Publishes an assessment task and removes other generated tasks for the same chat
        Returns: True if successful, error response if unsuccessful
        """
        try:
            result = await assessment_db.update_publish_status(
                task_id=task_id,
                chat_id=self.chat_id,
                user_id=self.user_id
            )
            
            if not result:
                return Responses.error(500, "Failed to publish assessment task")
                
            logging.info("Successfully published assessment task: %s", task_id)
            return True
            
        except Exception as e:
            logging.error("Error publishing assessment task: %s", str(e))
            return Responses.error(500, "Error publishing assessment task")
        
# import asyncio
# from pprint import pprint
# from app.config import start_db
# from app.services.assessment_services import AssessmentTaskGenerator
# from app.repository.assessment_repository import AssessmentRepository

# async def main_assessment():
#     """TESTING ASSESSMENT TASK GENERATOR"""
#     await start_db()
    
#     input_data = {
#         "job_description": """
#         We are looking for a talented Backend Developer to join our engineering team. The ideal candidate will have
#         strong skills in Python, Django, and RESTful API development.
        
#         Responsibilities:
#         - Design and implement scalable backend services and APIs
#         - Optimize database queries and schemas
#         - Collaborate with frontend developers to integrate user-facing elements
#         - Write clean, maintainable code with proper test coverage
#         - Participate in code reviews and technical discussions
        
#         Requirements:
#         - 3+ years of experience with Python
#         - Proficiency with Django or similar frameworks
#         - Experience with RESTful API design and implementation
#         - Knowledge of SQL databases (PostgreSQL preferred)
#         - Understanding of version control systems (Git)
#         - Strong problem-solving and debugging skills
        
#         Nice to have:
#         - Experience with containerization technologies (Docker, Kubernetes)
#         - Knowledge of message queuing systems (RabbitMQ, Kafka)
#         - Familiarity with CI/CD pipelines
#         - Background in microservices architecture
#         """,
#         "company_name": "TechInnovate",
#         "job_title": "Backend Developer",
#         "employment_type": "Full-Time",
#         "seniority_level": "Mid-Level"
#     }
    
#     # Create generator instance
#     generator = AssessmentTaskGenerator(
#         input_data=input_data,
#         user_id="67d44a9e90a12565210d0a2a",  # Use your test user ID
#         chat_id="backend_dev_chat_123"
#     )
    
#     print("\n--- Generating Assessment Task ---")
#     # Generate assessment task
#     task_id = await generator.generate()
#     print(f"Generated assessment task ID: {task_id}")
    
#     # Retrieve the generated task
#     print("\n--- Retrieving Generated Task ---")
#     assessment = await AssessmentRepository.get_assessment_by_id(task_id)
#     print("Assessment Task:")
#     pprint(assessment["assessment_task"])
    
#     # Test customization
#     print("\n--- Testing Task Customization ---")
#     customization_data = {
#         "focus_on_fastapi": True,
#         "add_security_requirement": True,
#         "reduce_timeline": "3 days"
#     }
    
#     # Update the task
#     updated_task_id = await generator.customize_task(task_id, customization_data)
#     print(f"Updated assessment task ID: {updated_task_id}")
    
#     # Retrieve the updated task
#     updated_assessment = await AssessmentRepository.get_assessment_by_id(updated_task_id)
#     print("Updated Assessment Task:")
#     pprint(updated_assessment["assessment_task"])
    
#     # Test publishing
#     print("\n--- Testing Task Publishing ---")
#     publish_result = await generator.publish_task(updated_task_id)
#     print(f"Publish result: {publish_result}")
    
#     return {
#         "original_task_id": task_id,
#         "updated_task_id": updated_task_id
#     }

# async def main_frontend_assessment():
#     """TESTING ASSESSMENT TASK GENERATOR FOR FRONTEND ROLE"""
#     await start_db()
    
#     input_data = {
#         "job_description": """
#         We are seeking a skilled Frontend Developer to create exceptional user experiences. 
#         You will be responsible for implementing visual elements and interactions that users engage with.
        
#         Responsibilities:
#         - Develop responsive user interfaces using React and modern JavaScript
#         - Work with designers to implement UI/UX designs with precision
#         - Ensure cross-browser compatibility and responsive design principles
#         - Optimize applications for maximum speed and scalability
#         - Collaborate with backend developers to integrate frontend with API services
        
#         Requirements:
#         - 2+ years of experience with React.js and JavaScript ES6+
#         - Strong knowledge of HTML5, CSS3, and responsive design
#         - Experience with state management libraries (Redux, MobX)
#         - Proficiency with modern frontend build tools (Webpack, Babel)
#         - Understanding of cross-browser compatibility issues
#         - Experience with Git version control
        
#         Bonus Skills:
#         - Experience with TypeScript
#         - Knowledge of UI/UX design principles
#         - Experience with Next.js or similar frameworks
#         - Understanding of CI/CD workflows
#         """,
#         "company_name": "DesignWorks",
#         "job_title": "Frontend Developer",
#         "employment_type": "Full-Time",
#         "seniority_level": "Mid-Level"
#     }
    
#     # Create generator instance
#     generator = AssessmentTaskGenerator(
#         input_data=input_data,
#         user_id="67d44a9e90a12565210d0a2a",  # Use your test user ID
#         chat_id="frontend_dev_chat_456"
#     )
    
#     print("\n--- Generating Frontend Assessment Task ---")
#     # Generate assessment task
#     task_id = await generator.generate()
#     print(f"Generated frontend assessment task ID: {task_id}")
    
#     # Retrieve the generated task
#     assessment = await AssessmentRepository.get_assessment_by_id(task_id)
#     print("Frontend Assessment Task:")
#     pprint(assessment["assessment_task"])
    
#     return {
#         "frontend_task_id": task_id
#     }

# async def main_non_tech_assessment():
#     """TESTING ASSESSMENT TASK GENERATOR FOR NON-TECHNICAL ROLE"""
#     await start_db()
    
#     input_data = {
#         "job_description": """
#         We are looking for a Marketing Manager to lead our marketing efforts and develop strategies to increase brand awareness.
        
#         Responsibilities:
#         - Develop and implement comprehensive marketing strategies
#         - Manage the marketing budget and allocate resources effectively
#         - Lead market research efforts to identify opportunities
#         - Create content for various channels (social media, website, email)
#         - Analyze campaign performance and optimize marketing tactics
#         - Collaborate with sales team to align marketing initiatives with sales goals
        
#         Requirements:
#         - Bachelor's degree in Marketing, Business, or related field
#         - 3+ years of experience in marketing roles
#         - Strong understanding of digital marketing channels
#         - Experience with marketing analytics tools
#         - Excellent communication and presentation skills
#         - Creative thinking and problem-solving abilities
        
#         Preferred Qualifications:
#         - Experience in the tech industry
#         - Knowledge of SEO and content marketing
#         - Project management skills
#         - Experience managing a small team
#         """,
#         "company_name": "GrowthTech",
#         "job_title": "Marketing Manager",
#         "employment_type": "Full-Time",
#         "seniority_level": "Mid-Senior Level"
#     }
    
#     # Create generator instance
#     generator = AssessmentTaskGenerator(
#         input_data=input_data,
#         user_id="67d44a9e90a12565210d0a2a",  # Use your test user ID
#         chat_id="marketing_mgr_chat_789"
#     )
    
#     print("\n--- Generating Marketing Assessment Task ---")
#     # Generate assessment task
#     task_id = await generator.generate()
#     print(f"Generated marketing assessment task ID: {task_id}")
    
#     # Retrieve the generated task
#     assessment = await AssessmentRepository.get_assessment_by_id(task_id)
#     print("Marketing Assessment Task:")
#     pprint(assessment["assessment_task"])
    
#     return {
#         "marketing_task_id": task_id
#     }

# if __name__ == "__main__":
#     # Run the test functions
#     print("RUNNING ASSESSMENT GENERATOR TESTS")
#     asyncio.run(main_assessment())
#     # Uncomment to run additional tests
#     # asyncio.run(main_frontend_assessment())
#     # asyncio.run(main_non_tech_assessment())