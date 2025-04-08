import logging
import asyncio
from typing import List, Dict, Any
from app.services.prompts.mail_prompts import SEND_EMAIL, CSS_STYLE
from app.repository.user_repository import UserRepository as user_db
from app.helpers.mail_helper import MailHelper as mail_helper
from app.utils.http_responses import Responses
from app.repository.conversations_repository import ConversationsRepository as conversations_db

logging.basicConfig(level=logging.INFO)

class EmailProcessor:
    """
    A class for processing and generating different types of emails for candidates.
    
    This class uses the Command Pattern, where each email type has a dedicated 
    async method that handles the specific formatting and validation requirements.
    """
    def __init__(self, candidates: List[Dict[str, Any]], email_type: str, input_data: Dict[str, Any] = None,  id: str = "JD001"):
        """
        Initialize the EmailProcessor with candidate information and email configuration.
        
        Args:
            candidates: List of candidate dictionaries containing at least Name and Email
            email_type: Type of email to send (task_link, offer_letter, etc.)
            input_data: Data needed for email generation
            id: Job ID for reference
        """
        self.candidates = candidates
        self.email_type = email_type
        self.input_data = input_data or {}
        self.id = id
        self.custom_email_body = input_data.get('custom_email_body') if email_type == "custom_email" else None
        
    def get_subject_by_type(self) -> str:
        """Generate email subject based on email type"""
        
        subject_mapping = {
            "task_link": f"{self.id} Task for {self.input_data.get('job_title')} at {self.input_data.get('company_name')}",
            "task_attachment": f"{self.id} Task for {self.input_data.get('job_title')} at {self.input_data.get('company_name')}",
            "offer_letter": f"{self.id} Offer Letter for {self.input_data.get('job_title')} at {self.input_data.get('company_name')}",
            "rejection_letter": f"{self.id} Application Status Update for {self.input_data.get('job_title')} at {self.input_data.get('company_name')}",
            "meet_link_email": f"{self.id} Interview Invitation for {self.input_data.get('job_title')} at {self.input_data.get('company_name')}",
            "custom_email": f"{self.id} {self.input_data.get('subject')}"
        }
        return subject_mapping.get(self.email_type, f"{self.id} Notification for {self.input_data.get('job_title')}")
    
    async def generate_custom_email(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate custom email content for a candidate.
        Uses a template approach where the user can provide a custom template.
        """
        required_keys = ["subject", "custom_email_body"]
        if not all(key in self.input_data for key in required_keys):
            logging.error("Missing required keys for custom email: %s", required_keys)
            return None 
        subject = self.get_subject_by_type()
        candidate_name = candidate.get('Name')

        formatted_email = self.input_data['custom_email_body'].format(candidate_name=candidate_name)

        email_body = f"""
            {CSS_STYLE}
            <body>
              <div class="email-container">
                {formatted_email}
                <p>
                If you have any queries, please don't hesitate to reply to this email.
                <span style="color: #ff0000;">To ensure proper tracking, please maintain this email thread for all communications.</span>
                </p>
              </div>
            </body>
            """
        return {"email": candidate.get('Email'),"subject": subject,"body": email_body}
    
    async def generate_task_link_email(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate task link email content for a candidate.
        Implements the Strategy Pattern by handling specific validation for this email type.
        """
        logging.info("generating task link email")
        required_keys = ["job_title", "company_name", "department", "task_link", "duration", "deadline", "contact_email"]
        if not all(key in self.input_data for key in required_keys):
            logging.error("Missing required keys for task_link email: %s", required_keys)
            return None
            
        subject = self.get_subject_by_type()
        email_body = SEND_EMAIL["ASSESSMENT_EMAIL_LINK"].format(
            candidate_name=candidate.get('Name'), **self.input_data)
        return {"email": candidate.get('Email'),"subject": subject,"body": email_body}
    
    async def generate_task_attachment_email(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Generate task attachment email content for a candidate"""
        required_keys = ["job_title", "company_name", "department", "duration", "deadline", "contact_email"]
        if not all(key in self.input_data for key in required_keys):
            logging.error("Missing required keys for task_attachment email: %s", required_keys)
            return None
            
        subject = self.get_subject_by_type()
        email_body = SEND_EMAIL["ASSESSMENT_EMAIL_ATTACHMENT"].format(candidate_name=candidate.get('Name'), **self.input_data)
        
        return {"email": candidate.get('Email'),"subject": subject,"body": email_body}
    
    async def generate_offer_letter_email(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        print("candidate::::::RejectionLetter",candidate)
        """Generate offer letter email content for a candidate"""
        required_keys = ["job_title", "company_name", "department", "start_date", "salary_details", 
                         "work_location", "acceptance_deadline", "contact_email"]
        if not all(key in self.input_data for key in required_keys):
            logging.error("Missing required keys for offer_letter email: %s", required_keys)
            return None
            
        subject = self.get_subject_by_type()
        email_body = SEND_EMAIL["OFFER_LETTER_EMAIL"].format(
            candidate_name=candidate.get('Name'), 
            **self.input_data
        )
        
        return {"email": candidate.get('Email'),"subject": subject,"body": email_body}
    
    async def generate_rejection_letter_email(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rejection letter email content for a candidate"""
        required_keys = ["job_title", "company_name", "department", "contact_email"]
        if not all(key in self.input_data for key in required_keys):
            logging.error("Missing required keys for rejection_letter email: %s", required_keys)
            return None
            
        subject = self.get_subject_by_type()
        email_body = SEND_EMAIL["REJECTION_LETTER_EMAIL"].format(candidate_name=candidate.get('Name'), **self.input_data)
        return {"email": candidate.get('Email'),"subject": subject,"body": email_body}
    
    # async def generate_meet_link_email(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Generate meet link email content for a candidate.
    #     Shows polymorphic behavior by handling data from either input_data or candidate dict.
    #     """
    #     slots, duration, candidates, participant_emails
    #     required_keys = ["job_title", "company_name", "department", "contact_email"]
    #     required_meet_keys = ["meet_link", "start_time", "duration"]
        
    #     # Check if required standard keys are present
    #     if not all(key in self.input_data for key in required_keys):
    #         lo.error(f"Missing required keys for meet_link email: {required_keys}")
    #         return None
        
    #     # If meet_link and start_time are in candidate data, use them
    #     if "Meet_Link" in candidate and "Start_Time" in candidate:
    #         self.extra_data["meet_link"] = candidate.get("Meet_Link")
    #         self.extra_data["start_time"] = candidate.get("Start_Time")
            
    #     return self.get_email_content(candidate)
    
    async def frame_email_bodies(self) -> Dict[str, Any]:
        """
        Prepare email payloads for all candidates based on the email type.
        
        This method generates email content concurrently for each candidate by merging 
        candidate data (e.g., name, email) with the provided input_data. It filters out 
        candidates missing a valid email address and returns a dictionary containing 
        the list of payloads.
        
        Returns:
            A dictionary with a single key "payloads" that maps to a list of email payloads.
            Each payload is a dictionary with keys "to", "subject", and "message".
        """
        email_type_method_map = {
            "custom_email": self.generate_custom_email,
            "task_link": self.generate_task_link_email,
            "task_attachment": self.generate_task_attachment_email,
            "offer_letter": self.generate_offer_letter_email,
            "rejection_letter": self.generate_rejection_letter_email,
            # "meet_link_email": self.generate_meet_link_email
        }
        if self.email_type not in email_type_method_map:
            return {"payloads": []}

        method = email_type_method_map[self.email_type]
        valid_candidates = [candidate for candidate in self.candidates if candidate.get("Email")]

        content_tasks = [method(candidate) for candidate in valid_candidates]
        email_contents = await asyncio.gather(*content_tasks, return_exceptions=True)
        return email_contents
    
    @staticmethod
    async def process_emails(user_email: str):
        try:
            user = await user_db.get_user_by_email(user_email)

            if  not user:
                logging.error("User not found")
                return Responses.error(404, message="User not found")
            
            access_token: str = await mail_helper.generate_access_token(user["oauth_refresh_token"])

            if not access_token:
                logging.error("Failed to generate access token")
                return Responses.error(400, message="Failed to generate access token")
            
            service = await mail_helper.get_gmail_service(access_token)

            results = service.users().messages().list(userId="me", maxResults=1).execute()
            if not results.get("messages"):
                return {"message": "No new messages found"}
            
            message_id = results["messages"][0]["id"]

            message = await conversations_db.find_message_by_id(message_id)

            if message:
                return None

            message = service.users().messages().get(userId="me", id=message_id).execute()
            body = mail_helper.extract_email_body(message=message)

            headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
            sender = headers.get("From")
            recipient = headers.get("To")
            subject = headers.get("Subject")

            sender_email = sender.split("<")[-1].replace(">", "").strip()
            recipient_email = recipient.split("<")[-1].replace(">", "").strip()

            hr_email = user_email  
            candidate_email = sender_email 

            inserted_msg = None

            if sender_email != hr_email:
                inserted_msg = await conversations_db.insert_recieved_message(hr_email, candidate_email, subject, body, message_id)
            
            if not inserted_msg:
                logging.error("Message not inserted")
                return Responses.error(400, message="Message not inserted")
            
            logging.info("Message inserted successfully: %s", inserted_msg["message_id"])
            # TODO : Send message to the candidate check the flow once and add ai logic..
            
        except Exception as e:
            logging.error(f"Error processing emails: {str(e)}")
            return Responses.error(500, message=str(e))


# import ast 
# import logging
# from src.emailCoordination.receive_agent.prompt import SENTIMENT_ANALYSIS_SYSTEM_PROMPT, SENTIMENT_ANALYSIS_USER_PROMPT, TASK_ATTACHMENT_SYSTEM_PROMPT, TASK_ATTACHMENT_USER_PROMPT, REPLY_EMAIL_SYSTEM_PROMPT, REPLY_EMAIL_USER_PROMPT
# from src.emailCoordination.receive_agent.schemas import SentimentReceiveResponse, TaskAttachmentReceiveResponse, ReplyEmailResponse
# from typing import Dict
# from src.helper import openai_model_response
# from src.helper import get_openai_client

# logging.basicConfig(level=logging.INFO)
    
# class EmailAnalysis:
#     def __init__(self, email_type: str, email_content: str, client, extra_information: str = None):
#         self.email_type = email_type
#         self.email_content = email_content
#         self.extra_information = extra_information
#         self.client = client

#     @classmethod
#     async def create(cls, email_type: str, email_content: str):
#         client = await get_openai_client()
#         return cls(email_type, email_content, client)

#     async def mail_analysis(self) -> Dict:
#         try:
#             logging.debug("Sending request to LLM model")
#             sentiment_email = ["task_link","task_attachment","offer_letter","rejection_letter"]
#             if self.email_type in sentiment_email:
#                formatted_prompt = SENTIMENT_ANALYSIS_USER_PROMPT.format(email_content=self.email_content, extra_information=self.extra_information)
#                response, token_usage, cost = await openai_model_response(self.client, SENTIMENT_ANALYSIS_SYSTEM_PROMPT, formatted_prompt, SentimentReceiveResponse, "o3-mini")
#             else:
#                 formatted_prompt = REPLY_EMAIL_USER_PROMPT.format(email_content=self.email_content, extra_information=self.extra_information)
#                 response, token_usage, cost = await openai_model_response(self.client, REPLY_EMAIL_SYSTEM_PROMPT, formatted_prompt, ReplyEmailResponse, "o3-mini")
               
#             return response, token_usage, cost
#         except Exception as e:
#             logging.error(f"Error generating job description: {str(e)}")
#             return {"job_description": "Error generating job description"}
        
#     async def task_attachment_analysis(self) -> Dict:
#         try:
#             formatted_prompt = TASK_ATTACHMENT_USER_PROMPT.format(email_content=self.email_content, extra_information=self.extra_information)
#             response, token_usage, cost = await openai_model_response(self.client, TASK_ATTACHMENT_SYSTEM_PROMPT, formatted_prompt, TaskAttachmentReceiveResponse, "o3-mini")
#             return response, token_usage, cost
#         except Exception as e:
#             logging.error(f"Error generating task attachment analysis: {str(e)}")
#             return {"task_attachment_analysis": "Error generating task attachment analysis"}

