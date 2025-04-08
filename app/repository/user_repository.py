"User model CRUD operations - Update any particular user details and delete user is yet to be implemented"
from typing import Optional, List, Any, Dict
import logging
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from app.models.user_model import UserSchema as user_schema
from app.models.user_model import ExternalService
from app.models.order_model import OrderSchema as order_schema
from app.utils.http_responses import Responses
from uuid import uuid4

class UserBasicDetails(BaseModel):
    user_id: PydanticObjectId = Field(alias="_id")
    email: str
    name: str
    company_name: Any
    oauth_refresh_token: Any
    enabled_services: List[ExternalService]
    chats: List[str]
    role: str

class FetchUserPassword(BaseModel):
    email: str
    name: str
    password: Any

class UserRepository:
    "CRUD operations for user model"
    @staticmethod
    async def get_user_by_email(email: str) -> Dict:
        "Get a user by their email."
        logging.info("Getting user by email: %s", email)
        try:
            user = await user_schema.find_one({"email": email}, projection_model=UserBasicDetails)
            if not user:
                logging.error("User not found for email: %s", email)
                return None
            user_dict = user.model_dump()
            user_dict["user_id"] = str(user_dict["user_id"]) 
            return user_dict
        except Exception as e:
            logging.error("Error getting user by email: %s", str(e))
            return Responses.error(500, message=str(e))
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Dict:
        "Get a user by their ID."
        logging.info("Getting user by ID: %s", user_id)
        user = await user_schema.find_one({"_id": PydanticObjectId(user_id)}, projection_model=UserBasicDetails)
        if not user:
            logging.error("User not found for ID: %s", user_id)
            return None
        user_dict = user.model_dump()
        user_dict["user_id"] = str(user_dict["user_id"])
        return user_dict
    
    @staticmethod 
    async def get_user_by_email_with_password(email: str) -> Dict:
        "Get a user by their email with their password."
        logging.info("Getting user by email with password: %s", email)
        user = await user_schema.find_one({"email": email}, projection_model=FetchUserPassword)
        if not user:
            logging.error("User not found for email: %s", email)
            return Responses.error(400, message="User not found for password retrieval")
        return user.model_dump()
   
    @staticmethod
    async def get_user_token_cost_usage(email: str) -> Dict:
        "Get a user's token, cost usage."
        logging.info("Getting user's token, cost usage: %s", email)
        user = await user_schema.find_one({"email": email})
        if not user:
            logging.error("User not found for email: %s", email)
            return Responses.error(400, message="User not found for token cost usage retrieval")
        return {"user_id": str(user.id), "token_usage": user.token_usage.model_dump(), "cost": user.cost.model_dump()}
    
    @staticmethod
    async def insert_user(email: str, name: str,company_name: Optional[str] = None,password: Optional[str] = None, oauth_refresh_token: Optional[str] = None, enabled_services: Optional[List[ExternalService]] = []) -> Dict:
        """Create a new user."""
        try: 
            user = user_schema(
                email=email,
                name=name,
                company_name=company_name,
                password=password,
                oauth_refresh_token=oauth_refresh_token,
                enabled_services=enabled_services
            )

            await user.insert()
            logging.info("User inserted successfully: %s", str(user.id))

            return {"user_id": str(user.id), "email": user.email, "name": user.name,"role":user.role}

        except Exception as e:
            logging.error("Error inserting user: %s", str(e))
            return Responses.error(500, message=str(e))
        
    @staticmethod
    async def update_users_services(user_id: str, services: List[ExternalService], oauth_refresh_token: Optional[str] = None) -> bool:
        "Update a user's services."
        try:
            logging.info("Updating user's services: %s", user_id)
            
            update_query = {
                "$addToSet": {"enabled_services": {"$each": services}},
            }

            if oauth_refresh_token:
                update_query["$set"] = {"oauth_refresh_token": oauth_refresh_token}

            result = await user_schema.find_one(
                {"_id": PydanticObjectId(user_id)}
            ).update(update_query)

            if not result:
                logging.error("User not found or update failed for ID: %s", user_id)
                return False
            
            return True

        except Exception as e:
            logging.error("Error updating user services: %s", str(e))
            return False





            
    @staticmethod
    async def update_user_token_cost(user_id: str, token_usage: int, cost: float, usage_type: str) -> Dict:
        "Update a user's token, cost usage."
        logging.info("Updating user's token, cost usage: %s", user_id)
        valid_types = {"jd": "jd_tokens", "chat": "chat_tokens", "resume": "resume_tokens", "assessment": "assessment_tokens",
            "conversation": "conversation_tokens"}

        if usage_type not in valid_types:
            logging.error("Invalid type: %s", usage_type)
            return Responses.error(400, message=f"Invalid type: {usage_type}")
        
        token_field = valid_types[usage_type]
        cost_field = f"{usage_type}_cost"
        
        try:
            update_query = {"$inc": {f"token_usage.{token_field}": token_usage, f"cost.{cost_field}": cost, "token_usage.total_tokens": token_usage,
                    "cost.total_cost": cost}}

            user = await user_schema.find_one({"_id": PydanticObjectId(user_id)}).update(update_query)
            if not user:
                logging.error("User not found for ID: %s", user_id)
                return Responses.error(404, message="User not found")
                
            logging.info("User's token, cost usage updated successfully: %s", user_id)
            return True
        
        except Exception as e:
            logging.error("Error updating user token cost: %s", str(e))
            return Responses.error(500, message=f"Error updating token usage: {str(e)}")

    @staticmethod
    async def update_user_chat_id(user_id: str) -> Dict:
        "Update a user's chat ID."
        logging.info("Updating user's chat ID: %s", user_id)
        chat_id = str(uuid4())
        await user_schema.find_one({"_id": PydanticObjectId(user_id)}).update({"$push": {"chats": chat_id}})
        return chat_id
    
    
    @staticmethod
    async def create_order(user_id:str, credit:int, amount:int,order_id:str,payment_source:str):
        try:
            # print(amount,credit,user_id,order_id,"Details")
            print()
            orders = order_schema(user_id=user_id, credit=float(credit), amount=float(amount), status="pending", order_id=order_id,payment_source=payment_source)
            await orders.insert()
            logging.info("Order inserted successfully: %s", str(orders.id))
            return str(orders.order_id)
        except Exception as e:
            logging.error("Error in inserting orderId: %s", str(e))
            return Responses.error(500, message=str(e))
            
    @staticmethod
    async def update_status(order_id,status):
        try:
            update_order_status = await order_schema.find_one(order_id=order_id).update({"$set": {"status": status}})
            if not update_order_status:
                return Responses.error(404, message="Order not found")
            return True
        except Exception as e:
            logging.error("Error in updating order status: %s", str(e))
            return Responses.error(500, message=str(e))
            
    @staticmethod
    async def update_credits(order_id,user_id):
        try:
            get_credits = await order_schema.find_one(order_id=order_id).to_list()
            if not get_credits:
                return None
            print(get_credits,"credits:::::::::::::::::::::")
            credits = get_credits['credits']
            update_user_credits = await user_schema.find_one({"_id": PydanticObjectId(user_id)}).update({"$inc": {"credits": credits}})
            if not update_user_credits:
                return None
            return True
        except Exception as e:
            logging.error("Error in updating credits: %s", str(e))
            return Responses.error(500, message=str(e))
        
        
    @staticmethod
    async def update_password(user_id:str,password:Optional[str]):
        try:
            print("Varun",password)
            update_user_password = await user_schema.find_one({"_id": PydanticObjectId(user_id)}).update({"$set": {"password": password}})
            if not update_user_password:
                return None
            return True
        except Exception as e:
            logging.error("Error in updating password: %s", str(e))
            return Responses.error(500, message=str(e))
            
# ----------------------------- Testing -------------------------------
import asyncio

async def test_update_user_token_cost():
        """
        Test function for updating user token cost

        Usage:
        - Make sure your database is running
        - Run this script with a valid user_id from your database
        """
    # Initialize database connection
        from app.config import start_db
        await start_db()

        # Test parameters - replace with valid values from your database
        user_id = "67d44a9e90a12565210d0a2a"  # Replace with a valid user ID
        token_usage = 100
        cost = 0.05
        usage_type = "chat"  # One of: "jd", "chat", "resume", "assessment", "conversation"

        try:
            print(f"Updating token usage for user {user_id}")
            print(f"Adding {token_usage} tokens and ${cost} cost for {usage_type}")
            
            # Call the method being tested
            result = await UserRepository.update_user_token_cost(
                user_id=user_id,
                token_usage=token_usage,
                cost=cost,
                usage_type=usage_type
            )
            
            # Display results
            if "status" in result and result["status"] == "error":
                print(f"❌ Error: {result['message']}")
            else:
                print("✅ Update successful!")
                print(f"Updated user ID: {result['user_id']}")
                print(f"Token usage: {result['token_usage']}")
                print(f"Cost: {result['cost']}")
                
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        finally:
            # Close database connection if needed
            pass

        if __name__ == "__main__":
        # Run the test
            asyncio.run(test_update_user_token_cost())
            