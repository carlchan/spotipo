import flask
from celery import Celery
from functools import wraps
import random
import os,sys
from flask import current_app

from celery.signals import worker_process_init
from config.celeryconfig import  BROKER_URL

class FlaskCelery(Celery):

    def __init__(self, *args, **kwargs):

        super(FlaskCelery, self).__init__(*args, **kwargs)
        #self.patch_task()
        self.app = None

        #if 'app' in kwargs:
        #    self.init_app(kwargs['app'])

    def patch_task(self):
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                if flask.has_app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
                else:
                    with self.app.app_context():
                        return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask

    def init_app(self, app):
        self.app = app
        #self.config_from_object(app.config)
        #self.conf.update(app.config)

    ### Code is based on http://stackoverflow.com/questions/17979655/how-to-implement-autoretry-for-celery-tasks
    def task(self, *args_task, **opts_task):
        def real_decorator(func):
            sup = super(FlaskCelery, self).task

            @sup(*args_task, **opts_task)
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    func(*args, **kwargs)
                except opts_task.get('autoretry_on', Exception) as exc:
                    wrapper.retry(exc=exc, args=args, kwargs=kwargs,)
            return wrapper
        return real_decorator    

celery = Celery(__name__,broker=BROKER_URL)

@worker_process_init.connect
def setup_worker_process_flask_db(**kwargs):
    # something that connects flaskdb to your flask app
    # work around as per https://github.com/celery/celery/issues/3438
    # for allowing celery to perform DB operations
    if sys.platform == 'win32':
        from unifispot import create_app 
        app = create_app(mode= 'development')
        app.app_context().push()
def configure(app):
    #load all celery tasks


    task_files = []


    blueprints_path = app.config.get('MODULE_PATH', 'modules')
    path = os.path.join(
        app.config.get('PROJECT_ROOT', '..'),
        blueprints_path
    )  
    corepath = os.path.join(
        app.config.get('PROJECT_ROOT', '..'),
        'core'
    )      
    base_module_name = ".".join([app.name, blueprints_path])
    dir_list = os.listdir(path)
    mods = {}
    object_name     = app.config.get('BLUEPRINTS_OBJECT_NAME', 'module')
    module_name     = app.config.get('BLUEPRINTS_MODULE_NAME', 'main')
    tasks_name      = app.config.get('BLUEPRINTS_TASKS_NAME', 'tasks')
    tasks_file      = tasks_name + '.py'
    module_file     = module_name + '.py'

    #load core tasks
    if os.path.exists(os.path.join(corepath, 'core', 'tasks.py')):
        task_files.append('unifispot.modules.core.tasks')    

    #load tasks from mobules

    for fname in dir_list:
        if not os.path.exists(os.path.join(path, fname, 'DISABLED')) and  \
                os.path.isdir(os.path.join(path, fname)) and \
                os.path.exists(os.path.join(path, fname, module_file)) and \
                os.path.exists(os.path.join(path, fname, tasks_file)):
            task_files.append('unifispot.modules.%s.tasks'%fname)
    app.config['CELERY_IMPORTS']=tuple(task_files)

    #patch celery to execute with app context

    TaskBase = celery.Task
    _celery = celery

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    #celery.init_app(app)
    celery.conf.update(app.config)

