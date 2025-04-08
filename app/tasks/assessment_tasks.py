import logging
import asyncio
from app.tasks.celery_app import celery_app
from app.config.db_config import start_db, close_db
from app.repository.task_repository import TaskRepository as task_db
from app.services.assessment_services import AssessmentTaskGenerator

logging.basicConfig(level=logging.INFO)



@celery_app.task
def generate_assessment_worker(input_data, user_id, chat_id, task_id):
    """
    Celery task to generate assessment tasks and save them to the database.
    """
    logging.info("Starting assessment task generation with payload: %s", input_data)
    
    # Set up the event loop for this task
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Define the async function
    async def _generate():
        try:
            await start_db()
            logging.info("Database connection established")
            
            # Update task status to PROCESSING
            task = await task_db.update_task_status(task_id, "PENDING")
            logging.info("Task status updated to PENDING: %s", task_id)
            
            # Initialize generator and generate assessment
            generator = AssessmentTaskGenerator(input_data, user_id, chat_id)
            logging.info("Generator initialized for user_id: %s, chat_id: %s", user_id, chat_id)
            
            assessment_id = await generator.generate()
            logging.info("Assessment generated with ID: %s", assessment_id)
            
            # Handle potential error response
            if isinstance(assessment_id, dict) and "error" in assessment_id:
                error_msg = assessment_id.get("message", "Unknown error")
                logging.error("Error generating assessment: %s", error_msg)
                await task_db.update_task_status(task_id, "FAILED")
                close_db()
                return {
                    "status": "error", 
                    "code": 500, 
                    "message": f"Error generating assessment: {error_msg}"
                }
            
            # Update task with assessment ID
            logging.info("Updating task status to COMPLETED for task_id: %s", task_id)
            await task_db.update_task(task_id, {
                "status": "SUCCESS",
                "metadata": {"assessment_id": assessment_id}
            })
            
            close_db()
            logging.info("Database connection closed")
            
            return {
                "status": "success", 
                "task_id": task_id, 
                "assessment_id": assessment_id,
                "message": "Successfully generated assessment tasks."
            }
        
        except Exception as e:
            logging.error("Exception in _generate: %s", str(e), exc_info=True)
            try:
                await task_db.update_task_status(task_id, "FAILED")
                close_db()
            except Exception as db_e:
                logging.error("Error updating task status: %s", str(db_e))
            
            return {
                "status": "error", 
                "code": 500, 
                "message": f"Error in assessment generation task: {str(e)}"
            }
    
    # Run the async function in the event loop
    try:
        result = loop.run_until_complete(_generate())
        logging.info("Task completed with result: %s", result)
        return result
    except Exception as e:
        logging.error("Error running event loop: %s", str(e), exc_info=True)
        return {
            "status": "error",
            "code": 500,
            "message": f"Error in celery task event loop: {str(e)}"
        }
# @celery_app.task
# def generate_assessment_worker(input_data, user_id, chat_id, task_id):
#     """
#     Celery task to generate assessment tasks and save them to the database.
#     The task uses an event loop to run the async operations.
#     """
#     logging.info("Starting assessment task generation")
    
#     async def _generate():
#         await start_db()
#         task = await task_db.update_task_status(task_id, "PROCESSING")
        
#         try:
#             generator = AssessmentTaskGenerator(input_data, user_id, chat_id)
#             assessment_id = await generator.generate()
#             logging.info('got the assessment_id{assessment_id}')
            
#             if isinstance(assessment_id, dict) and "error" in assessment_id:
#                 # Handle error response
#                 logging.error("Error generating assessment: %s", assessment_id.get("message", "Unknown error"))
#                 task = await task_db.update_task_status(task_id, "FAILED")
#                 close_db()
#                 return {
#                     "status": "error", 
#                     "code": 500, 
#                     "message": f"Error generating assessment: {assessment_id.get('message')}"
#                 }
            
#             logging.info("Updating task status to SUCCESS for task_id: %s - assessment_id: %s", task_id, assessment_id)
            
#             # Add assessment_id to task metadata
#             await task_db.update_task(task_id, {
#                 "status": "COMPLETED",
#                 "metadata": {"assessment_id": assessment_id}
#             })
            
#             close_db()
#             logging.info("Database connection closed")
            
#             return {
#                 "status": "success", 
#                 "task_id": task_id, 
#                 "assessment_id": assessment_id,
#                 "message": "Successfully generated assessment tasks. Would you like to review or customize them?"
#             }
        
#         except Exception as e:
#             close_db()
#             logging.error("Error in assessment generation task: %s", e)
#             task = await task_db.update_task_status(task_id, "FAILED")
#             return {
#                 "status": "error", 
#                 "code": 500, 
#                 "message": f"Error in assessment generation task: {e}"
#             }
    
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     return loop.run_until_complete(_generate())

@celery_app.task
def customize_assessment_worker(assessment_id, customization_data, user_id, chat_id, task_id):
    """
    Celery task to customize an existing assessment based on user requirements.
    The task uses an event loop to run the async operations.
    """
    logging.info("Starting assessment customization task")
    
    async def _customize():
        await start_db()
        task = await task_db.update_task_status(task_id, "PROCESSING")
        
        try:
            generator = AssessmentTaskGenerator({}, user_id, chat_id)  # Empty input_data since we're using existing assessment
            updated_assessment_id = await generator.customize_task(assessment_id, customization_data)
            
            if isinstance(updated_assessment_id, dict) and "error" in updated_assessment_id:
                # Handle error response
                logging.error("Error customizing assessment: %s", updated_assessment_id.get("message", "Unknown error"))
                task = await task_db.update_task_status(task_id, "FAILED")
                close_db()
                return {
                    "status": "error", 
                    "code": 500, 
                    "message": f"Error customizing assessment: {updated_assessment_id.get('message')}"
                }
            
            logging.info("Updating task status to SUCCESS for task_id: %s - updated_assessment_id: %s", 
                        task_id, updated_assessment_id)
            
            # Add assessment_id and customization details to task metadata
            await task_db.update_task(task_id, {
                "status": "COMPLETED",
                "metadata": {
                    "assessment_id": updated_assessment_id,
                    "original_assessment_id": assessment_id,
                    "customization_applied": customization_data
                }
            })
            
            close_db()
            logging.info("Database connection closed")
            
            return {
                "status": "success", 
                "task_id": task_id, 
                "assessment_id": updated_assessment_id,
                "message": "Successfully customized assessment tasks. Would you like to review or publish them?"
            }
        
        except Exception as e:
            close_db()
            logging.error("Error in assessment customization task: %s", e)
            task = await task_db.update_task_status(task_id, "FAILED")
            return {
                "status": "error", 
                "code": 500, 
                "message": f"Error in assessment customization task: {e}"
            }
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_customize())

@celery_app.task
def publish_assessment_worker(assessment_id, user_id, chat_id, task_id):
    """
    Celery task to publish an assessment and remove draft versions.
    The task uses an event loop to run the async operations.
    """
    logging.info("Starting assessment publication task")
    
    async def _publish():
        await start_db()
        task = await task_db.update_task_status(task_id, "PROCESSING")
        
        try:
            generator = AssessmentTaskGenerator({}, user_id, chat_id)  # Empty input_data since we're using existing assessment
            result = await generator.publish_task(assessment_id)
            
            if isinstance(result, dict) and "error" in result:
                # Handle error response
                logging.error("Error publishing assessment: %s", result.get("message", "Unknown error"))
                task = await task_db.update_task_status(task_id, "FAILED")
                close_db()
                return {
                    "status": "error", 
                    "code": 500, 
                    "message": f"Error publishing assessment: {result.get('message')}"
                }
            
            logging.info("Updating task status to SUCCESS for task_id: %s - published assessment_id: %s", 
                        task_id, assessment_id)
            
            # Add publication details to task metadata
            await task_db.update_task(task_id, {
                "status": "COMPLETED",
                "metadata": {
                    "assessment_id": assessment_id,
                    "published": True
                }
            })
            
            close_db()
            logging.info("Database connection closed")
            
            return {
                "status": "success", 
                "task_id": task_id, 
                "assessment_id": assessment_id,
                "message": "Assessment tasks have been published successfully and are ready for use."
            }
        
        except Exception as e:
            close_db()
            logging.error("Error in assessment publication task: %s", e)
            task = await task_db.update_task_status(task_id, "FAILED")
            return {
                "status": "error", 
                "code": 500, 
                "message": f"Error in assessment publication task: {e}"
            }
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_publish())
