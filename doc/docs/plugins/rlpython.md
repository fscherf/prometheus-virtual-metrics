# rlpythonPlugin

Runs a [rlpython](https://github.com/fscherf/rlpython) server alongside the
prometheus-virtual-metrics-server.


## Usage

```python
# settings.py
from prometheus_virtual_metrics.plugins import rlpythonPlugin

PLUGINS = [
    rlpythonPlugin(bind='127.0.0.1:5000'),
]
```

::: prometheus_virtual_metrics.plugins.rlpythonPlugin
    handler: python
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false
