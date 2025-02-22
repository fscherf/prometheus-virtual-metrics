from prometheus_virtual_metrics.plugins import ExamplePlugin

LOG_LEVEL = 'info'
SETUP_LOGGING = True
MAX_THREADS = 12
HOST = '127.0.0.1'
PORT = 9090

PLUGINS = [
    ExamplePlugin(),
]
