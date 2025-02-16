import logging

# Gunicorn config variables
loglevel = 'info'
accesslog = '-'       # Send access logs to stdout
errorlog = '-'        # Send error logs to stderr
capture_output = True # Capture worker stdout/stderr
enable_stdio_inheritance = True

# Optionally, configure Python logging here as well
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
