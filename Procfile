web: gunicorn bek.wsgi:application --bind 0.0.0.0:8000
worker: celery -A bek worker --loglevel=info
