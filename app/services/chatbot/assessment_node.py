

import logging
from typing import Annotated, List, Dict, Optional
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langchain_core.messages import ToolMessage, SystemMessage
from app.helpers.ai_helper import LangGraphClient
from app.services.model_format.chatbot_format import MainState, AssessmentStructuredOutput
from app.services.prompts.chatbot_prompts import ASSESSMENT_PROMPT
from app.repository.task_repository import TaskRepository as task_db
from app.repository.user_repository import UserRepository as user_db
from app.tasks.assessment_tasks import generate_assessment_worker

logging.basicConfig(level=logging.INFO)

async def generate_assessment(
    tool_call_id: Annotated[str, InjectedToolCallId],
    chat_id: Annotated[str, InjectedState('chat_id')], 
    user_id: Annotated[str, InjectedState('user_id')],
    job_description: Optional[str],
    company_name: Optional[str],
    job_title: Optional[str],
    employment_type: Optional[str] = "Full-Time",
    seniority_level: Optional[str] = "Mid-Level",
    verified: bool = False
):
    '''
    Generates assessment task for hiring candidates based on job description
    
    Parameters:
    - job_description: str - Optional (full job description text)
    - company_name: str - Optional (name of the company offering the position)
    - job_title: str - Optional (title of the job position)
    - employment_type: str - Optional (defaults to "Full-Time")
    - seniority_level: str - Optional (used to adjust task difficulty)
    - verified: bool - Whether the assessment task inputs are verified

    it return a task crafted to test the candidates according to the job description
    '''
    if verified:
        payload = {
            "job_description": job_description,
            "company_name": company_name,
            "job_title": job_title,
            "employment_type": employment_type,
            "seniority_level": seniority_level
        }
        
        try:
            task_id = await task_db.insert_task(
                user_id=user_id, 
                chat_id=chat_id, 
                task_type="assessment_generation", 
                status="PENDING", 
                metadata=None
            )
            
            # Start the Celery worker task
            logging.info(f'got the task_id { task_id}')
            generate_assessment_worker.delay(payload, user_id, chat_id, task_id)
            logging.info("Assessment generation task_id: %s", task_id)

            return Command(update = {
                "task_id": task_id, 
                "assessment_id": None,
                "assessment_status": "pending",
                "messages": [ToolMessage(
                    "Successfully initiated assessment task generation. I'll create two tasks with different difficulty levels to evaluate candidates. This will take a moment to process.", 
                    tool_call_id=tool_call_id
                )]
            })
        
        except Exception as e:
            logging.error("Error in assessment generation at verification step: %s", e)
            return Command({"messages": [ToolMessage(f"Error: {e}", tool_call_id=tool_call_id)]})
    else:
        logging.error("Assessment task inputs are not verified")
        return Command({"messages": [ToolMessage("I need to verify the assessment inputs before proceeding. Could you confirm the job details are accurate?", tool_call_id=tool_call_id)]})

async def customize_assessment(
    tool_call_id: Annotated[str, InjectedToolCallId],
    chat_id: Annotated[str, InjectedState('chat_id')], 
    user_id: Annotated[str, InjectedState('user_id')],
    assessment_id: str,
    customization_requests: Dict
):
    '''
    Customizes an existing assessment task based on specific requirements
    
    Parameters:
    - assessment_id: str - ID of the assessment task to customize
    - customization_requests: Dict - Dictionary of customization requests
    '''
    try:
        from app.repository.assessment_repository import AssessmentRepository
        
        # Verify task exists and user has access
        assessment = await AssessmentRepository.get_assessment_by_chat_id(chat_id)
        assessment = await AssessmentRepository.get_assessment_by_id(assessment_id)
        
        if not assessment:
            return Command({"messages": [ToolMessage("Assessment task not found", tool_call_id=tool_call_id)]})
            
        if assessment["user_id"] != user_id:
            return Command({"messages": [ToolMessage("You don't have permission to customize this assessment", tool_call_id=tool_call_id)]})
        
        # Create a new task for customization
        customization_task_id = await task_db.insert_task(
            user_id=user_id, 
            chat_id=chat_id, 
            task_type="assessment_customization", 
            status="PENDING", 
            metadata={"original_assessment_id": assessment_id}
        )
        
        # Start the Celery worker task
        from app.tasks.assessment_tasks import customize_assessment_worker
        customize_assessment_worker.delay(assessment_id, customization_requests, user_id, chat_id, customization_task_id)
        
        logging.info("Assessment customization task_id: %s", customization_task_id)
        
        return Command(update = {
            "task_id": customization_task_id,
            "assessment_status": "processing",
            "messages": [ToolMessage(
                "I'm customizing your assessment tasks according to your requirements. This will take a moment to process.", 
                tool_call_id=tool_call_id
            )]
        })
        
    except Exception as e:
        logging.error("Error in assessment customization: %s", e)
        return Command({"messages": [ToolMessage(f"Error during customization: {e}", tool_call_id=tool_call_id)]})

async def publish_assessment(
    tool_call_id: Annotated[str, InjectedToolCallId],
    chat_id: Annotated[str, InjectedState('chat_id')], 
    user_id: Annotated[str, InjectedState('user_id')],
    assessment_id: str
):
    '''
    Publishes an assessment task and removes other drafts
    
    Parameters:
    - assessment_id: str - ID of the assessment task to publish
    '''
    try:
        from app.services.assessment_services import AssessmentTaskGenerator
        from app.repository.assessment_repository import AssessmentRepository
        
        # Verify task exists and user has access
        assessment = await AssessmentRepository.get_assessment_by_id(assessment_id)
        
        if not assessment:
            return Command({"messages": [ToolMessage("Assessment task not found", tool_call_id=tool_call_id)]})
            
        if assessment["user_id"] != user_id:
            return Command({"messages": [ToolMessage("You don't have permission to publish this assessment", tool_call_id=tool_call_id)]})
        
        # Initialize assessment generator
        generator = AssessmentTaskGenerator(
            input_data={},  # Empty as we'll use the stored inputs
            user_id=user_id,
            chat_id=chat_id
        )
        
        # Publish the task
        result = await generator.publish_task(assessment_id)
        
        if isinstance(result, dict) and "error" in result:
            return Command({"messages": [ToolMessage(f"Error: {result['message']}", tool_call_id=tool_call_id)]})
        
        return Command(update = {
            "assessment_status": "published",
            "messages": [ToolMessage(
                "Assessment task has been published successfully. It's now ready to be sent to candidates.", 
                tool_call_id=tool_call_id
            )]
        })
        
    except Exception as e:
        logging.error("Error in assessment publication: %s", e)
        return Command({"messages": [ToolMessage(f"Error during publication: {e}", tool_call_id=tool_call_id)]})

# async def assessment_assistant(state: MainState):
#     """
#     Assessment Assistant node that handles assessment-related user requests.
    
#     Args:
#         state: The current state containing messages, user_id, and chat_id
        
#     Returns:
#         dict: Updated state with the assistant's response
#     """
#     llm = LangGraphClient()
#     logging.info("Processing request in assessment_assistant")
    
#     # Create system message with the assessment prompt
#     sys_msg = SystemMessage(content=ASSESSMENT_PROMPT)
    
#     # Create the assistant with assessment tools
#     assistant = llm.create_assistant(
#         tools=[generate_assessment, customize_assessment, publish_assessment],
#         response_format=AssessmentStructuredOutput
#     )
    
#     # Invoke the assistant
#     response = await assistant.ainvoke([sys_msg] + state["messages"])
    
#     # Calculate token usage and update user stats
#     token_cost_usage = llm.total_token_cost_calculator(response['raw'].usage_metadata)
#     await user_db.update_user_token_cost(
#         state["user_id"], 
#         token_cost_usage["token_usage"], 
#         token_cost_usage["cost"], 
#         "chat"
#     )
    
#     # Extract the structured output
#     structured_output = response['parsed']
    
#     # Prepare updates to the state
#     updates = {"messages": [response['raw']]}
    
#     # Add assessment-related updates if available
#     if structured_output.assessment_id:
#         updates["assessment_id"] = structured_output.assessment_id
    
#     if structured_output.assessment_status:
#         updates["assessment_status"] = structured_output.assessment_status
    
#     logging.info("Assessment assistant processed request successfully")
#     return updates

async def assessment_assistant(state: MainState):
    """
    Assessment Assistant node that handles assessment-related user requests.
    """
    llm = LangGraphClient()
    logging.info("Processing request in assessment_assistant")
    
    # Create system message with the assessment prompt
    sys_msg = SystemMessage(content=ASSESSMENT_PROMPT)
    
    # Create the assistant with assessment tools - mimic successful jd_assistant pattern
    assistant = llm.create_assistant(tools=[generate_assessment, customize_assessment, publish_assessment])
    
    response = assistant.invoke([sys_msg] + state["messages"])
    
    token_cost_usage = llm.total_token_cost_calculator(response.usage_metadata)
    await user_db.update_user_token_cost(
        state["user_id"], 
        token_cost_usage["token_usage"], 
        token_cost_usage["cost"], 
        "chat"
    )
    
    return {"messages": [response]}