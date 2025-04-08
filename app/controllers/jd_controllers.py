import logging
from app.utils.http_responses import Responses
from app.repository.jd_repository import JobDescriptionRepository as JDService
from app.repository.user_repository import UserRepository as UserDbServices
from fastapi import Depends
from app.repository.chat_repository import ChatRepository as chat_db
from app.middlewares.auth_middleware import AuthMiddleware as Auth


logging.basicConfig(level=logging.INFO)

class Jd:
  
  @staticmethod
  async def get_jd(jd_id: str,user=Depends(Auth.authenticate_user)):
    logging.info("Getting job description with id: %s", jd_id)
    try:
        user = await UserDbServices.get_user_by_email(user["email"])
        if not user:
          return Responses.error(404, "User not found")
        jd = await JDService.get_jd_by_id(jd_id)
        if not jd:
            return Responses.error(404, "Job description not found with your UserId")
        return Responses.success(200, jd, "Job description found")
    except Exception as e:
        logging.warning("Job description not found: %s", str(e))
        return Responses.error(404, "Job description not found") 
          
  @staticmethod
  async def get_all_jd(user=Depends(Auth.authenticate_user)):
    logging.info("Getting all job descriptions with userId: %s", user)
    try:
        user = await UserDbServices.get_user_by_email(user["email"])
        if not user:
            return Responses.error(404, "User not found")
        jd = await JDService.get_all_jd(user.get("user_id"))
        if not jd:
            return Responses.error(404, "Job description not found with your UserId")
        return Responses.success(200, "Job description found",jd)
    except Exception as e:
        logging.warning("Job description not found: %s", str(e))
        return Responses.error(404, "Job description not found")
         
  @staticmethod
  async def update_publish_status(jd_id: str,chat_id: str, user=Depends(Auth.authenticate_user)):
    logging.info("Publishing job description with id: %s", jd_id)
    try:
      user = await UserDbServices.get_user_by_email(user["email"])
      print(user,"User:::::::")
      # await chat_db.update_created_jd_id(chat_id, jd_id)
      if not user: 
        return Responses.error(404, "User not found")
      jd = await JDService.get_jd_by_id(jd_id)
      if not jd:
        return Responses.error(404, "Job description not found with your UserId")
      is_publish = await JDService.update_publish_status(jd_id,chat_id,user['user_id'])
      if not is_publish:
        return Responses.error(404, "Job description not found with your UserId")
      return Responses.success(200, "Job description published successfully",jd['jd_id'])
    except Exception as e:
      logging.warning("Job description not found: %s", str(e))
      return Responses.error(404, "Job description not found")
      
  @staticmethod
  async def get_jd_by_id(jd_id: str):
    logging.info("Getting job description with id: %s", jd_id)
    try:
        jd = await JDService.get_jd_by_id(jd_id)
        if not jd:
            return Responses.error(404, "Job description not found with your UserId")
        return Responses.success(200, jd, "Job description found")
    except Exception as e:
        logging.warning("Job description not found: %s", str(e))
        return Responses.error(404, "Job description not found")   
  
  @staticmethod
  async def get_candidate_status_by_jd_id(jd_id: str, user=Depends(Auth.authenticate_user)):
    logging.info("Getting candidate status with id: %s", jd_id)
    try:
        jd = await JDService.get_candidate_status_by_jd_id(jd_id)
        print("job is", jd)
        if not jd:
            return Responses.error(404, "Job description not found with your UserId")
        return Responses.success(200, f"Candidates status for JD_id For {jd_id}", jd)
    except Exception as e:
        logging.warning("Job description not found: %s", str(e))
        return Responses.error(404, "Job description not found") 
    
  