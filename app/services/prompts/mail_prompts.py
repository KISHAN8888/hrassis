SEND_EMAIL = {
  "ASSESSMENT_EMAIL_LINK": """
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
    .email-container {{ max-width: 600px; margin: 20px auto; padding: 20px; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
    h1, h2, h3 {{ color: #333; }}
    a {{ color: #007aff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    p {{ margin-bottom: 15px; }}
    .footer {{ font-size: 12px; color: #999; margin-top: 20px; }}
    .cta {{ display: inline-block; padding: 10px 20px; background-color: #007aff; color: #fff; border-radius: 5px; text-decoration: none; }}
    .cta:hover {{ background-color: #005bb5; }}
  </style>
</head>
<body>
  <div class="email-container">
    <h1>Your Next Step at {company_name}</h1>
    <p>Dear  candidate,</p>
    <p>
      Thank you for applying for the <strong>{job_title}</strong> position in our 
      <strong>{department}</strong> department at <strong>{company_name}</strong>. We are excited about the 
      skills and experiences you bring to the table and are eager to learn more about your potential fit for our team.
    </p>
    <p>
      As part of our recruitment process, we invite you to complete an assessment designed to evaluate the key skills required for this role. 
      This will help us better understand your capabilities and ensure a strong match for both you and our team.
    </p>
    <h2>Assessment Details</h2>
    <p><strong>Position:</strong> {job_title}</p>
    <p><strong>Duration:</strong> {duration}</p>
    <p><strong>Deadline:</strong> {deadline}</p>
    <div class="cta">
      <a href="{task_link}" target="_blank">Start Assessment</a>
    </div>
    <p>Please reply to this email once you have completed the assessment.</p>
    <p>
      If you have any questions or encounter issues, please don't hesitate to reply to this email.
      <span style="color: #ff0000;">Please maintain this email thread for all communications.</span>
    </p>
    <p>
      We appreciate your time and effort in completing this step and look forward to reviewing your responses.
    </p>
    <p>Best regards,</p>
    <p>{company_name}</p>
    <div class="footer">
      &copy; {company_name}. All rights reserved.
    </div>
  </div>
</body>
</html>
""",
  
  "ASSESSMENT_EMAIL_ATTACHMENT": """
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
    .email-container {{ max-width: 600px; margin: 20px auto; padding: 20px; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
    h1, h2, h3 {{ color: #333; }}
    a {{ color: #007aff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    p {{ margin-bottom: 15px; }}
    .footer {{ font-size: 12px; color: #999; margin-top: 20px; }}
    .cta {{ display: inline-block; padding: 10px 20px; background-color: #007aff; color: #fff; border-radius: 5px; text-decoration: none; }}
    .cta:hover {{ background-color: #005bb5; }}
  </style>
</head>
<body>
  <div class="email-container">
    <p>Dear {candidate_name},</p>
    <p>
      Thank you for applying for the <strong>{job_title}</strong> position in our <strong>{department}</strong> department at <strong>{company_name}</strong>. We are thrilled to invite you to participate in the next stage of our recruitment process.
    </p>
    <h2>Assessment Details</h2>
    <p>
      Please find attached the assessment document containing detailed instructions and the required materials. This task is designed to help us evaluate your skills and alignment with the responsibilities of the role.
    </p>
    <h3>Instructions for Submission:</h3>
    <ol>
      <li>Review the attached document thoroughly to understand the assessment requirements.</li>
      <li>Complete the task within the allotted time of <strong>{duration}</strong>.</li>
      <li>Prepare your submission as per the guidelines outlined in the attached document.</li>
      <li>Reply to this email with your completed assessment by the deadline: <strong>{deadline}</strong>.</li>
      <li>Ensure your submission highlights your relevant skills and approach to solving the task.</li>
    </ol>
    <h3>Additional Notes:</h3>
    <ul>
      <li>Please ensure that your work is original and demonstrates your expertise.</li>
      <li>Plagiarism of any kind will result in disqualification from the recruitment process.</li>
      <li><span style="color: #ff0000;">Please maintain this email thread for all communications to ensure efficient tracking of your application.</span></li>
    </ul>
    <h2>Next Steps</h2>
    <p>
      Once your submission is received, our team will review it and provide feedback. You will be notified of the next steps in the hiring process shortly thereafter.
    </p>
    <p>
      We appreciate the time and effort you are putting into this process and wish you the best of luck with the assessment.
    </p>
    <p>Best regards,</p>
    <p>Team HR<br>{company_name}</p>
    <div class="footer">
      &copy; {company_name}. All rights reserved.
    </div>
  </div>
  <p>Please acknowledge this email once you have received the task.</p>
</body>
</html>
""",
  
  "OFFER_LETTER_EMAIL": """
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
    .email-container {{ max-width: 600px; margin: 20px auto; padding: 20px; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
    h1, h2, h3 {{ color: #333; }}
    a {{ color: #007aff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    p {{ margin-bottom: 15px; }}
    .footer {{ font-size: 12px; color: #999; margin-top: 20px; }}
    .cta {{ display: inline-block; padding: 10px 20px; background-color: #007aff; color: #fff; border-radius: 5px; text-decoration: none; }}
    .cta:hover {{ background-color: #005bb5; }}
  </style>
</head>
<body>
  <div class="email-container">
    <p>Dear {candidate_name},</p>
    <p>
      Congratulations! We are delighted to offer you the position of 
      <strong>{job_title}</strong> in our <strong>{department}</strong> at 
      <strong>{company_name}</strong>.
    </p>
    <h2>Offer Details</h2>
    <ul>
      <li><strong>Position:</strong> {job_title}</li>
      <li><strong>Department:</strong> {department}</li>
      <li><strong>Start Date:</strong> {start_date}</li>
      <li><strong>Location:</strong> {work_location}</li>
      <li><strong>Salary:</strong> {salary_details}</li>
    </ul>
    <p>
      Attached to this email, you will find the detailed offer letter outlining the terms and conditions of your employment. Please review the document thoroughly and let us know if you have any questions or require any clarifications.
    </p>
    <h2>Next Steps</h2>
    <p>
      To confirm your acceptance of this offer, please reply to this email with your confirmation or sign and return the attached offer letter by <strong>{acceptance_deadline}</strong>. 
      Once we receive your confirmation, we will share further details regarding your onboarding process.
    </p>
    <p>
      We are excited to have you join our team and look forward to the contributions you will bring to <strong>{company_name}</strong>.
    </p>
    <p>
      If you have any queries, please don't hesitate to reply to this email.
      <span style="color: #ff0000;">To ensure proper tracking, please maintain this email thread for all communications.</span>
    </p>
    <p>Best regards,</p>
    <p>Team HR<br>{company_name}</p>
    <div class="footer">
      &copy; {company_name}. All rights reserved.
    </div>
  </div>
</body>
</html>
""",
  
  "REJECTION_LETTER_EMAIL": """
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
    .email-container {{ max-width: 600px; margin: 20px auto; padding: 20px; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
    h1, h2, h3 {{ color: #333; }}
    a {{ color: #007aff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    p {{ margin-bottom: 15px; }}
    .footer {{ font-size: 12px; color: #999; margin-top: 20px; }}
    .cta {{ display: inline-block; padding: 10px 20px; background-color: #007aff; color: #fff; border-radius: 5px; text-decoration: none; }}
    .cta:hover {{ background-color: #005bb5; }}
  </style>
</head>
<body>
  <div class="email-container">
    <p>Hi {candidate_name},</p>
    <p>
      Thank you for applying for the <strong>{job_title}</strong> role in our <strong>{department}</strong> at <strong>{company_name}</strong>. 
      We really enjoyed reviewing your application and learning more about you!
    </p>
    <p>
      After careful consideration, we’ve decided to proceed with other candidates for this position. 
      Please know this doesn’t reflect on your skills or potential—we truly appreciate the effort you put into applying.
    </p>
    <p>
      We encourage you to keep an eye on future opportunities at <strong>{company_name}</strong>. 
      We’d love to see you back in the candidate pool someday!
    </p>
    <p>
      If you have any questions or would like to connect in the future, please feel free to reply to this email. 
      We're here for you!
      <span style="color: #ff0000;">Please maintain this email thread for any follow-up communications.</span>
    </p>
    <p>Wishing you all the best,</p>
    <p>The Team at <strong>{company_name}</strong></p>
    <div class="footer">
      &copy; {company_name}. All rights reserved.
    </div>
  </div>
</body>
</html>
""",
  
  "MEET_LINK_EMAIL": """
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
    .email-container {{ max-width: 600px; margin: 20px auto; padding: 20px; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }}
    h1, h2, h3 {{ color: #333; }}
    a {{ color: #007aff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    p {{ margin-bottom: 15px; }}
    .footer {{ font-size: 12px; color: #999; margin-top: 20px; }}
    .cta {{ display: inline-block; padding: 10px 20px; background-color: #007aff; color: #fff; border-radius: 5px; text-decoration: none; }}
    .cta:hover {{ background-color: #005bb5; }}
  </style>
</head>
<body>
  <div class="email-container">
    <p>Dear {candidate_name},</p>
    <p>We are pleased to inform you that your interview for the position of <strong>{job_title}</strong> at <strong>{company_name}</strong> has been scheduled.</p>
    <p><strong>Interview Details:</strong></p>
    <ul>
      <li><strong>Date & Time:</strong> {start_time} UTC</li>
      <li><strong>Duration:</strong> {duration} minutes</li>
      <li><strong>Location:</strong> Online via Google Meet</li>
    </ul>
    <p>Please join the meeting using the following link:</p>
    <p><a href="{meet_link}">Join Google Meet</a></p>
    <p>If you have any questions, please reply to this email.</p>
    <p><span style="color: #ff0000;">Please maintain this email thread for all interview-related communications.</span></p>
    <p>Best regards,<br/>HR Team at {company_name}</p>
    <div class="footer">
      &copy; {company_name}. All rights reserved.
    </div>
  </div>
</body>
</html>
"""
}

CSS_STYLE = """
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
      .email-container { max-width: 600px; margin: 20px auto; padding: 20px; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }
      p { margin-bottom: 15px; }
      .footer { font-size: 12px; color: #999; margin-top: 20px; }
    </style>
"""

SENTIMENT_ANALYSIS_SYSTEM_PROMPT = """
You are an advanced AI email sentiment analyzer specialized in interpreting email communications in a professional recruitment context. Your objective is to read through the conversation between the candidate and the HR (including any optional contextual information about the HR or the company) and then determine the sentiment of the candidate’s most recent email.

Upon classifying the candidate’s email sentiment, you must generate four key outputs:

1. sentiment: Must be one of the following values: "Approved", "Disapproved", or "Pending".
2. reason: A short explanation if the sentiment is "Disapproved" or "Pending". If "Approved", the reason is simply a dash (-).
3. ai_reply: A suggested, professionally written reply to the candidate’s email, addressing any relevant points or concerns.
4. ai_reply_summary: A concise 2–3 line summary of the proposed reply.

ENVIRONMENT & LIMITATIONS
--------------------------
1. Context & Input
   - You will be provided with the past email conversation between HR and the candidate, along with any extra details about the HR or the organization.
   - You must rely solely on the information given in the input; no external data is available or should be used.

2. Classification Rules
   - Approved
     * Indicates clear acceptance, enthusiasm, or a positive response to move forward.
     * Denote the reason field with a dash (-).

   - Disapproved
     * Indicates rejection, disagreement, or unwillingness to proceed.
     * The reason should be a short line explaining why the sentiment is disapproved.

   - Pending
     * Suggests uncertainty, requires more information, or requests an extension.
     * The reason should be a short line that explains the ambiguity or additional requirement.

3. Guidelines
   - If the email suggests complete disagreement or refusal to proceed, classify as "Disapproved".
   - If the email suggests clear agreement or willingness to proceed, classify as "Approved".
   - If the candidate’s position is unclear or they ask for more details, classify as "Pending".
   - Do not include any unrelated information outside of the email.
"""

SENTIMENT_ANALYSIS_USER_PROMPT = """
<email_conversation>
{email_content}
</email_conversation>

<extra_information>
{extra_information}
</extra_information>
"""

TASK_ATTACHMENT_SYSTEM_PROMPT = """
You are an advanced AI email assistant specialized in extracting relevant information from email conversations. Your objective is to read through the past email conversation between HR and the candidate and extract the following information:

1. task_info: Any relevant text information from the email content focusing explicitly on explaining the given task. If nothing relevant is found, return an empty string.
2. project_links: A list of URLs related to the candidate's projects. If no links are found, return an empty list.

**Guidelines**  
- Do not include any unrelated information from the email.  
- Ensure that all extracted links are valid URLs.  
- Do not invent or modify information; only use what is explicitly available in the email.  
- If no links are present, use an empty array for `project_links`.  
- If no relevant text is present, use an empty string for `text_info`.  
- Maintain the exact JSON format without additional delimiters or sections.
"""

TASK_ATTACHMENT_USER_PROMPT = """
<email_conversation>
{email_content}
</email_conversation>

<extra_information>
{extra_information}
</extra_information>
"""

REPLY_EMAIL_SYSTEM_PROMPT = """
You are an advanced AI email assistant specialized in drafting professional recruitment-related email communications. Your objective is to read the conversation between the candidate and the HR (including any optional contextual information about the HR or the organization) and then produce:

1. summary_of_email: A concise summary of the candidate’s latest email.
2. ai_response: A full, professionally written email response to the candidate’s message.
   - If there is insufficient information to form a meaningful reply, leave this field blank ("").
3. ai_reply_summary: A 2–3 line summary of the proposed email response.
   - If the ai_response is blank due to insufficient information, mention that in the summary (e.g., "Insufficient information to form a response.").

ENVIRONMENT & LIMITATIONS
-------------------------
1. Context & Input
   - You will be provided with the past email conversation between HR and the candidate, along with any optional details about the HR or the company.
   - You must rely solely on the information given in the input; no external data is available or should be used.

2. Guidelines
   - Keep the response professional and aligned with typical HR communication norms.
   - Tailor the response based on any specific details mentioned in the candidate’s email or in the additional info provided.
   - Do not include unrelated information from the conversation.
"""

REPLY_EMAIL_USER_PROMPT = """
<email_conversation>
{email_content}
</email_conversation>

<extra_information>
{extra_information}
</extra_information>
"""