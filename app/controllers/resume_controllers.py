from typing import Optional, List
import logging, os, asyncio, shutil,aiohttp
from fastapi import UploadFile, Depends, Form, File, Request
from app.middlewares.auth_middleware import AuthMiddleware as auth_middleware
from app.repository.user_repository import UserRepository as user_db
from app.repository.task_repository import TaskRepository as task_db
from app.repository.chat_repository import ChatRepository as chat_db
from app.repository.resume_repository import ResumeRepository as resume_db
from app.repository.jd_repository import JobDescriptionRepository as jd_db
from app.services.jd_services import JobDescriptionOptimiser as jd_optimiser
from app.config.env_config import env_config
from app.utils.mail_utils import MailUtils
from app.utils.http_responses import Responses
from app.helpers.resume_helper import ResumeHelper as resume_helper
from app.utils.temp_folder import TempFolder as temp_folder
from app.tasks.resume_tasks import parse_resume_worker
from app.services.user_services import Auth as auth
from pprint import pprint

logging.basicConfig(level=logging.INFO)

class ResumeControllers:
    @staticmethod
    async def upload_resumes(jd_id: Optional[str] = Form(None), job_description: Optional[str] = Form(None), jd_file: Optional[UploadFile] = File(None), resume_files: List[str] = File(None), chat_id: str = Form(None), user = Depends(auth_middleware.authenticate_user)):
    # async def upload_resumes(jd_id: Optional[str] = Form(None), job_description: Optional[str] = Form(None), jd_file: Optional[UploadFile] = File(None), resume_files: List[UploadFile] = File(...), chat_id: str = Form(None)):
        "Upload resumes to the server"
        try:
            logging.info("Starting resume upload process....")
            if not resume_files:
                logging.warning("No resume files provided in request..")
                return Responses.error(400, message="No resume files uploaded")
            
            if not (jd_id or job_description or jd_file):
                logging.warning("No job description information provided...")
                return Responses.error(400, message="Please provide either job description text, job description file, or job description ID")
            
            if not jd_id:
                if job_description:
                    logging.info("Processing provided job description text...")
                    jd_optimzier = jd_optimiser(job_description, user["user_id"], chat_id)
                    jd_id = await jd_optimzier.optimise()
                elif jd_file:
                    logging.info("Processing uploaded job description file...")
                    temp_file_name = await temp_folder.create_temp_folder(jd_file)
                    file_text = asyncio.to_thread(resume_helper.extract_text_from_file_path, temp_file_name)
                    jd_id = await jd_optimiser(file_text, user["user_id"], chat_id).optimise()
                    await temp_folder.delete_temp_folder(temp_file_name)

            task_id = await task_db.insert_task(user["user_id"],chat_id,"resume_parsing","PENDING", {"uploaded_resumes": len(resume_files), "parsed_resumes": 0})
            await chat_db.update_parsed_jd_id(chat_id, jd_id)
            try: 
                # user = await user_db.get_user_by_id(user_id=user["user_id"])
                # token = await auth.create_jwt_token(user)
                # headers = { 'Authorization': f'Bearer {token}' }
                            
                # async with aiohttp.ClientSession() as session:
                #     data = aiohttp.FormData()
                #     for resume_file in resume_files:
                #         await resume_file.seek(0)
                #         file_content = await resume_file.read()
                #         data.add_field('resumes',file_content, filename=resume_file.filename, content_type='application/pdf')
                    
                #     async with session.post("https://upload-staging.aichatur.com/api/v1/resume/upload-resume", headers=headers, data=data) as response:
                #         result = await response.json()
                #         location_urls = []
                #         if result.get("success") and "filepaths" in result:
                #             location_urls = [filepath.get("Location") for filepath in result.get("filepaths", [])]
                for location in resume_files:
                    parse_resume_worker.delay(user["user_id"], chat_id, jd_id, location, task_id)

                logging.info("Resume parsing task queued with ID: %s", task_id)
                return {"message": "Resume parsing task queued successfully", "task_id": task_id, "jd_id": chat_id}
            except Exception as e:
                # if os.path.exists(upload_path):
                #     shutil.rmtree(upload_path)
                return Responses.error(400, message=f"Error in resume upload: {str(e)}")
        except Exception as e:
            logging.error("Error uploading resumes: %s", str(e))
            return Responses.error(500, message="Error in uploading resumes route")

    @staticmethod
    async def update_candidate_status(request: Request,user = Depends(auth_middleware.authenticate_user)): 
        "Update candidate function"
        try:
            data = await request.json()
            jd_id = data.get("jd_id")
            status = data.get("status")
            chat_id = data.get("chat_id")
            resume_ids = data.get("resume_id")
            user = await user_db.get_user_by_email(user["email"])
            if not user:
                logging.error("User not found")
                return Responses.error(404, message="User not found")
            if not user['user_id'] or not jd_id or not status or not resume_ids or not chat_id:
                logging.error("Missing required fields:user_id, jd_id,chat_id or status")
                return Responses.error(400, message="Missing required fields: candidate_email, user_id, jd_id, or status")
            
            # Aggregate resumes by ids
            candidate_data = await resume_db.get_resumes_by_ids(resume_ids)
            candidates_data = {
                "candidates":candidate_data,
                "input_data":{
                    "job_title": "SDE2",
                    "company_name": "Wsserstoff",
                    "department": "IT",
                    "contact_email":user['email']
                },
                "chat_id":chat_id,
                "email_type":"rejection_letter",
            }
            if status not in ["ACCEPTED", "REJECTED", "PENDING"]:
                return Responses.error(400, message="Invalid status value")
            for id in resume_ids:
                updated_resume = await resume_db.update_resume_status(status, user['user_id'], jd_id, id)
            isupdated = await jd_db.update_candidate_status(jd_id, chat_id, user["user_id"], status, resume_ids)

            if not isupdated:
                logging.error("Candidate status successfully updated.")
                return Responses.error(400, message="Candidate not updated successfully")
            if not updated_resume:
                logging.error("Resume not found for ID")
                return Responses.error(404, message="Resume not Updated or Resume Not Found")
            if status == "REJECTED":
                print("CndidateData:",candidates_data)
                # logging.info("Sending rejection email to %s", resume_data.get("Email"))
                await MailUtils.send_bulk_email(candidates_data,user)
            # DONE : If candidate is rejected send him a rejected email for the job  he screened for
            logging.info("Updated resume status successfully")
            # logging.info("Resume dat")

            return Responses.success(200, message="Resume status updated successfully", data=candidates_data)

        except Exception as e:
            return Responses.error(500, message=f'Error occured in updating candidate function - {str(e)}')



    @staticmethod
    async def get_accepted_resumes(jd_id:str,user=Depends(auth_middleware.authenticate_user)):
        try:
            resume = await resume_db.get_accepted_resume(jd_id,user["user_id"])
            print("resume_is", resume)
            if not resume:
                return Responses.error(404, message="Resume not found")
            return Responses.success(200, message="Resume fetched successfully", data=resume)
        except Exception as e:
            return Responses.error(500, message=f'Error occured in getting accepted resume - {str(e)}')
