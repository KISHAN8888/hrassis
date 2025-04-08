import logging, asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from app.helpers.ai_helper import LangGraphClient
from app.services.model_format.chatbot_format import MainState, MainOutputState
from app.services.model_format.chatbot_format import RouterResponse
from app.services.prompts.chatbot_prompts import ROUTE_PROMPT
from app.repository.user_repository import UserRepository as user_db
from app.services.chatbot.jd_node import jd_assistant, generate_jd
from app.services.chatbot.resume_node import rp_assistant, rescreening_tool, rescreen_to_db_node_condition, rp_rescreening, rp_node_condition, candidate_fetching_db_tool_for_resume
from app.services.chatbot.ga_node import general_assistant
from app.services.chatbot.db_node import db_assistant, search_db
from app.services.chatbot.mail_node import email_assistant, sending_mail_tool, candidate_fetching_db_tool, sending_mail, sending_mail_condition
from app.services.chatbot.assessment_node import assessment_assistant, generate_assessment, customize_assessment, publish_assessment
from app.config.env_config import env_config

logging.basicConfig(level=logging.INFO)

# ------------------------------------------ Summarize Conversation ------------------------------------------
async def summarize_conversation(state: MainState):
    """ This function summarizes the conversation to date. """
    summary = state.get("summary", "")
    llm = LangGraphClient(model_name="o3-mini").create_assistant()
    if summary:
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Include key mentions regarding the details mentioned by the user in the conversation to date"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above, taking into the key details mentioned by the user previously:"

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = await llm.ainvoke(messages)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}
        
def summary_should_continue(state: MainState):
    """Return the next node to execute."""
    messages = state["messages"]
    if len(messages) > 4:
        return "summarize_conversation"
    return "entry_route"

# ------------------------------------------ Entry Route ------------------------------------------
async def entry_route(state: MainState):
    """ This function routes the user to the appropriate assistant based on their message. """
    llm = LangGraphClient(model_name="o3-mini")
    system_message = SystemMessage(content=ROUTE_PROMPT)
    assistant = llm.create_assistant(response_format=RouterResponse)
    response = await assistant.ainvoke([system_message]+ state["messages"])
    logging.info("Response of the entry route: %s", response)
    token_cost_usage = llm.total_token_cost_calculator(response['raw'].usage_metadata)
    await user_db.update_user_token_cost(state["user_id"], token_cost_usage["token_usage"], token_cost_usage["cost"], "chat")
    return {"selected_route": response['parsed'].selected_route}

def which_way_to_go(state: MainState):
    route = state.get("selected_route")
    if route == "jd_assistant":
        return "jd_assistant"
    elif route == "rp_assistant":
        return "rp_assistant"
    elif route == "general_assistant":
        return "general_assistant"
    elif route == "db_assistant":
        return "db_assistant"  
    elif route == "email_assistant":
        return "email_assistant"
    elif route == "assessment_assistant":
        return "assessment_assistant"
    
# ------------------------------------------ MAIN GRAPH ------------------------------------------

async def build_main_graph():
    builder = StateGraph(MainState, MainOutputState)

    # Define tools for each assistant
    jd_tools = [generate_jd]
    rp_tools = [rescreening_tool, candidate_fetching_db_tool_for_resume]
    db_tools = [search_db]
    email_tools = [sending_mail_tool, candidate_fetching_db_tool]
    assessment_tools = [generate_assessment, customize_assessment, publish_assessment]
    
    # Add nodes
    builder.add_node("summarize_conversation", summarize_conversation)
    builder.add_node("entry_route", entry_route)
    
    # JD nodes
    builder.add_node("jd_assistant", jd_assistant)
    builder.add_node("jd_tools", ToolNode(jd_tools))
    
    # Resume parsing nodes
    builder.add_node("rp_assistant", rp_assistant)
    builder.add_node("rescreening", rp_rescreening)
    builder.add_node("rp_tools", ToolNode(rp_tools))
    
    # General assistant node
    builder.add_node("general_assistant", general_assistant)
    
    # Database assistant nodes
    builder.add_node("db_assistant", db_assistant)
    builder.add_node("db_tools", ToolNode(db_tools))
    
    # Email assistant nodes
    builder.add_node("email_assistant", email_assistant)
    builder.add_node("sending_mail", sending_mail)
    builder.add_node("email_tools", ToolNode(email_tools))
    
    # Assessment assistant nodes (NEW)
    builder.add_node("assessment_assistant", assessment_assistant)
    builder.add_node("assessment_tools", ToolNode(assessment_tools))

    # Add edges
    builder.add_edge(START, "entry_route")
    
    # Route conditional edges
    builder.add_conditional_edges("entry_route", which_way_to_go, [
        "jd_assistant", 
        "rp_assistant", 
        "general_assistant", 
        "db_assistant", 
        "email_assistant",
        "assessment_assistant"  # Added assessment route
    ])
    
    # JD edges
    builder.add_conditional_edges("jd_assistant", LangGraphClient().create_tool_condition("jd_tools"), ["jd_tools", END])
    builder.add_edge("jd_tools", "jd_assistant")
    
    # RP edges
    builder.add_conditional_edges("rp_assistant", rp_node_condition, ["rescreening", END])
    builder.add_conditional_edges("rescreening", LangGraphClient().create_tool_condition("rp_tools"), ["rp_tools", END])
    builder.add_edge("rp_tools", "rescreening")
    builder.add_conditional_edges("rescreening", rescreen_to_db_node_condition, ["db_assistant", END])
    
    # General assistant edge
    builder.add_edge("general_assistant", END)
    
    # Email edges
    builder.add_conditional_edges("email_assistant", sending_mail_condition, ["sending_mail", END])
    builder.add_conditional_edges("sending_mail", LangGraphClient().create_tool_condition("email_tools"), ["email_tools", END])
    builder.add_edge("email_tools", "sending_mail")
    
    # DB edges
    builder.add_conditional_edges("db_assistant", LangGraphClient().create_tool_condition("db_tools"), ["db_tools", END])
    builder.add_edge("db_tools", "db_assistant")
    
    # Assessment edges (NEW)
    builder.add_conditional_edges(
        "assessment_assistant", 
        LangGraphClient().create_tool_condition("assessment_tools"), 
        ["assessment_tools", END]
    )
    builder.add_edge("assessment_tools", "assessment_assistant")
    
    # Set up MongoDB checkpointing
    mongo_client = AsyncIOMotorClient(env_config.db.db_url)
    checkpointer = AsyncMongoDBSaver(client=mongo_client, db_name=env_config.db.db_name, checkpoint_collection_name="chat_checkpoints")
    
    logging.info("Compiling graph- %s", MainState)
    main_graph = builder.compile(checkpointer=checkpointer)
    return main_graph