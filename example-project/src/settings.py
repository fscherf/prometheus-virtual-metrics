from plugins.example_plugin import ExamplePlugin

LOG_LEVEL = 'info'
SETUP_LOGGING = True
MAX_THREADS = 12
HOST = '0.0.0.0'
PORT = 9090

PLUGINS = [
    ExamplePlugin(),
]
