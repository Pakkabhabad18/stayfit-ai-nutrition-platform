from app import create_app
from app.celery_utils import celery_init_app

app = create_app()
celery = celery_init_app(app)

# Import tasks so they are registered with Celery
from app import tasks
