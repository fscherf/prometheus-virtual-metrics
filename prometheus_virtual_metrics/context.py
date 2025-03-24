from time import perf_counter
import asyncio
import logging
import os

from prometheus_virtual_metrics import default_settings, constants
from prometheus_virtual_metrics.exceptions import ForbiddenError

from prometheus_virtual_metrics.response import (
    PROMETHEUS_RESPONSE_TYPE,
    PrometheusResponse,
)

default_logger = logging.getLogger('prometheus-virtual-metrics')


class PrometheusVirtualMetricsContext:
    """
    Attributes:
        settings (module | namespace): Central settings
    """

    def __init__(self, settings, run_coroutine_sync, logger=default_logger):
        self.settings = settings
        self.run_coroutine_sync = run_coroutine_sync
        self.logger = logger

        self._plugin_hooks = {}

        self.discover_plugin_hooks()

    def valid_prometheus_request_path(self, path):
        """
        Returns `True` if the given path is a valid Prometheus request path.

        Args:
            path (str): HTTP request path

        Returns:
            path_is_valid (bool): path_is_valid
        """

        # check prefix
        api_url_prefix = getattr(
            self.settings,
            'API_URL_PREFIX',
            default_settings.API_URL_PREFIX,
        )

        prefix = os.path.join(
            '/',
            api_url_prefix,
            'api/v1/',
        )

        if not (path.startswith(prefix) and len(path) > len(prefix)):
            return False

        # check endpoint
        endpoint = path[len(prefix):].split('/')[0]

        return endpoint in (
            'query',
            'query_range',
            'series',
            'labels',
            'label',
        )

    # plugin management #######################################################
    def discover_plugin_hooks(self):
        """
        Discover plugin hooks in `settings.PLUGINS`.
        """

        self.logger.debug('discovering plugin hooks')

        plugins = getattr(
            self.settings,
            'PLUGINS',
            default_settings.PLUGINS,
        )

        for hook_name in constants.PLUGIN_HOOK_NAMES:
            self.logger.debug("searching for '%s' hooks", hook_name)

            self._plugin_hooks[hook_name] = []

            for plugin in plugins:
                if not hasattr(plugin, hook_name):
                    continue

                hook = getattr(plugin, hook_name)
                is_async = asyncio.iscoroutinefunction(hook)

                self.logger.debug(
                    '%s %s hook in %s found',
                    'async' if is_async else 'sync',
                    hook_name,
                    plugin,
                )

                self._plugin_hooks[hook_name].append(
                    (is_async, hook, )
                )

    def run_plugin_hook(self, hook_name, hook_args=None, hook_kwargs=None):
        """
        Run plugin hook.

        Args:
            hook_name (str): Name of the hook to run
            hook_args (tuple | None): Hook args
            hook_kwargs (tuple | dict): Hook keyword args
        """

        hook_args = hook_args or tuple()
        hook_kwargs = hook_kwargs or dict()

        self.logger.debug(
            'running plugin hook %s with %s %s',
            hook_name,
            hook_args,
            hook_kwargs,
        )

        assert hook_name in constants.PLUGIN_HOOK_NAMES, f'unknown hook name: {hook_name}'  # NOQA

        for is_async, hook in self._plugin_hooks[hook_name]:
            if is_async:
                self.run_coroutine_sync(
                    hook(*hook_args, **hook_kwargs),
                )

            else:
                hook(*hook_args, **hook_kwargs)

    # prometheus HTTP API #####################################################
    def handle_prometheus_request(self, prometheus_request):
        """
        Handle Prometheus request.

        Args:
            prometheus_request (prometheus_request.PrometheusRequest): prometheus request

        Returns:
            prometheus_response (prometheus_request.PrometheusResponse): prometheus_response
        """  # NOQA

        try:
            start_time = perf_counter()
            request_type = ''
            data_point_type = ''

            # prepare prometheus response
            prometheus_response = None
            hook_name = ''

            # /api/v1/query
            if prometheus_request.path[0] == 'query':
                response_type = PROMETHEUS_RESPONSE_TYPE.VECTOR
                request_type = 'instant'
                data_point_type = 'samples'
                hook_name = 'on_instant_query_request'

            # /api/v1/query_range
            elif prometheus_request.path[0] == 'query_range':
                response_type = PROMETHEUS_RESPONSE_TYPE.MATRIX
                request_type = 'range'
                data_point_type = 'samples'
                hook_name = 'on_range_query_request'

            # /api/v1/labels
            elif prometheus_request.path[0] == 'labels':
                response_type = PROMETHEUS_RESPONSE_TYPE.DATA
                request_type = 'label names'
                data_point_type = 'values'
                hook_name = 'on_label_names_request'

            # /api/v1/label/foo/values
            # /api/v1/label/__name__/values
            elif prometheus_request.path[0] == 'label':
                response_type = PROMETHEUS_RESPONSE_TYPE.DATA
                request_type = 'label values'
                data_point_type = 'values'

                if prometheus_request.path[1] == '__name__':
                    hook_name = 'on_metric_names_request'

                else:
                    hook_name = 'on_label_values_request'

            # /api/v1/series
            elif prometheus_request.path[0] == 'series':
                response_type = PROMETHEUS_RESPONSE_TYPE.SERIES
                request_type = 'metrics names'
                data_point_type = 'values'
                hook_name = 'on_metric_names_request'

            prometheus_response = PrometheusResponse(
                response_type=response_type,
                request=prometheus_request,
            )

            # run plugin hooks
            self.run_plugin_hook(
                hook_name=hook_name,
                hook_kwargs={
                    'request': prometheus_request,
                    'response': prometheus_response,
                },
            )

            # log response
            end_time = perf_counter()

            self.logger.info(
                'handled %s request in %s, returning %s %s [query=%s, client=%s]',  # NOQA
                request_type,
                f'{(end_time - start_time) * 1000:.3f}ms',
                prometheus_response.result_count,
                data_point_type,
                repr(prometheus_request.query_string),
                prometheus_request.http_remote,
            )

            # finish
            return prometheus_response

        except ForbiddenError as exception:
            response = PrometheusResponse(
                response_type=PROMETHEUS_RESPONSE_TYPE.ERROR,
                request=prometheus_request,
            )

            response._set_error(
                error_type='HTTP',
                error=repr(exception),
                http_status=401,
            )

            return response

        except Exception as exception:
            self.logger.exception(
                'exception raised while running processing %s request',
                prometheus_request.path[0],
            )

            response = PrometheusResponse(
                response_type=PROMETHEUS_RESPONSE_TYPE.ERROR,
                request=prometheus_request,
            )

            response._set_error(
                error_type='Python Exception',
                error=repr(exception),
            )

            return response
