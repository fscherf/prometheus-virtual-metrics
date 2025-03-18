from django.apps import AppConfig

from .state import setup_context, get_context


class PrometheusVirtualMetricsAppConfig(AppConfig):
    name = 'prometheus_virtual_metrics.django_app'

    def ready(self):
        context = setup_context()

        context.run_plugin_hook(
            hook_name='on_startup',
            hook_kwargs={
                'context': context,
            },
        )
