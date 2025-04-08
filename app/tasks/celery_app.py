from celery import Celery

celery_app = Celery(
    "app.tasks",
    broker="amqp://guest:guest@localhost:5672//",
    backend="rpc://" # change this to None, and add database walla logic for routing..
    # redis has to be implemented later..
)

celery_app.conf.update(
    task_routes = {"app.tasks.jd_tasks.generate_jd_worker": {"queue": "job_description"},
                   "app.tasks.resume_tasks.parse_resume_worker": {"queue": "resumes"},
                   "app.tasks.resume_tasks.rescreening_worker": {"queue": "resumes"},
                   "app.tasks.assessment_tasks.generate_assessment_worker": {"queue": "assessments"},
                   },
    task_track_started = True
)

from app.tasks import jd_tasks
from app.tasks import resume_tasks
from app.tasks import assessment_tasks