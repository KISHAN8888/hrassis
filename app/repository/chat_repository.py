from typing import Dict
import logging, os, asyncio
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.http_responses import Responses
from app.config.env_config import env_config
from app.services.chatbot.chatbot import build_main_graph

logging.basicConfig(level=logging.INFO)

class ChatRepository:
    @staticmethod
    async def get_chat_checkpoint(chat_id: str) -> Dict:
        "Get a chat checkpoint."
        logging.info("Getting chat checkpoint: %s", chat_id)
        client = AsyncIOMotorClient(env_config.db.db_url)
        checkpointer = AsyncMongoDBSaver(client=client, db_name=env_config.db.db_name, checkpoint_collection_name="chat_checkpoints")
        checkpoint = await checkpointer.aget_tuple({"configurable": {"thread_id": chat_id}})
        checkpoint = checkpoint.checkpoint['channel_values']
        if not checkpoint:
            logging.error("Chat checkpoint not found: %s", chat_id)
            return Responses.error(404, message="Chat checkpoint not found")
        return checkpoint
    
    @staticmethod
    async def get_chats(chat_id: str):
        try:
            logging.info("Getting chats: %s", chat_id)
            messages = list()
            client = AsyncIOMotorClient(env_config.db.db_url)
            checkpointer = AsyncMongoDBSaver(client=client, db_name=env_config.db.db_name, checkpoint_collection_name="chat_checkpoints")
            checkpoints = await checkpointer.aget_tuple({"configurable": {"thread_id": chat_id}})
            checkpoints = checkpoints.checkpoint['channel_values']['messages']
            if not checkpoints:
                logging.error("Chat checkpoint not found: %s", chat_id)
                return Responses.error(404, message="Chat checkpoint not found")
            for checkpoint in checkpoints:
                if checkpoint.type != "tool" and checkpoint.content != "":
                    messages.append({"type": checkpoint.type, "content": checkpoint.content})
            return messages
        except Exception as e:
            logging.error("Error in get_chats: %s", str(e))
            return Responses.error(500, f'Error fetching chats: {str(e)}')
        
    @staticmethod
    async def update_resume_parsed_to_true(chat_id: str):
        try:
            logging.info("Updating resume parsed to true: %s", chat_id)
            chatbot =await build_main_graph()
            await asyncio.to_thread(lambda: chatbot.update_state({"configurable": {"thread_id": chat_id}}, {"resume_parsed": True}))
        except Exception as e:
            logging.error("Error in update_resume_parsed_to_true: %s", str(e))
            return Responses.error(500, f'Error updating resume parsed to true: {str(e)}') 
        
    @staticmethod
    async def update_created_jd_id(chat_id: str, created_jd_id: str):
        try:
            logging.info("Updating created jd id: %s", chat_id)
            chatbot =await build_main_graph()
            await asyncio.to_thread(lambda: chatbot.update_state({"configurable": {"thread_id": chat_id}}, {"created_jd_id": created_jd_id}))
        except Exception as e:
            logging.error("Error in update_created_jd_id: %s", str(e))
            return Responses.error(500, f'Error updating created jd id: {str(e)}') 
    
    @staticmethod
    async def update_parsed_jd_id(chat_id: str, parsed_jd_id: str):
        try:
            logging.info("Updating parsed jd id: %s", chat_id)
            chatbot =await build_main_graph()
            await asyncio.to_thread(lambda: chatbot.update_state({"configurable": {"thread_id": chat_id}}, {"parsed_jd_id": parsed_jd_id}))
        except Exception as e:
            logging.error("Error in update_parsed_jd_id: %s", str(e))
            return Responses.error(500, f'Error updating parsed jd id: {str(e)}') 
        
        
        
    @staticmethod
    async def get_all_chats(user_id:str):
        try:
            logging.info("Getting all chats: %s", user_id)
            
        except Exception as e:
            logging.error("Error in get_all_chats: %s", str(e))
            