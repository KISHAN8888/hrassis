import logging
import asyncio
from langchain_core.messages import HumanMessage
from app.config.db_config import start_db
from app.services.chatbot.chatbot import build_main_graph

logging.basicConfig(level=logging.INFO)

async def main():
    await start_db()
    main_graph = await build_main_graph()
    config = {"configurable": {"thread_id": "3"}}
    
    # Initial state
    state = {
    "messages": [],
    "resume_parsed": True,
    "created_jd_id": "67a0ea9b6b8baff368224fb1",
    "parsed_jd_id": "67a0ce087eedb97fccd8aaaa",
    "user_id": "67d44a9e90a12565210d0a2a",
    "chat_id": "456",
    "summary": "",  # Add empty summary
    "task_id": None,  # Add None for optional fields
    "db_query_result": {},
    "assessment_id": None,
    "assessment_status": None
}
    
    print("Chat started! Type 'exit' to quit.")
    
    # Chat loop
    while True:
        # Get user input
        user_input = input("\n> ")
        if user_input.lower() == 'exit':
            break
            
        # Add user message to state
        state["messages"] = [HumanMessage(content=user_input)]
        
        # Process message through graph
        result = await main_graph.ainvoke(state, config)
        
        # Update state with result
        state = result
        
        # Print responses
        print("\nResponse:")
        for message in result["messages"]:
            if hasattr(message, 'content'):
                print(f"{message.content}")

if __name__ == "__main__":
    asyncio.run(main())



# import logging
# import asyncio
# from langchain_core.messages import HumanMessage, ToolMessage
# from app.config.db_config import start_db
# from app.services.chatbot.chatbot import build_main_graph

# logging.basicConfig(level=logging.INFO)

# async def main():
#     await start_db()
#     main_graph = await build_main_graph()
#     config = {"configurable": {"thread_id": "3"}}
    
#     # Initial state
#     state = {
#         "messages": [],
#         "resume_parsed": True,
#         "created_jd_id": "67a0ea9b6b8baff368224fb1",
#         "parsed_jd_id": "67a0ce087eedb97fccd8aaaa", 
#         "user_id": "67d44a9e90a12565210d0a2a", 
#         "chat_id": "456"
#     }
    
#     print("Chat started! Type 'exit' to quit.")
    
#     # Chat loop
#     while True:
#         # Get user input
#         user_input = input("\n> ")
#         if user_input.lower() == 'exit':
#             break
            
#         # Add user message to state
#         state["messages"] = [HumanMessage(content=user_input)]
        
#         try:
#             # Process message through graph
#             print("Processing message...")
#             result = await main_graph.ainvoke(state, config)
            
#             # Update state with result
#             state = result
            
#             # Process and handle any tool calls
#             for message in state["messages"]:
#                 if hasattr(message, 'tool_calls') and message.tool_calls:
#                     print(f"Found tool calls: {message.tool_calls}")
                    
#                     # Check if we already have tool responses
#                     has_tool_responses = False
#                     for msg in state["messages"]:
#                         if isinstance(msg, ToolMessage):
#                             has_tool_responses = True
#                             break
                    
#                     # If no tool responses exist and we need them, add empty ones
#                     if not has_tool_responses:
#                         for tool_call in message.tool_calls:
#                             tool_call_id = tool_call.get('id', None)
#                             if tool_call_id:
#                                 # Add a placeholder tool response to satisfy OpenAI's requirement
#                                 state["messages"].append(
#                                     ToolMessage(
#                                         content="Tool response placeholder",
#                                         tool_call_id=tool_call_id
#                                     )
#                                 )
#                                 print(f"Added placeholder response for tool call: {tool_call_id}")
            
#             # Print responses
#             print("\nResponse:")
#             for message in result["messages"]:
#                 if hasattr(message, 'content') and not isinstance(message, ToolMessage):
#                     print(f"{message.content}")
                    
#         except Exception as e:
#             print(f"\nError: {e}")
#             logging.error(f"Error in chat processing: {e}", exc_info=True)

# if __name__ == "__main__":

#     asyncio.run(main())


