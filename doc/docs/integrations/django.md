# Django

To integrate prometheus-virtual-metrics in your Django project, install the
prometheus-virtual-metrics app and add a route that points to
`prometheus_virtual_metrics.django_app.views.handle_prometheus_request`.
Afterwards, you can configure prometheus-virtual-metrics from your
Django `settings.py`.

To avoid clashes with Django settings, prometheus-virtual-metrics expects you
to prefix all settings with `PROMETHEUS_VIRTUAL_METRICS_`.

```python
# Django settings.py
from prometheus_virtual_metrics.plugins import BasicAuthPlugin
from my_app.plugins import MyPlugin

INSTALLED_APPS = [
    'prometheus_virtual_metrics.django_app',
]

PROMETHEUS_VIRTUAL_METRICS_PLUGINS = [
    BasicAuthPlugin(
        credentials={
            'admin': 'admin',
        },
    ),
    MyPlugin(),
)
```
```python
# Django urls.py
from prometheus_virtual_metrics.django_app.views import handle_prometheus_request  # NOQA

urlpatterns = [
    re_path(r'api/v1/.*', handle_prometheus_request),
]
```
!!! note

    If the Prometheus HTTP API URLs (`/api/v1/.*`) clash with your application's URLs,
    you can prefix the route with any string.

    **Example:**

    ```python
    re_path(r'prometheus-virtual-metrics/api/v1/.*', handle_prometheus_request),
    ```

!!! warning

    `on_shutdown` plugin hooks are not supported when using Django.
