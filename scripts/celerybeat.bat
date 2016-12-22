C:\spotipo\env\Scripts\celery -A celeryworker.celery  --workdir=C:\\spotipo\\ beat -b "sqla+sqlite:///instance\celeryd.db" --loglevel=DEBUG -f logs\\celerybeat.log
