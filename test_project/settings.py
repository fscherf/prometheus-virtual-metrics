from prometheus_virtual_metrics.plugins.example_plugin import ExamplePlugin

from plugins.test_plugin import TestPlugin

LOG_LEVEL = 'info'

PLUGINS = [
    ExamplePlugin(),
    TestPlugin(),
]
