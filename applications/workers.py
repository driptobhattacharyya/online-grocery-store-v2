from celery import Celery, Task

class FlaskTask(Task):
    def __init__(self, app):
        super().__init__()
        self.app = app
    
    def __call__(self, *args, **kwargs):
        with self.app.app_context():
            return self.run(*args, **kwargs)

def celery_init_app(app):
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object("celeryconfig")
    return celery_app