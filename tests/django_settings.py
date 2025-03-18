from prometheus_virtual_metrics.plugins import BasicAuthPlugin

# DJANGO
DEBUG = True
SECRET_KEY = 'secret'
USE_TZ = True
TIME_ZONE = 'UTC'
ROOT_URLCONF = __name__
urlpatterns = []


# prometheus-virtual-metrics
PLUGIN_STARTUP_RAN = False


class Plugin:
    async def on_startup(self, context):
        from django.conf import settings

        settings.PLUGIN_STARTUP_RAN = True

    def on_instant_query_request(self, request, response):
        if request.query.name_matches('metric_1'):
            response.add_sample(
                metric_name='metric_1',
                metric_value=1,
                timestamp=request.time,
            )

        elif request.query.name_matches('metric_2'):
            raise RuntimeError('This crash is on purpose')


MIDDLEWARE = [
    'prometheus_virtual_metrics.django_app.middlewares.PrometheusVirtualMetricsMiddleware',  # NOQA
]

INSTALLED_APPS = [
    'prometheus_virtual_metrics.django_app',
]

PROMETHEUS_VIRTUAL_METRICS_PLUGINS = [
    BasicAuthPlugin(
        credentials={
            'username': 'password',
        },
    ),
    Plugin(),
]
