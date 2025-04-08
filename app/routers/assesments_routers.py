from fastapi import APIRouter
from app.controllers.assesments_controllers import AssesmentController as assesments_controllers

assesment_router = APIRouter()

# assesment_router.post("/create/")(assesments_controllers.create_assesment)
assesment_router.get("/user-assessment/")(assesments_controllers.get_user_assessment)
assesment_router.get("/get-assesment-by-id/")(assesments_controllers.get_assesment_by_id)

