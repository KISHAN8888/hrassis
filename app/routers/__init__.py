from fastapi import APIRouter
from app.routers.user_routers import user_router 
from app.routers.mail_routers import mail_router as mail_router
from app.routers.jd_routers import jd_router as jd_router
from app.routers.chat_routers import chat_router as chat_router
from app.routers.candidate_routers import resume_router as resume_router
from app.routers.candidate_routers import resume_router as resume_router
from app.routers.assesments_routers import assesment_router

router = APIRouter()

@router.get("/")  
def root():
  return{"status": True, "message": "Server is up and running"}

router.include_router(user_router, prefix="/auth", tags=["Auth"])
router.include_router(mail_router, prefix="/mail", tags=["Mail"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(jd_router, prefix="/jd", tags=["JD"])
router.include_router(resume_router, prefix="/resume", tags=["Resume"])
router.include_router(assesment_router, prefix="/assessment", tags=["Assessment"])

