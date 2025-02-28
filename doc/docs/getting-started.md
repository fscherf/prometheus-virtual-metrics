# Getting Started

To get started with prometheus-virtual-metrics, you can either use the
[example project](https://github.com/fscherf/prometheus-virtual-metrics/tree/master/example-project)
as a starting point or follow this tutorial.


## Starting The Server

prometheus-virtual-metrics is started by invoking
`python3 -m prometheus_virtual_metrics`. All configuration is done by
specifying a settings module by either setting the environment variable
`PROMETHEUS_VIRTUAL_METRICS_SETTINGS` or the command line flag `-s`.

The settings module needs to be specified as a Python import string (for
example: `my_project.settings`, not `my_project/settings.py`) and has to be
importable. Documentation on all available settings values can be
found [here](settings.md).

prometheus-virtual-metrics can be used with
[watchfiles](https://watchfiles.helpmanual.io/).

Examples:
```bash
# command line flag
python3 -m prometheus_virtual_metrics -s my_project.settings

# environment variable
PROMETHEUS_VIRTUAL_METRICS_SETTINGS=my_project.settings python3 -m prometheus_virtual_metrics

# watchfiles
python3 -m watchfiles \
    "python3 -m prometheus_virtual_metrics -s my_project.settings" \
    /app/my_project/
```


## Connecting Grafana

Once the server runs, you can open Grafana and connect to
prometheus-virtual-metrics like you would connect to a regular Prometheus
server: [Link](https://grafana.com/docs/grafana/latest/datasources/prometheus/configure-prometheus-data-source/#configure-the-data-source)

The prometheus-virtual-metrics default settings configure an example plugin
that exposes a metric called `prometheus_virtual_metrics_example_metric`. To
verify that everything works, you can go to Grafanas explore view and query
`prometheus_virtual_metrics_example_metric`.


# Write A Plugin

Write a [Plugin](plugin-api.md) and put it somewhere your settings module
can import it. Then load the plugin into your settings module and add it to
`PLUGINS`:

```python
# settings.py
from my_project.plugins import MyPlugin

PLUGINS = [
    MyPlugin(),
]
```
