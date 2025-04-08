from fastapi import APIRouter
from app.controllers.jd_controllers import Jd as jd_controllers
jd_router = APIRouter()


jd_router.get("/getjd/{jd_id}/")(jd_controllers.get_jd)
jd_router.get("/getalljd/")(jd_controllers.get_all_jd)
jd_router.put("/updatestatus/")(jd_controllers.update_publish_status)
jd_router.get("/publishjd/{jd_id}/")(jd_controllers.get_jd_by_id)
jd_router.get("/getcandidatestatus/{jd_id}/")(jd_controllers.get_candidate_status_by_jd_id)




