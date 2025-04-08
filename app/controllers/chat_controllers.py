import logging
from fastapi import Depends,Request
from langchain_core.messages import HumanMessage
from app.repository.user_repository import UserRepository as user_db
from app.repository.chat_repository import ChatRepository as chat_db
from app.repository.task_repository import TaskRepository as task_db
from app.repository.jd_repository import JobDescriptionRepository as jd_db
from app.repository.resume_repository import ResumeRepository as resume_db
from app.services.chatbot.chatbot import build_main_graph 
from app.validators.ask_validator import AskValidator as ask_validator
from app.middlewares.auth_middleware import AuthMiddleware as auth_middleware
from app.utils.http_responses import Responses
from app.repository.assessment_repository import AssessmentRepository as assessment_db
logging.basicConfig(level=logging.INFO)

class ChatController:
    @staticmethod
    async def ask(body: ask_validator, user = Depends(auth_middleware.authenticate_user)):
    # async def ask(body: ask_validator):
        try:
            # user = await user_db.get_user_by_email("aastha.rathi@thewasserstoff.com")
            user = await user_db.get_user_by_email(user.get("email"))
            message = body.message
            chat_id = body.chat_id
            user_id = user["user_id"]
            created_jd_id, parsed_jd_id, resume_parsed, task_id, db_query_result, email_type, email_material, mail_attachment = "", "", False, "", {}, None, None, False
            config = {"configurable": {"thread_id": chat_id}}
            if body.chat_id == "":
                chat_id = await user_db.update_user_chat_id(user_id)
                config = {"configurable": {"thread_id": chat_id}}
            else:
                checkpointer = await chat_db.get_chat_checkpoint(chat_id)
                if checkpointer:
                    # print("xcvgbnm0000000000000000:",checkpointer)
                    created_jd_id = checkpointer["created_jd_id"]
                    parsed_jd_id = checkpointer["parsed_jd_id"]
                    resume_parsed = checkpointer["resume_parsed"]
                    task_id = checkpointer.get("task_id","")
                    db_query_result = checkpointer.get("db_query_result",{})
            logging.info("Invoking main_graph with chat_id: %s", chat_id)
            chatbot = await build_main_graph()
            messages = await chatbot.ainvoke({"user_id": user_id, "chat_id": chat_id, "parsed_jd_id": parsed_jd_id, "created_jd_id": created_jd_id,
                "messages": [HumanMessage(content=message)], "resume_parsed": resume_parsed, "task_id": task_id, "db_query_result": db_query_result,
                "email_type": email_type, "email_material": email_material, "mail_attachment": mail_attachment}, config)
            print("_----")
            print("Messages", messages)
            print("_----")
            message_text = messages["messages"][-1].content
            selected_route = messages["selected_route"]
            resume_parsed = messages["resume_parsed"]
            created_jd_id = messages["created_jd_id"]
            parsed_jd_id = messages["parsed_jd_id"]
            task_id = messages.get("task_id", "")
            db_query_result = messages.get("db_query_result", {})
            email_type = messages.get("email_type", None)
            email_material = messages.get("email_material", None)
            mail_attachment = messages.get("mail_attachment", False)
            logging.info("Chat processing completed. Selected route: %s", selected_route)
            return {
                "chat_id": chat_id,
                "message": message_text,
                "screen": selected_route,
                "verified": resume_parsed,
                "created_jd_id": created_jd_id,
                "parsed_jd_id": parsed_jd_id,
                "task_id": task_id,
                "db_query_result": db_query_result,
                "email_type": email_type,
                "email_material": email_material,
                "mail_attachment": mail_attachment
            }
        except Exception as e:
            logging.error("Error in Ask Route: %s", str(e))
            return Responses.error(500, str(e))
        
    @staticmethod
    async def get_chat_id(chat_id: str,user=Depends(auth_middleware.authenticate_user)):
        user = await user_db.get_user_by_email(user.get("email"))
        if chat_id not in user['chats']:
            return Responses.error(404, message="Chat not found")
        chats = await chat_db.get_chats(chat_id)
        return chats
    
    
    @staticmethod
    async def task(task_id: str, chat_id: str, user = Depends(auth_middleware.authenticate_user)):
    # async def task(task_id: str, chat_id: str):
        logging.info("Getting task: %s", task_id)
        # user = await user_db.get_user_by_email("aastha.rathi@thewasserstoff.com")
        print("user", user)
        user = await user_db.get_user_by_email(user['email'])
        try:
            if chat_id not in user['chats']:
                return Responses.error(404, message="Chat not found")
            task = await task_db.get_task(task_id, chat_id)
            if task['status'] == "SUCCESS":
                if task['task_type'] == "jd_generation":
                    jd = await jd_db.get_jd_by_chat_id(chat_id, user['user_id'])
                    return Responses.success(200, message="Job description fetched successfully", data={"jd": jd, "status": task['status']})
                elif task['task_type'] in ["resume_parsing","rescreening"]:
                    resumes = await resume_db.get_resumes_by_chat_id(chat_id, user['user_id'])

                    return Responses.success(200, message="Resumes fetched successfully", data={"resumes": resumes, "status": task['status']})
                elif task['task_type'] == 'assessment_generation':
                    assessment = await assessment_db.get_assessment_by_chat_id(chat_id, user['user_id'])
                    return Responses.success(200, message="Assessment fetched successfully", data={"assessment": assessment, "status": task['status']})
                else:
                    return Responses.error(404, message="Task not found")
            elif task['status'] == "PENDING":
                if task['task_type'] in ["resume_parsing","rescreening"]:
                    if task['metadata']['parsed_resumes'] == task['metadata']['uploaded_resumes']:
                        await task_db.update_task_status(task_id, "SUCCESS")
                        await chat_db.update_resume_parsed_to_true(chat_id)
                        return Responses.success(200, message="Task in progress", data={"metadata": task['metadata'], "status": "PENDING"})
                    else:
                        return Responses.success(200, message="Task in progress", data={"metadata": task['metadata'], "status": task['status']})
                else:
                    return Responses.success(200, message="Task in progress", data={"status": task['status']})
        except Exception as e:
            logging.error("Error in task: %s", str(e))
            return Responses.error(500, str(e))
        
        
        
    @staticmethod
    async def get_all_chats(user = Depends(auth_middleware.authenticate_user)):
        print("-----------------",user)
        user = await user_db.get_user_by_email(user.get("email"))
        if not user:
            return Responses.error(404, message="User not found")
        user_chat_ids = user.get("chats")
        return Responses.success(200, message="Chats fetched successfully", data={"chats": user_chat_ids})
        