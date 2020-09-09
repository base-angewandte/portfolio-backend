import multiprocessing
import os

bind = ':{}'.format(os.getenv('GUNICORN_PORT', '8200'))

keepalive = 120
max_requests = 1000
max_requests_jitter = 50
timeout = 300
workers = os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1)
worker_tmp_dir = '/dev/shm'

loglevel = 'info'
accesslog = '/logs/gunicorn.access.log'
errorlog = '/logs/gunicorn.error.log'
