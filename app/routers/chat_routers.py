from fastapi import APIRouter
from app.controllers.chat_controllers import ChatController as chat_controller
chat_router = APIRouter()

chat_router.post("/ask/")(chat_controller.ask)
chat_router.get("/tasks/")(chat_controller.task)
chat_router.get("/chats/")(chat_controller.get_chat_id)
chat_router.get("/get_chats/")(chat_controller.get_all_chats)