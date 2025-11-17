# Gunicorn Configuration for Production
# /opt/clinidocs/cr_backend/gunicorn_config.py

import multiprocessing

# Server Socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Graceful Restart
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = "clinidocs_gunicorn"

# Server Mechanics
daemon = False
pidfile = "/var/run/gunicorn/gunicorn.pid"
user = "ubuntu"
group = "www-data"
umask = 0o007

# SSL (si no usas Nginx/ALB)
# keyfile = "/etc/ssl/private/clinidocs.key"
# certfile = "/etc/ssl/certs/clinidocs.crt"

# Environment
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.settings.production_aws",
]

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
