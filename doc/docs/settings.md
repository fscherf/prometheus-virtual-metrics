# Settings

| Name | Default | Description |
| - | - | - |
| LOG_LEVEL | `'info'` | Log level. Possible values: `'debug'`, `'info'`, `'error'`, `'critical'` |
| SETUP_LOGGING | `True` | If set to `False` the system logging will remain untouched |
| MAX_THREADS | `12` | The max amount of worker threads |
| HOST | `'127.0.0.1'` | The host the server will try to bind to |
| PORT | `9090` | The port the server will try to bind to |
| PLUGINS | `[prometheus_virtual_metrics.plugins.ExamplePlugin()]` | List of plugin objects (not classes) that should be loaded |
