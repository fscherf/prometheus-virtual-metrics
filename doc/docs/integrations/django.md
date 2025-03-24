# Django

To integrate prometheus-virtual-metrics in your Django project, install the
prometheus-virtual-metrics app and middleware. Afterwards, you can configure
prometheus-virtual-metrics from your Django `settings.py`.

To avoid clashes with Django settings, prometheus-virtual-metrics expects you
to prefix all settings with `PROMETHEUS_VIRTUAL_METRICS_`.

!!! note

    If the Prometheus HTTP API URLs clash with your applications URLs, you can
    prefix prometheus-virtual-metrics URLs by setting `API_URL_PREFIX` in
    the settings (`PROMETHEUS_VIRTUAL_METRICS_API_URL_PREFIX` in
    Django settings).

```python
# Django specific
MIDDLEWARE = [
    'prometheus_virtual_metrics.django_app.middlewares.PrometheusVirtualMetricsMiddleware',  # NOQA
]

INSTALLED_APPS = [
    'prometheus_virtual_metrics.django_app',
]

# prometheus-virtual-metrics
from prometheus_virtual_metrics.plugins import BasicAuthPlugin
from my_app.plugins import MyPlugin

PROMETHEUS_VIRTUAL_METRICS_PLUGINS = [
    BasicAuthPlugin(
        credentials={
            'admin': 'admin',
        },
    ),
    MyPlugin(),
)
```
