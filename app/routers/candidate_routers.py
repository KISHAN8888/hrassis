from fastapi import APIRouter
from app.controllers.resume_controllers import ResumeControllers as resume_controllers

resume_router = APIRouter()

resume_router.post("/update-status/")(resume_controllers.update_candidate_status)
resume_router.post("/upload-resumes/")(resume_controllers.upload_resumes)
resume_router.get('/get_accepted_resumes/')(resume_controllers.get_accepted_resumes)


