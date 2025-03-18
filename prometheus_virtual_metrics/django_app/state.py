from types import SimpleNamespace
import logging

from asgiref.sync import async_to_sync
from django.conf import settings

from prometheus_virtual_metrics import (
    PrometheusVirtualMetricsContext,
    default_settings,
)

SETTINGS_PREFIX = 'PROMETHEUS_VIRTUAL_METRICS_'

_state = {
    'context': None,
}

logger = logging.getLogger('prometheus-virtual-metrics.logger')


def _run_coroutine_sync(coroutine):
    async def async_function():
        return await coroutine

    return async_to_sync(async_function)()


def setup_context():
    values = {
        'PLUGINS': default_settings.PLUGINS,
    }

    for key in dir(settings):
        if not key.startswith(SETTINGS_PREFIX):
            continue

        values[key[len(SETTINGS_PREFIX):]] = getattr(settings, key)

    _state['context'] = PrometheusVirtualMetricsContext(
        settings=SimpleNamespace(**values),
        run_coroutine_sync=_run_coroutine_sync,
    )

    if _state['context']._plugin_hooks['on_shutdown']:
        logger.warning(
            'on_shutdown hooks are not supported when used with Django',
        )

    return _state['context']


def get_context():
    return _state['context']
