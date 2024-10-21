import os
from functools import lru_cache

from kombu import Queue

from celery.schedules import crontab


def route_task(name, args, kwargs, options, task=None, **kw):
    """
    Route tasks to specific queues based on task name.

    If a task name contains a colon (":") it splits the task name and assigns the task
    to the queue before the colon. Otherwise, it assigns the task to the default 'celery' queue.

    :param name: The name of the task.
    :type name: str
    :param args: Positional arguments for the task.
    :param kwargs: Keyword arguments for the task.
    :param options: Additional task options.
    :param task: The task object (optional).
    :param kw: Additional keyword arguments.

    :return: A dictionary with the queue routing information.
    :rtype: dict
    """
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "celery"}


class BaseConfig:
    """
    Base configuration for Celery.

    This class defines the basic Celery settings such as broker URL, result backend,
    task queues, and task routing strategy. Environment variables are used to override defaults.
    """

    CELERY_BROKER_URL: str = os.environ.get(
        "CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"
    )
    CELERY_RESULT_BACKEND: str = os.environ.get("CELERY_RESULT_BACKEND", "rpc://")

    # Define the default task queue
    CELERY_TASK_QUEUES: list = (Queue("celery"),)

    # Specify how tasks are routed to queues
    CELERY_TASK_ROUTES = (route_task,)

    CELERY_BEAT_SCHEDULE = {
        "cleanup-expired-sessions": {
            "task": "sessions:cleanup_expired_sessions",
            "schedule": crontab(minute=0, hour=0),  # Execute daily at midnight
            "options": {"queue": "celery"},
        },
    }


class DevelopmentConfig(BaseConfig):
    """
    Development-specific configuration for Celery.

    This class inherits from BaseConfig and can override settings
    for a development environment.
    """

    pass


@lru_cache()
def get_settings():
    """
    Load and cache the Celery settings based on the environment.

    The function selects the appropriate configuration class (e.g., DevelopmentConfig)
    based on the environment variable `CELERY_CONFIG`. It uses `lru_cache` to cache
    the result, ensuring that settings are loaded only once.

    :return: The configuration class for the current environment.
    :rtype: BaseConfig
    """
    config_cls_dict = {
        "development": DevelopmentConfig,
    }
    config_name = os.environ.get("CELERY_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()


# Retrieve the Celery settings based on the current environment
settings = get_settings()
