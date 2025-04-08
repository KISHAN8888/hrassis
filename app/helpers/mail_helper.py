from typing import Optional, List, Dict
import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import httpx
import re
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.utils.http_responses import Responses
from app.config.env_config import env_config


logging.basicConfig(level=logging.INFO)

class MailHelper:
    """Helper class for sending emails."""
    @staticmethod
    async def generate_access_token(refresh_token: str) -> Optional[str]:
        """Generate a new access token using the refresh token."""
        logging.info("generating access token")
        token_url = "https://oauth2.googleapis.com/token"
        data = {"client_id": env_config.oauth.client_id, "client_secret": env_config.oauth.client_secret, "refresh_token": refresh_token, "grant_type": "refresh_token"}
        try: 
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
                response_data = response.json()
                if response.status_code != 200:
                    logging.error("Failed to generate access token: %s", response_data)
                    return Responses.error(400, message=response_data.get("error", "Failed to refresh token"))
                return response_data.get("access_token")
        except Exception as e:
            logging.error("Failed to generate access token: %s", e)
            return Responses.error(500, message=str(e))
        
    @staticmethod
    async def get_gmail_service(access_token: str):
        """Get a Gmail service object using the access token."""
        try:
            creds = Credentials(token = access_token)
            service = build("gmail", "v1", credentials=creds)
            return service
        except Exception as e:
            logging.error("Failed to get Gmail service: %s", e)
            return Responses.error(500, message=str(e))
        
    @staticmethod
    async def create_email(sender: str, to: str, subject: str, body: str):
        """Create an email message."""
        if not to:
            raise ValueError("Recipient email is required")
        message = MIMEText(body, "html")
        message["To"] = to
        message["From"] = sender
        message["Subject"] = subject
        message_bytes = message.as_bytes()
        base64_message = base64.urlsafe_b64encode(message_bytes).decode("utf-8")
        return {"raw": base64_message}
        
    @staticmethod
    async def create_email_with_attachment(sender: str, to: str, subject: str, body: str, attachment_path: str, attachment_name: str):
        """Create an email message with an attachment."""
        if not attachment_path or not attachment_name:
            raise ValueError("Attachment path and name are required")
        try:
            message = MIMEMultipart()
            message["To"] = to
            message["From"] = sender
            message["Subject"] = subject
            message.attach(MIMEText(body, "html"))
            with open(attachment_path, "rb") as attachment:
                file_content = attachment.read()
                attachment_filename = attachment_name or os.path.basename(attachment_path)
                    
                file_ext = os.path.splitext(attachment_path)[1].lower()
                content_type = {'.pdf': 'application/pdf', '.doc': 'application/msword', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', 
                                '.txt': 'text/plain'}.get(file_ext, 'application/octet-stream')
                
                part = MIMEBase(*content_type.split('/', 1))
                part.set_payload(file_content)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment_filename}",
                )
                message.attach(part)
        except FileNotFoundError:
            error_msg = f"Attachment file not found: {attachment_path}"
            logging.error(error_msg)
            return Responses.error(404, message=error_msg)
        except PermissionError:
            error_msg = f"Permission denied when accessing attachment: {attachment_path}"
            logging.error(error_msg)
            return Responses.error(403, message=error_msg)
        except Exception as e:
            logging.error("Failed to create email: %s", e)
            return Responses.error(500, message=str(e))
                
    @staticmethod
    async def extract_text_from_html(html_content):
        """Extract plain text from HTML content by removing all HTML tags"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)
            return clean_text
        except Exception as e:
            logging.error("Error extracting text from HTML: %s", str(e))
            return re.sub(r'<[^>]+>', '', html_content)
        
    @staticmethod
    def extract_email_body(message):
        """
        Extracts the email body from the Gmail API response.
        Handles both plain text and HTML formats.
        """
        payload = message["payload"]

        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

                if part["mimeType"] == "text/html" and "data" in part["body"]:
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

        return "No body found"