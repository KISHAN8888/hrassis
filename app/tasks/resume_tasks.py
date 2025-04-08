import os, logging, asyncio
from typing import List
from app.tasks.celery_app import celery_app
from app.services.resume_services import ResumeService as parsing_service
from app.services.resume_services import RescreeningService as rescreening_service
from app.repository.task_repository import TaskRepository as task_db
from app.config.db_config import start_db, close_db

logging.basicConfig(level=logging.INFO)

UPLOAD_DIR = os.getenv('RESUME_UPLOAD_DIR')

@celery_app.task
def parse_resume_worker(user_id: str, chat_id: str, jd_id: str, resume_file: str, task_id: str):
    """
    Celery task that processes a single resume:
      - Creates a ResumeParser instance
      - Processes the resume
      - Updates the task status in the DB
    """
    logging.info("Starting resume parsing task for file: %s", resume_file)
    result = {"file": os.path.basename(resume_file), "success": False}
    async def _process_resume():
        try:
            await start_db()
            logging.info("Processing single resume: %s", resume_file)
            parser = parsing_service(user_id, chat_id, jd_id, resume_file)
            candidate_name = await parser.parse_resume()
            result["candidate_name"] = candidate_name
            result["success"] = True
            logging.info("Parsed Candidate info: %s", candidate_name)
            await task_db.update_task_metadata(task_id)
            close_db()
            return result
        except Exception as e:
            logging.error("Error processing resume %s: %s", resume_file, str(e))
            result["error"] = str(e)
            result["success"] = False
            close_db()
            return result
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_process_resume())

@celery_app.task
def rescreening_worker(user_id: str, data: dict, jd_id: str, task_id: str, custom_parameters: List[str]):
    """
    Celery task that processes a single resume:
      - Creates a RescreeningService instance
      - Processes the resume
      - Updates the task status in the DB
    """
    logging.info("Starting rescreening task for task_id: %s", task_id)
    async def _rescreening():
        try:
            await start_db()
            await task_db.update_task_status(task_id, "PENDING")
            rescreener = rescreening_service(user_id, str(data['_id']), jd_id, custom_parameters, data)
            resume_id = await rescreener.rescreen_resume()
            logging.info("Rescreening task completed successfully for task_id: %s", task_id)
            await task_db.update_task_metadata(task_id)
            close_db()
            return resume_id
        except Exception as e:
            logging.error("Error in rescreening resumes: %s", e)
            await task_db.update_task_status(task_id, "FAILED")
            close_db()
            raise
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_rescreening())




