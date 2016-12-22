C:\spotipo\env\Scripts\celery -A celeryworker.celery  --workdir=C:\\spotipo\\ worker -b "sqla+sqlite:///instance\celerydb.db" --loglevel=DEBUG --concurrency=1 -f logs\\celeryd.log
