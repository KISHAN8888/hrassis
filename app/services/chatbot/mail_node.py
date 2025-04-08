import logging
from typing import Dict, Any, Annotated
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langgraph.graph import END
from langgraph.types import Command
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from app.services.model_format.chatbot_format import MainState
from app.services.prompts.chatbot_prompts import EMAIL_TYPE_PROMPTS, EMAIL_PROMPT
from app.services.model_format.chatbot_format import EmailStructuredOutput
from app.services.prompts.mail_prompts import SEND_EMAIL
from app.services.db_services import UserQuery as user_query
from app.repository.user_repository import UserRepository as user_db
from app.repository.task_repository import TaskRepository as task_db
from app.helpers.ai_helper import LangGraphClient
from app.utils.mail_utils import MailUtils as mail_utils
from app.config import chat_db
import inspect
import pprint
logging.basicConfig(level=logging.INFO)

def mapping_function(email_type: str):
    email_mappings = {
    "task_link": {"prompt": EMAIL_TYPE_PROMPTS['task_link'], "template": SEND_EMAIL['ASSESSMENT_EMAIL_LINK']},
    "task_attachment": {"prompt": EMAIL_TYPE_PROMPTS['task_attachment'], "template": SEND_EMAIL['ASSESSMENT_EMAIL_ATTACHMENT']},
    "offer_letter": {"prompt": EMAIL_TYPE_PROMPTS['offer_letter'], "template": SEND_EMAIL['OFFER_LETTER_EMAIL']},
    "rejection_letter": {"prompt": EMAIL_TYPE_PROMPTS['rejection_letter'], "template": SEND_EMAIL['REJECTION_LETTER_EMAIL']},
    "meet_link": {"prompt": EMAIL_TYPE_PROMPTS['meet_link_email'], "template": SEND_EMAIL['MEET_LINK_EMAIL']},
    "custom_email": {"prompt": EMAIL_TYPE_PROMPTS['custom_email'], "template": ''}}

    return email_mappings.get(email_type, {"prompt": "Unknown email type. Please specify a valid email type.", "template": "default_email_template"})

async def sending_mail_tool(tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[MainState, InjectedState],chat_id: Annotated[str, InjectedState('chat_id')], user_id: Annotated[str, InjectedState('user_id')], input_data: Dict[str, Any]):
    '''
    input_data (Dict[str, Any]): Dictionary containing all required fields for the email type, Don't proceed with the tool call if the all the fields in input_data is not complete. 
    '''
    try:
        logging.info("===== TOOL CALL STARTED =====")
        logging.info("Raw tool_call_id: %s", tool_call_id)
        logging.info("Raw state type: %s", type(state))
        logging.info("Raw input_data type: %s", type(input_data))
        logging.info("Full state contents: %s", vars(state) if hasattr(state, '__dict__') else state)
        logging.info("Calling the sending mail tool with input data: %s", input_data)
        if not input_data:
            return Command(update={'task_id': "", 'messages': [
                ToolMessage(content='Error: Missing input data for email. Please provide all required fields.', 
                           tool_call_id=tool_call_id, role="tool")
            ]})
        
        # Get email type and chat_id from state
        email_type = state.get('email_type')
        logging.info(email_type)
        chat_id = state.get('chat_id')
        logging.info(chat_id)

        user_id = state.get('user_id')
        logging.info(user_id)
        user_email = "ayush.chauhan@thewasserstoff.com"
        logging.info(f"user email{user_email}")
        
        if not email_type or not chat_id or not user_id:
            return Command(update={'task_id': "", 'messages': [
                ToolMessage(content='Error: Missing required state fields (email_type, chat_id, user_id, or user_email)',
                           tool_call_id=tool_call_id, role="tool")
            ]})
        
        # For task_link email type, directly fetch candidates from the database
        if email_type == "task_link":
            
            db = chat_db()
            logging.info("Fetching candidates with status ACCEPTED for chat_id: %s", chat_id)
            candidates_data = db.resumeData.find({"status": "ACCEPTED", "chat_id": chat_id}).to_list(length=500)
            logging.info(candidates_data)
            
            if not candidates_data:
                return Command(update={'task_id': "", 'messages': [
                    ToolMessage(content='No accepted candidates found for this chat session.', 
                               tool_call_id=tool_call_id, role="tool")
                ]})
            
            candidates = [candidate["parsed_resume"] for candidate in candidates_data]
            logging.info("Found %d accepted candidates", len(candidates))
   
    # try:
    #     logging.info("calling the sending mail tool")
    #     email_type = state['email_type']
    #     chat_id = state['chat_id']

    #     if email_type == "task_link":
    #         db = chat_db()
    #         candidates_data = await db.resumeData.find({"status": "ACCEPTED","chat_id":chat_id}).to_list(length=500)
            
    #         candidates = [candidate["parsed_resume"] for candidate in candidates_data]

    #     #if state["db_query_result"]["type"] == "resumes":
    #     #    candidates = [candidate["parsed_resume"] for candidate in state["db_query_result"]["data"]]
    #     #else:
    #     #    return Command(update={'task_id': "",'messages': [ToolMessage(content='No candidates fetched, use `candidate_fetching_db_tool` to fetch candidates `Name` and `Email`', tool_call_id=tool_call_id, role="tool")]})
        
        logging.info("proceeding with next")
        if email_type != "custom_email":
            email_material = state['email_material'].format(**input_data)
        else:
            email_material = input_data['custom_email_body']
        logging.info("proceeding with next data")    

        data = {"candidates": candidates, "email_type": email_type, "input_data": input_data, "chat_id": state['chat_id'], "id": state['chat_id'][:4]}
        logging.info(f"got this data {data}")
        task_id = await task_db.insert_task(user_id=state['user_id'], chat_id=state['chat_id'], task_type="sending_mail", status="PENDING", metadata=None)
        logging.info("Sending mail task_id: %s", task_id)
        user = await user_db.get_user_by_email(user_email)
        logging.info(f"got the user{user}")
        await mail_utils.send_bulk_email(data, user)

        return Command(update={'task_id': task_id, 'email_material': email_material, 'messages': [ToolMessage(content='Buddy! Done sending those emails!, what else can I do for you?', tool_call_id=tool_call_id, role="tool")]})
    except Exception as e:
        return Command(update={'task_id': "",'messages': [ToolMessage(content=f'Error: {e}', tool_call_id=tool_call_id, role="tool")]})
    
async def candidate_fetching_db_tool(tool_call_id: Annotated[str, InjectedToolCallId] ,chat_id: Annotated[str, InjectedState('chat_id')], user_id: Annotated[str, InjectedState('user_id')], message:str):
    '''
    This tools is used to fetches information based on the user's requirements.
    message: str - user requirements.
    '''
    try:

        db = chat_db()
        logging.info("Fetching candidates with status ACCEPTED for chat_id: %s", chat_id)
        candidates_data = db.resumeData.find({"status": "ACCEPTED", "chat_id": chat_id}).to_list(length=500)
        logging.info()
        candidates = [candidate["parsed_resume"] for candidate in candidates_data]
                        
        # logging.info("Fetching data from the database for message: %s and chat_id: %s", message, chat_id)
        # db_query_result = await user_query(message + "\n" + "Fetch candidates **Name** and **Email** and **_id**, **along with above mentioned requirements**", chat_id, 'resume', user_id).fetch_data()
        # print(db_query_result)
        data = {"type": 'resumes', "data": candidates}
        logging.info("Data fetched from the database: %s", candidates[1])
        return Command(update = {"db_query_result": data, "messages": [ToolMessage(content="Successfully fetched the data from the database, Is there anything else you want to know?", tool_call_id=tool_call_id, role="tool")]})
    except Exception as e:
        return Command(update = {"messages": [ToolMessage(content=f'Error: {e}', tool_call_id=tool_call_id, role="tool")]})

async def email_assistant(state: MainState):
    llm = LangGraphClient()
    mail_attachment = False
    sys_msg = SystemMessage(content=EMAIL_PROMPT.format(messages=state["messages"]))
    assistant = llm.create_assistant(response_format=EmailStructuredOutput)
    response = assistant.invoke([sys_msg])
    logging.info("Response received from email assistant")
    if response['parsed'].email_type in ["task_attachment", "offer_letter"]:
        mail_attachment = True
    token_cost_usage = llm.total_token_cost_calculator(response['raw'].usage_metadata)
    await user_db.update_user_token_cost(state["user_id"], token_cost_usage["token_usage"], token_cost_usage["cost"], "chat")
    return {'email_type': response['parsed'].email_type, 'mail_attachment': mail_attachment, 'messages': AIMessage(response['parsed'].messages, name="chatur")}

async def sending_mail(state: MainState):
    logging.info("ending the email")
    llm = LangGraphClient()
    prompt_body = mapping_function(state['email_type'])
    sys_msg = SystemMessage(content=prompt_body['prompt'])
    mail_tools = [sending_mail_tool, candidate_fetching_db_tool]
    # logging.info("Tool signatures: %s", [inspect.signature(tool) for tool in mail_tools])
    logging.info("assistant created")
    assistant = llm.create_assistant(tools=mail_tools)
    response = assistant.invoke([sys_msg] + state['messages'])
    token_cost_usage = llm.total_token_cost_calculator(response.usage_metadata)
    await user_db.update_user_token_cost(state["user_id"], token_cost_usage["token_usage"], token_cost_usage["cost"], "chat")
    return {"messages": [response], "email_material": prompt_body['template']}

def sending_mail_condition(state: MainState):
    if state['email_type']:
        return "sending_mail"
    return END

def mail_asking_db_node_condition(state: MainState):
    if state["messages"][-1].content == "db_assistant":
        return "db_assistant"
    return END


# ------------------------------ TESTING THE MAIL ASSISTANT ------------------------------

# from langgraph.graph import StateGraph, START
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.messages import HumanMessage
# from langgraph.prebuilt import ToolNode
# import asyncio
# from app.services.model_format.chatbot_format import MainOutputState
# from app.services.chatbot.db_node import db_assistant

# if __name__ == "__main__":
#     from app.config.db_config import start_db

#     async def build_mail_graph():
#         builder = StateGraph(MainState, MainOutputState)
#         mail_tools = [sending_mail_tool]
#         builder.add_node("mail_assistant", email_assistant)
#         builder.add_node("db_assistant", db_assistant)
#         builder.add_node("mail_tools", ToolNode(mail_tools))

#         builder.add_edge(START, "mail_assistant")
#         builder.add_conditional_edges("mail_assistant", sending_mail_condition, ["mail_tools", END])
#         builder.add_edge("mail_tools", "mail_assistant")
#         builder.add_conditional_edges("mail_assistant", mail_asking_db_node_condition, ["db_assistant", END])
#         builder.add_edge("db_assistant", END)
        
#         return builder.compile()
    
#     async def test_mail_assistant(prompt="Hi, I want to send an email to the candidates"):
#         await start_db()
        
#         graph = await build_mail_graph()
#         config = {"configurable": {"thread_id": "3"}}
        
#         test_state = {
#             "messages": [HumanMessage(content=prompt)],
#             "user_id": "67d44a9e90a12565210d0a2a", 
#             "chat_id": "456",
#             "email_type": None
#         } 
#         messages = await graph.ainvoke(test_state)
    
#         print("\n=== TEST RESULTS ===")
#         print(f"Input: {prompt}")
#         print(f"Output: {messages}")
#         for m in messages['messages']:
#             m.pretty_print()    
#         return messages
    
#     asyncio.run(test_mail_assistant())
    