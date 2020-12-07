from flask import g, current_app
from celery import Celery

@celery.task()
def runTrain(model_name):
    pass

@celery.task()
def runPredict(model_name):
    pass


def make_celery(app):
    celery = Celery(app.import_name)
    celery.config_from_object('project.celeryconfig')
    celery.conf.update(app.config)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
