release: python manage.py migrate
web: gunicorn locallibrary.wsgi --log-file -
celerybeat: celery -A wsb_ticker -l INFO