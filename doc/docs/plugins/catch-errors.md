# CatchErrorsPlugin

Catches exceptions in plugin hooks to shield the server from crashing.


## Usage

```python
# settings.py
from prometheus_virtual_metrics.plugins import CatchErrorsPlugin

PLUGINS = [
    CatchErrorsPlugin(
        FlakyPlugin(),
    ),
]
```

::: prometheus_virtual_metrics.plugins.CatchErrorsPlugin
    handler: python
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false
