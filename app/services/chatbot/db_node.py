import logging
from typing import Annotated
from langgraph.graph import END
from langgraph.prebuilt import InjectedState
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools.base import InjectedToolCallId
from langgraph.types import Command
from app.services.db_services import UserQuery as user_query
from app.services.model_format.chatbot_format import MainState
from app.services.prompts.chatbot_prompts import DB_PROMPT
from app.helpers.ai_helper import LangGraphClient
from app.repository.user_repository import UserRepository as user_db

logging.basicConfig(level=logging.INFO)

async def search_db(tool_call_id: Annotated[str, InjectedToolCallId] ,chat_id: Annotated[str, InjectedState('chat_id')], user_id: Annotated[str, InjectedState('user_id')], message:str, type: str):
    '''
    This tools is used to fetches information based on the user's requirements.
    message: str - user requirements.
    type: Literal[`job_description`, `resume`] - type of the data to be fetched from db.
    '''
    try:
        logging.info("Fetching data from the database for message: %s and chat_id: %s", message, chat_id)
        db_query_result = await user_query(message, chat_id, type, user_id).fetch_data()
        data = {"type": type, "data": db_query_result}
        logging.info("Data fetched from the database: %s", db_query_result[1])
        return Command(
            update = {"db_query_result": data, "messages": [ToolMessage("Successfully fetched the data from the database, Is there anything else you want to know?", tool_call_id=tool_call_id)]})
    except Exception as e:
        return Command(update = {"messages": [ToolMessage(f'Error: {e}', tool_call_id=tool_call_id)]})

async def db_assistant(state: MainState):
    sys_msg = SystemMessage(content=DB_PROMPT)
    llm = LangGraphClient()
    assistant = llm.create_assistant(tools=[search_db])
    response = assistant.invoke([sys_msg]+state['messages'])
    token_cost_usage = llm.total_token_cost_calculator(response.usage_metadata)
    await user_db.update_user_token_cost(state["user_id"], token_cost_usage["token_usage"], token_cost_usage["cost"], "chat")
    return {"messages": [response]}

def db_tool_condition(state: MainState):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "db_tools"
    return END

# --------------- TESTING THE DB ASSISTANT ---------------
# if __name__ == "__main__":
#     from app.config.db_config import start_db
#     from langgraph.graph import StateGraph, END, START
#     from langchain_core.messages import HumanMessage
#     from langgraph.prebuilt import ToolNode
#     import asyncio
#     from app.services.model_format.chatbot_format import MainOutputState
#     import sys

#     def build_jd_graph():
#         """Build and return the JD assistant graph"""
#         builder = StateGraph(MainState, MainOutputState)
#         db_tools = [search_db]
#         builder.add_node("db_assistant", db_assistant)
#         builder.add_node("db_tools", ToolNode(db_tools))

#         builder.add_edge(START, "db_assistant")
#         builder.add_conditional_edges(
#             "db_assistant", 
#             LangGraphClient().create_tool_condition("search_db"), 
#             ["db_tools", END]
#         )
#         builder.add_edge("db_tools", "db_assistant")
        
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
