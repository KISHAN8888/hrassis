from fastapi import APIRouter
from app.controllers.mail_controllers import MailControllers as mail_controllers

mail_router = APIRouter()

mail_router.post("/send/")(mail_controllers.send_bulk_email_endpoint)
mail_router.get("/watch/")(mail_controllers.watchEmail)
mail_router.post("/gmail/webhook/")(mail_controllers.google_webhook) 