import logging
from fastapi import Request, Depends
from app.utils.mail_utils import MailUtils as mail_utils
from app.repository.user_repository import UserRepository as user_db
from fastapi import Request, Depends, HTTPException, BackgroundTasks
# from app.repository.conversations_repository import ConversationsRepository as conversations_db
from app.helpers.mail_helper import MailHelper as mail_helper
from app.utils.http_responses import Responses
from app.services.mail_services import EmailProcessor as email_sending_service
from app.middlewares.auth_middleware import AuthMiddleware as auth_middleware
import base64
import json

logging.basicConfig(level=logging.INFO)

class MailControllers:
    @staticmethod
    async def send_bulk_email_endpoint(request: Request, user=Depends(auth_middleware)):
        "Send bulk email function"
        user = await user_db.get_user_by_email(user["email"])
        await mail_utils.send_bulk_email(request, user)

    @staticmethod
    async def watchEmail(user = Depends(auth_middleware.authenticate_user)):
        try:
            user = await user_db.get_user_by_email(user["email"])
            

            access_token: str = await mail_helper.generate_access_token(user["oauth_refresh_token"])

            if not access_token:
                raise HTTPException(status_code=400, detail="Access token is required")
        
            service = await mail_helper.get_gmail_service(access_token)

            request_body = {
                "labelIds": ["INBOX"],
                "topicName": f"projects/regal-cycling-441610-j6/topics/rohit"
            }

            response = service.users().watch(userId="me", body=request_body).execute()
            return {"message": "Watch request set successfully", "historyId": response["historyId"]}

        except Exception as e:
            return Responses.error(500, message=f'Error occured in watching email function - {str(e)}')
        
    @staticmethod
    async def google_webhook(request: Request, backgroundTask: BackgroundTasks):
        try:
            data = await request.json()
            messageData = data.get("message", {}).get("data")

            if not messageData:
                logging.error("Missing required fields: messageData")
                return Responses.error(400, message="Missing required fields: messageData")
            
            decodedMessage = base64.b64decode(messageData).decode("utf-8")
            message_json = json.loads(decodedMessage)
            user_email = message_json.get("emailAddress")
            
            await backgroundTask.add_task(email_sending_service.process_emails, user_email)

            # TODO : Send message to the candidate check the flow once and add ai logic..

        
        except Exception as e:
            return Responses.error(500, message=f'Error occured in watching email function - {str(e)}')

