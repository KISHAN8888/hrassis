import os,logging
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
logging.basicConfig(level=logging.INFO)
load_dotenv()

# Set your SendGrid API key here
SENDGRID_API_KEY = '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'

def send_email(email,template,subject):
    message = Mail(
      from_email = 'varun.kate@thewasserstoff.com',  # Replace with your verified SendGrid email
      to_emails=email,  # Replace with recipient's email
      subject=subject,
      html_content=template,
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logging.info("Sending Email Via Sendgrid")
        print(f"Email sent! Status code: {response.status_code}")
        return True
    except Exception as e:
      print(f"Error sending email: {e}")
      return False
