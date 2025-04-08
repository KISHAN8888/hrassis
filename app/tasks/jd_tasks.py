import logging
import asyncio
# from celery.signals import worker_process_init
from app.tasks.celery_app import celery_app
from app.config.db_config import start_db, close_db
from app.repository.task_repository import TaskRepository as task_db
from app.services.jd_services import JobDescriptionGenerator as jd_generator

logging.basicConfig(level=logging.INFO)
async_loop = None
    
@celery_app.task
def generate_jd_worker(input_data, user_id, chat_id, task_id):
    """
    Celery task to generate a job description and save it to the database.
    The task uses an event loop to run the async operations.
    """
    logging.info("Starting job description generation task")
    async def _generate():
        await start_db()
        task = await task_db.update_task_status(task_id, "PENDING")
        try:
            generator = jd_generator(input_data, user_id, chat_id)
            jd_id = await generator.generate()
            logging.info("Updating task status to SUCCESS for task_id: %s - jd_id: %s", task_id, jd_id)

            task = await task_db.update_task_status(task_id, "SUCCESS")
            close_db()
            logging.info("Database connection closed")
            return {"status": "success", "task_id": task, "message": "Successfully drafted the JD, Do you want to suggest any changes?"}
        
        except Exception as e:
            close_db()
            logging.error("Error in job description generation task: %s", e)
            task = await task_db.update_task_status(task_id, "FAILED")
            return {"status": "error", "code": 500, "message": f"Error in job description generation task: {e}"}
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_generate())

