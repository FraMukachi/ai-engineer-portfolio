import os
import multiprocessing

# Bind to the correct port
port = os.environ.get('PORT', '8000')
bind = f'0.0.0.0:{port}'

# Worker configuration
workers = int(os.environ.get('WEB_CONCURRENCY', 1))
threads = int(os.environ.get('WEB_THREADS', 2))

# Timeout settings
timeout = 120
graceful_timeout = 30

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Keepalive
keepalive = 5

# Preload app for better performance
preload_app = True

# Worker class
worker_class = 'sync'

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def on_exit(server):
    pass
