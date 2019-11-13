import multiprocessing

bind = ":8200"

keepalive = 120
max_requests = 1000
timeout = 300
workers = multiprocessing.cpu_count() * 2 + 1
worker_tmp_dir = "/dev/shm"

loglevel = "info"
accesslog = "/logs/gunicorn.access.log"
errorlog = "/logs/gunicorn.error.log"
