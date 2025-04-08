import logging
from typing import Annotated, List, Dict
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.graph import END
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langgraph.types import Command
from app.services.model_format.chatbot_format import MainState
from app.repository.task_repository import TaskRepository as task_db
from app.repository.user_repository import UserRepository as user_db
from app.helpers.ai_helper import LangGraphClient
from app.services.db_services import UserQuery as user_query
from app.services.model_format.chatbot_format import RpStructuredOutput
from app.services.prompts.chatbot_prompts import RP_PROMPT, RP_RESCREENING_PROMPT
from app.tasks.resume_tasks import rescreening_worker   

logging.basicConfig(level=logging.INFO)

async def rescreening_tool(tool_call_id: Annotated[str, InjectedToolCallId], user_id: Annotated[str, InjectedState('user_id')], chat_id: Annotated[str, InjectedState('chat_id')], db_query_result: Annotated[Dict, InjectedState('db_query_result')], parsed_jd_id: Annotated[str, InjectedState('parsed_jd_id')], custom_parameters:List[str]):
    '''
    This tool will be used to rescreen the candidates, based on the custom parameters provided by the user.
    custom_parameters: HR custom requirements regarding candidates in a comma separated python list.
    '''
    try:
        if db_query_result != {}:
            if db_query_result['type'] == 'resumes':
                logging.info("DB query result: %s", db_query_result)
                candidates = db_query_result['data']
            else:
                return Command(update={'task_id': "",'messages': [ToolMessage(content='use `candidate_fetching_db_tool_for_resume` to fetch candidates required by the user.', tool_call_id=tool_call_id)]})
        else:
            return Command(update={'task_id': "",'messages': [ToolMessage(content='use `candidate_fetching_db_tool_for_resume` to fetch candidates required by the user.', tool_call_id=tool_call_id)]})
        task_id = await task_db.insert_task(user_id=user_id, chat_id=chat_id, task_type="rescreening", status="PENDING", metadata={'uploaded_resumes':len(candidates), 'parsed_resumes':0})
        for candidate in candidates:
            rescreening_worker.delay(user_id, candidate, parsed_jd_id, task_id, custom_parameters)

        return Command(update={'task_id': task_id, 'messages': [ToolMessage(content='your resumes are sent for rescreening, you will receive the results shortly.', tool_call_id=tool_call_id, role="tool")]})
    except Exception as e:
        logging.error("Error in rescreening tool: %s", e)
        return Command(update={'task_id': "",'messages': [ToolMessage(content=f'Error: {e}', tool_call_id=tool_call_id, role="tool")]})

async def candidate_fetching_db_tool_for_resume(tool_call_id: Annotated[str, InjectedToolCallId] ,chat_id: Annotated[str, InjectedState('chat_id')], user_id: Annotated[str, InjectedState('user_id')], message:str):
    '''
    This tools is used to fetches information based on the user's requirements.
    message: str - user requirements.
    '''
    try:
        logging.info("Fetching data from the database for message: %s and chat_id: %s", message, chat_id)
        db_query_result = await user_query(message + "\n" + "Fetch candidates **parsed_resume** and **_id**", chat_id, 'resume', user_id).fetch_data()
        print(db_query_result)
        data = {"type": 'resumes', "data": db_query_result}
        logging.info("Data fetched from the database: %s", db_query_result[1])
        return Command(update = {"db_query_result": data, "messages": [ToolMessage(content="Successfully fetched the data from the database, Is there anything else you want to know?", tool_call_id=tool_call_id, role="tool")]})
    except Exception as e:
        return Command(update = {"messages": [ToolMessage(content=f'Error: {e}', tool_call_id=tool_call_id, role="tool")]})

async def rp_assistant(state: MainState):
    sys_msg = SystemMessage(content=RP_PROMPT.format(messages=state["messages"], resume_parsed=state["resume_parsed"]))
    llm = LangGraphClient()
    assistant = llm.create_assistant(response_format=RpStructuredOutput)
    response = assistant.invoke([sys_msg])
    logging.info("Response: %s", response)
    token_cost_usage = llm.total_token_cost_calculator(response['raw'].usage_metadata)
    await user_db.update_user_token_cost(state["user_id"], token_cost_usage["token_usage"], token_cost_usage["cost"], "chat")
    return {'resume_parsed': response['parsed'].resume_parsed, 'messages': AIMessage(response['parsed'].messages, name="chatur")}


async def rp_rescreening(state: MainState):
    sys_msg = SystemMessage(content=RP_RESCREENING_PROMPT)
    llm = LangGraphClient()
    assistant = llm.create_assistant(tools=[rescreening_tool, candidate_fetching_db_tool_for_resume])
    response = assistant.invoke([sys_msg] + state['messages'])
    logging.info("Response: %s", response)
    token_cost_usage = llm.total_token_cost_calculator(response.usage_metadata)
    await user_db.update_user_token_cost(state["user_id"], token_cost_usage["token_usage"], token_cost_usage["cost"], "chat")
    return {"messages": [response]}

def rescreening_tool_conndition(state: MainState):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "rp_tools"
    return END

def rp_node_condition(state: MainState):
    if state["resume_parsed"] == True:
        return "rescreening"
    return END

def rescreen_to_db_node_condition(state: MainState):
    if state["messages"][-1].content == "db_assistant":
        return "db_assistant"
    return END


# --------------- TESTING THE JD ASSISTANT ---------------
# if __name__ == "__main__":
#     from app.config.db_config import start_db
#     from langgraph.graph import StateGraph, END, START
#     from langchain_core.messages import HumanMessage
#     from langgraph.prebuilt import ToolNode
#     import sys
#     import asyncio
#     from app.services.model_format.chatbot_format import MainOutputState


#     def build_jd_graph():
#         """Build and return the JD assistant graph"""
#         builder = StateGraph(MainState, MainOutputState)
#         rp_tools = [rescreening_tool]
#         builder.add_node("rp_assistant", rp_assistant)
#         builder.add_node("rescreening", rescreening)
#         builder.add_node("rp_tools", ToolNode(rp_tools))

#         builder.add_edge(START, "rp_assistant")
#         builder.add_conditional_edges("rp_assistant", rp_node_condition, ["rescreening", END])
#         builder.add_conditional_edges("rescreening", rescreening_tool_conndition, ["rp_tools", END])
#         builder.add_edge("rp_tools", "rescreening")
        
#         return builder.compile()

#     async def test_rp_assistant(prompt="Hi, screen the following resumes based on the custom parameters provided by the user"):
#         """Test the JD assistant with a sample prompt"""
#         await start_db()
        
#         graph = build_jd_graph()
#         config = {"configurable": {"thread_id": "3"}}
        
#         test_state = {
#             "messages": [HumanMessage(content=prompt)],
#             "user_id": "67d44a9e90a12565210d0a2a", 
#             "chat_id": "456",
#             "resume_parsed": True,
#         } 
#         messages = await graph.ainvoke(test_state)
    
#         print("\n=== TEST RESULTS ===")
#         print(f"Input: {prompt}")
#         print("\nOutput messages:")
#         for m in messages['messages']:
#             m.pretty_print()
        
#         return messages
    

#     asyncio.run(test_rp_assistant())