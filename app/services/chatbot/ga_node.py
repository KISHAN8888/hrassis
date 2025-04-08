import logging
from langchain_core.messages import SystemMessage
from app.services.prompts.chatbot_prompts import GA_PROMPT
from app.services.model_format.chatbot_format import MainState
from app.repository.user_repository import UserRepository as user_db
from app.helpers.ai_helper import LangGraphClient

logging.basicConfig(level=logging.INFO)

async def general_assistant(state: MainState):
    sys_msg = SystemMessage(content=GA_PROMPT.format(messages=state['messages']), name="chatur")
    llm = LangGraphClient()
    assistant = llm.create_assistant()
    response = assistant.invoke([sys_msg])
    logging.info("General assistant response: %s", response)
    token_cost_usage = llm.total_token_cost_calculator(response.usage_metadata)
    await user_db.update_user_token_cost(state["user_id"], token_cost_usage["token_usage"], token_cost_usage["cost"], "chat")
    return {"messages": [response]}

# --------------- TESTING THE GENERAL ASSISTANT ---------------
# if __name__ == "__main__":
    # from app.config.db_config import start_db
    # from langgraph.graph import StateGraph, END, START
    # from langchain_core.messages import HumanMessage
    # from langgraph.prebuilt import ToolNode
    # import asyncio
    # from app.services.model_format.chatbot_format import MainOutputState
    # import sys

    # def build_ga_graph():
    #     builder = StateGraph(MainState, MainOutputState)
    #     builder.add_node("ga_assistant", general_assistant)
    #     builder.add_edge(START, "ga_assistant")
    #     return builder.compile()

    # async def test_general_assistant(prompt="Hi, I am a recruiter, I need a JD for a job in a company called 'ABC'"):
    #     await start_db()
    #     graph = build_ga_graph()
    #     config = {"configurable": {"thread_id": "3"}}
    #     test_state = {
    #         "messages": [HumanMessage(content=prompt)],
    #         "user_id": "67d44a9e90a12565210d0a2a", 
    #     }
    #     messages = await graph.ainvoke(test_state, config)

    #     print("\n=== TEST RESULTS ===")
    #     print(f"Input: {prompt}")
    #     print("\nOutput messages:")
    #     for m in messages['messages']:
    #         m.pretty_print()

    #     return messages
    
    # asyncio.run(test_general_assistant())
