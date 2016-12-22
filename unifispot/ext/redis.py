from flask.ext.redis import FlaskRedis

redis = FlaskRedis()


def configure(app):
    #load all celery tasks
    redis.init_app(app)