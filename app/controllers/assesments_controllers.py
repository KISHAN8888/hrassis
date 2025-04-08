from fastapi import Request, Depends
# from app.services.assesments.generate_questions import generate_assessment
from app.middlewares.auth_middleware import AuthMiddleware
from app.repository.user_repository import UserRepository
from app.utils.http_responses import Responses
from app.repository.assessment_repository import AssessmentRepository as assessment_db

import logging
logging.basicConfig(level=logging.INFO)

class AssesmentController:
    # @staticmethod
    # async def create_assesment(request: Request, user = Depends(AuthMiddleware.authenticate_user)):
    #     "Create assesment"
    #     try:
    #         data =await request.json()
    #         print(data)
    #         duration = data.get("duration")
    #         difficulty = data.get("difficulty")
    #         final_skills = data.get("final_skills")
    #         total_questions = data.get("total_questions")
    #         chat_id = data.get("chat_id")

    #         user = await UserRepository.get_user_by_email(user["email"])

    #         result = await generate_assessment(final_skills, int(duration), difficulty, int(total_questions), chat_id, user["user_id"])

    #         print(result)
    #         return Responses.success(200, message="Success", data=result)
    #     except Exception as e:
    #         return Responses.error(500, message=str(e))
    
    @staticmethod
    async def get_user_assessment(user= Depends(AuthMiddleware.authenticate_user)):
        "Get user assessment"
        try:
            print("hello_bro")
            all_assessments = await assessment_db.get_user_assessments(user["user_id"])
            if not all_assessments:
                return Responses.error(404,message="Assessment not found")
            return Responses.success(200, message="Success - Get User Assessment", data=all_assessments)
        except Exception as e:
            return Responses.error(500, message=str(e))

        
    @staticmethod
    async def get_assesment_by_id(assesment_id: str, user= Depends(AuthMiddleware.authenticate_user)):
        try:
            assessment = await assessment_db.get_assessment_by_user_id(assesment_id,user["user_id"])
            print("helloof", assessment)
            if not assessment:
                return Responses.error(404, message="Assessment not found")
            return Responses.success(200, message="Success", data=assessment)
        except Exception as e:
            logging.error("Error in get_assesment_by_id: %s", str(e))
            return Responses.error(500, message=str(e))
