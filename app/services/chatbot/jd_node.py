import logging
from typing import Annotated, List
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langchain_core.messages import ToolMessage, SystemMessage
from app.helpers.ai_helper import LangGraphClient
from app.services.model_format.chatbot_format import MainState
from app.services.prompts.chatbot_prompts import JD_PROMPT
from app.repository.task_repository import TaskRepository as task_db
from app.repository.user_repository import UserRepository as user_db
from app.tasks.jd_tasks import generate_jd_worker

logging.basicConfig(level=logging.INFO)

async def generate_jd(tool_call_id: Annotated[str, InjectedToolCallId] ,chat_id: Annotated[str, InjectedState('chat_id')], user_id: Annotated[str, InjectedState('user_id')], job_title:str, company_name:str, department:str, location:str, job_type:str, experience:str = None, skills:List[str] = None, 
                qualifications:List[str] = None, language:str = None, salary_range:str = None, about_url:str = None, verifed:bool = False):
    
    '''The given function takes in the following inputs and returns a job description
    job_title: str - Tilte for the job, compulsory input
    company_name: str - Name of the company, compulsory input
    department: str - Department for which the job is being created, compulsory input
    location: str - Location of the company, compulsory input
    job_type: str - Type of the job, compulsory input
    experience: str - Experience required for the job, optional input
    skills: List[str] - Skills required for the job in a list, optional input
    qualifications: List[str] - Qualifications required for the job in a list, optional input
    language: str - Language of the job, optional input
    salary_range: str - Salary range for the job, optional input
    about_url: str - About page URL of the company, to better understand the company's business, optional input
    verifed: bool - Whether the job description's input are verified or not.
    '''
    if verifed:
        payload = {
            "job_title": job_title, "company_name": company_name,
            "department": department, "location": location,
            "job_type": job_type, "experience": experience,
            "skills": skills, "qualifications": qualifications,
            "language": language, "salary_range": salary_range,
            "about_url": about_url, "tone" : "professional and engaging"}
        
        try:
            task_id = await task_db.insert_task(user_id=user_id, chat_id=chat_id, task_type="jd_generation", status="PENDING", metadata=None)
            generate_jd_worker.delay(payload, user_id, chat_id, task_id)
            logging.info("JD generation task_id: %s", task_id)

            return Command(update = {"task_id": task_id, "messages": [ToolMessage("Successfully drafted the JD, Do you want to suggest any changes?", tool_call_id=tool_call_id)]})
        
        except Exception as e:
            logging.error("Error in JD generation at verification step: %s", e)
            return Command({"messages": [ToolMessage(f"Error: {e}", tool_call_id=tool_call_id)]})
    else:
        logging.error("Error in JD generation: %s", e)
        return Command({"messages": [ToolMessage(f"Error: {e}", tool_call_id=tool_call_id)]})

async def jd_assistant(state: MainState):
    sys_msg = SystemMessage(content=JD_PROMPT)
    llm = LangGraphClient()
    logging.info("Messages send to jd_assistant")
    assistant = llm.create_assistant(tools=[generate_jd])
    response = assistant.invoke([sys_msg] + state["messages"])
    token_cost_usage = llm.total_token_cost_calculator(response.usage_metadata)
    await user_db.update_user_token_cost(state["user_id"], token_cost_usage["token_usage"], token_cost_usage["cost"], "chat")
    return {"messages": [response]}
    
# --------------- TESTING THE JD ASSISTANT ---------------
# if __name__ == "__main__":
#     from app.config.db_config import start_db
#     from langgraph.graph import StateGraph, END, START
#     from langchain_core.messages import HumanMessage
#     from langgraph.prebuilt import ToolNode
#     import sys

#     def build_jd_graph():
#         """Build and return the JD assistant graph"""
#         builder = StateGraph(MainState, MainOutputState)
#         jd_tools = [generate_jd]
#         builder.add_node("jd_assistant", jd_assistant)
#         builder.add_node("jd_tools", ToolNode(jd_tools))

#         builder.add_edge(START, "jd_assistant")
#         builder.add_conditional_edges(
#             "jd_assistant", 
#             LangGraphClient().create_tool_condition("generate_jd"), 
#             ["jd_tools", END]
#         )
#         builder.add_edge("jd_tools", "jd_assistant")
        
#         return builder.compile()

#     async def test_jd_assistant(prompt="Hi, I am a recruiter, I need a JD for a job in a company called 'ABC'"):
#         """Test the JD assistant with a sample prompt"""
#         await start_db()
        
#         graph = build_jd_graph()
#         config = {"configurable": {"thread_id": "3"}}
        
#         test_state = {
#             "messages": [HumanMessage(content=prompt)],
#             "user_id": "67d44a9e90a12565210d0a2a", 
#             "chat_id": "456"
#         } 
#         messages = await graph.ainvoke(test_state)
    
#         print("\n=== TEST RESULTS ===")
#         print(f"Input: {prompt}")
#         print("\nOutput messages:")
#         for m in messages['messages']:
#             m.pretty_print()
        
#         return messages
    

#     asyncio.run(test_jd_assistant())


