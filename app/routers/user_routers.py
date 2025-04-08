from fastapi import APIRouter
from app.controllers.user_controllers import UserControllers as user_controllers

user_router = APIRouter()

user_router.post("/signup/")(user_controllers.sign_up)
user_router.post("/signin/")(user_controllers.sign_in)
user_router.get("/google-login/")(user_controllers.google_login)
user_router.post("/send-otp/")(user_controllers.send_otp)
user_router.post("/verify/")(user_controllers.verify_otp)
user_router.patch('/reset_password/')(user_controllers.reset_password)
user_router.get("/getorderbyid/")(user_controllers.get_order_of_user)
# user_router.get("/service/gmail/")(user_controllers.enable_gmail_service)
user_router.get("/user-services/")(user_controllers.users_enabled_services)


