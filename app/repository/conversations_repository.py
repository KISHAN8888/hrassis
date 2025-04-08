from typing import Dict, Literal
import logging
from beanie import PydanticObjectId
from pydantic import BaseModel
from app.models.conversations_model import ConversationSchema as conversation_schema
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)

class ConversationBasicSchema(BaseModel):
    user_email: str
    chat_id: str
    type: str

class ConversationsRepository:
    """CRUD operations for conversations models"""
    @staticmethod
    async def check_conversation_by_user(user_email: str, chat_id: str, type: str, candidate_email: str) -> Dict:
        """Check if a conversation exists for a user"""
        conversation = await conversation_schema.find_one({"user_email": user_email, "chat_id": chat_id, "type": type, "candidate_email": candidate_email}, projection_model=ConversationBasicSchema)
        if not conversation:
            logging.error("No conversation found for user: %s", user_email)
            return None
        return conversation.model_dump()

    @staticmethod
    async def insert_conversation(user_id: str, chat_id: str, user_email: str, candidate_email: str, type: str, messages: Dict, mode: Literal['Email','WhatsApp'] = 'Email') -> Dict:
        """Create a new conversation"""
        try:
            conversation = conversation_schema(user_id=PydanticObjectId(user_id), chat_id=chat_id, user_email=user_email, candidate_email=candidate_email, type=type, messages=messages, mode=mode)
            await conversation.insert()
            logging.info("Conversation created successfully: %s", chat_id)
            return str(conversation.id)
        except Exception as e:
            logging.error("Error creating conversation: %s", e)
            return None
    
    @staticmethod
    async def update_conversation(user_email: str, chat_id: str, type: str, messages: Dict, candidate_email: str) -> Dict:
        """Update a conversation"""
        conversation = await conversation_schema.find_one({"user_email": user_email, "chat_id": chat_id, "type": type, "candidate_email": candidate_email}).update_one({"$push": {"messages": messages}})
        logging.info("Conversation updated successfully: %s", chat_id)
        return None
        

    @staticmethod
    async def find_message_by_id(message_id: str) ->Dict:
        """Find a  user's message by its ID"""
        try:
            message = await conversation_schema.find_one({"messages.message_id": message_id})

            if not message:
                logging.error("Message not found for ID: %s", message_id)
                raise ValueError("Message not found")
            
            return message.model_dump()
        except Exception as e:
            logging.error("Error finding message by ID: %s", str(e))
            raise e
        
    @staticmethod
    async def insert_recieved_message(user_email: str, candidate_email: str, subject: str, content: str, message_id: str) -> Dict:
        """Insert a received message into a conversation"""
        try:
            message = {
                "message_id": message_id,
                "subject": subject,
                "content": content,
                "status": False,  
                "sent_by": "candidate", 
                "created_at": datetime.utcnow()
            }

             # Check if a conversation exists between the HR and the candidate
            conversation = await conversation_schema.find_one(
                {"user_email": user_email, "candidate_email": candidate_email}
            )

            if not conversation:
                logging.error("No conversation found for user: %s", user_email)
                raise ValueError("No conversation found")
            
            conversation.messages.append(message)
            conversation.updated_at = datetime.now(timezone.utc)
            inserted_msg = await conversation.save()

            if not inserted_msg:
                logging.error("Message not inserted")
                raise ValueError("Message not inserted")
        
            return inserted_msg.model_dump()
        except Exception as e:
            logging.error("Error inserting message: %s", str(e))
            raise e
        
    
        
    
    