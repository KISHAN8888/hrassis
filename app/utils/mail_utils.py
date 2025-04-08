import logging
from fastapi import Request
from app.repository.conversations_repository import ConversationsRepository as conversations_db
from app.helpers.mail_helper import MailHelper as mail_helper
from app.utils.http_responses import Responses
from app.services.mail_services import EmailProcessor as email_sending_service

class MailUtils:
    @staticmethod
    async def send_bulk_email(candidate_data, user):
        "Send bulk email function"
        try:
            logging.info(candidate_data,"candidate_data::::::")
            access_token: str = await mail_helper.generate_access_token(user["oauth_refresh_token"])
            if not access_token:
                logging.error("Failed to generate access token")
                return Responses.error(400, message="Failed to generate access token")
            # data = await candidate_data.json()
            # print(data,"data:::::SendBulk:")
            candidates = candidate_data.get("candidates", [])
            chat_id = candidate_data.get("chat_id", None)
            email_type = candidate_data.get("email_type")
            input_data = candidate_data.get("input_data", {})
            id = candidate_data.get("id", "JD001")

            if not candidates or not email_type:
                logging.error("Missing required fields: candidates or email_type")
                return Responses.error(400, message="Missing required fields: candidates or email_type")
            
            logging.info("Sending bulk emails - calling email sending service")
            # print("CandidateData::::::MailUtils",candidate_data)
            emails_info = await email_sending_service(candidates=candidates, email_type=email_type, input_data=input_data, id=id).frame_email_bodies()
            # print("emails_info::::::",emails_info)
            for email_info in emails_info:
                try:
                    logging.info("Sending email to %s", email_info["email"])
                    service = await mail_helper.get_gmail_service(access_token)
                    if email_type in ["task_link", "rejection_letter","meet_link_email","custom_email"]:
                        email_message = await mail_helper.create_email("me", email_info["email"], email_info["subject"], email_info["body"])
                    else:
                        attachment_file = candidate_data.get("attachment_file", None)
                        attachment_name = candidate_data.get("attachment_name", "attachment")
                        # temp function to create folder and send off emails and send path to this function
                        if not attachment_file:
                            logging.error("Attachment file is required for this email type")
                            return Responses.error(400, message="Attachment file is required for this email type")
                        attachment_path = None
                        email_message = await mail_helper.create_email_with_attachment("me", email_info["email"], email_info["subject"], email_info["body"], attachment_path, attachment_name)
                        
                    message_sent = service.users().messages().send(userId="me", body=email_message).execute()
                    plain_text_body = await mail_helper.extract_text_from_html(email_info["body"])
                    message_sent = [{"message_id": message_sent["id"], "subject": email_info["subject"], "content": plain_text_body, "status": True, "sent_by": "me"}]
                    check_conversation = await conversations_db.check_conversation_by_user(user["email"], chat_id, email_type, email_info["email"])

                    if check_conversation:

                        await conversations_db.update_conversation(user["email"], chat_id, email_type, message_sent, email_info["email"])
                        logging.info("Existing conversation updated for %s", email_info["email"])
                    else:
                        conversation_id = await conversations_db.insert_conversation(user["user_id"], chat_id, user["email"], email_info["email"], email_type, message_sent, "Email")
                        logging.info("New conversation created with ID: %s for %s", conversation_id, email_info["email"])
                    
                    logging.info("Conversation saved successfully for %s", email_info["email"])

                except Exception as e:
                    return Responses.error(400, message=f'Error occured while sending the mail to [{email_info["email"]}] : {str(e)}')

        except Exception as e:
            return  Responses.error(500, message=f'Error occured in sending bulk mail function - {str(e)}')
        return Responses.success(200, message="Email sent successfully", data=f'mail sent to {len(emails_info)} candidates')