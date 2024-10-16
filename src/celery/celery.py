from celery import current_app as current_celery_app
from celery.result import AsyncResult
from src.celery.config import settings


def create_celery():
    """
    Create and configure the Celery app instance.

    This function sets up the Celery application by loading its configuration from
    the settings object and applying additional configurations such as enabling task tracking,
    making task results persistent, and configuring worker behavior.

    :return: The configured Celery application instance.
    :rtype: Celery
    """
    celery_app = current_celery_app
    celery_app.config_from_object(settings, namespace="CELERY")
    celery_app.conf.update(task_track_started=True)
    celery_app.conf.update(result_persistent=True)
    celery_app.conf.update(worker_send_task_events=False)
    celery_app.conf.update(worker_prefetch_multiplier=1)

    return celery_app


def get_task_info(task_id):
    """
    Retrieve information about a Celery task given its task ID.

    This function fetches the task status and result for the specified task ID
    using Celery's AsyncResult.

    :param task_id: The unique identifier for the task.
    :type task_id: str

    :return: A dictionary containing the task ID, status, and result.
    :rtype: dict
    """
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result,
    }
    return result


# Create the Celery app and autodiscover tasks
celery = create_celery()
celery.autodiscover_tasks(["src.celery.tasks"], force=True)
