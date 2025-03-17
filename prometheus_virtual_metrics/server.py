from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
import asyncio
import logging

from multidict import CIMultiDict
from aiohttp import web

from prometheus_virtual_metrics.exceptions import ForbiddenError
from prometheus_virtual_metrics import default_settings
from prometheus_virtual_metrics import constants

from prometheus_virtual_metrics.request import (
    valid_prometheus_request_path,
    PrometheusRequest,
)

from prometheus_virtual_metrics.response import (
    PROMETHEUS_RESPONSE_TYPE,
    PrometheusResponse,
)

default_logger = logging.getLogger('prometheus-virtual-metrics')


class PrometheusVirtualMetricsServer:
    """
    Attributes:
        settings (module | namespace): Central server settings
    """

    def __init__(self, settings, aiohttp_app, logger=None):
        self.settings = settings
        self.aiohttp_app = aiohttp_app
        self.logger = logger or default_logger

        # start executor
        self.executor = ThreadPoolExecutor(
            max_workers=getattr(
                settings,
                'MAX_THREADS',
                default_settings.MAX_THREADS,
            ),
            thread_name_prefix='WorkerThread',
        )

        # setup aiohttp app
        self.aiohttp_app['server'] = self

        self.aiohttp_app.router.add_route(
            '*',
            r'/{path:.*}',
            self.handle_http_request,
        )

        self.aiohttp_app.on_startup.append(self.on_startup)
        self.aiohttp_app.on_shutdown.append(self.on_shutdown)

        # setup plugins
        self._plugin_hooks = {}

        self._discover_plugin_hooks()

    def run_coroutine_sync(self, coroutine):
        future = asyncio.run_coroutine_threadsafe(
            coro=coroutine,
            loop=self.loop,
        )

        return future.result()

    async def on_startup(self, app):
        self.loop = asyncio.get_event_loop()

        await self.loop.run_in_executor(
            self.executor,
            lambda: self._run_plugin_hook(
                hook_name='on_startup',
                hook_kwargs={
                    'server': self,
                },
            ),
        )

    async def on_shutdown(self, app):
        try:
            await self.loop.run_in_executor(
                self.executor,
                lambda: self._run_plugin_hook(
                    hook_name='on_shutdown',
                    hook_kwargs={
                        'server': self,
                    },
                )
            )

        finally:
            self.executor.shutdown()

    # plugin management #######################################################
    def _discover_plugin_hooks(self):
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

    def _run_plugin_hook(
            self,
            hook_name,
            hook_args=None,
            hook_kwargs=None,
    ):

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
                    coroutine=hook(*hook_args, **hook_kwargs),
                )

            else:
                hook(*hook_args, **hook_kwargs)

    async def handle_http_request(self, http_request):
        post_data = await http_request.post()

        def _get_aiohttp_response():

            # unknown endpoint; return empty response
            if not valid_prometheus_request_path(http_request.path):
                return web.json_response({})

            prometheus_request = PrometheusRequest(
                server=self,
                http_remote=http_request.remote,
                http_headers=CIMultiDict(http_request.headers),
                http_query=CIMultiDict(http_request.query),
                http_post_data=CIMultiDict(post_data),
                http_path=http_request.path,
            )

            prometheus_response = self.handle_prometheus_request(
                prometheus_request=prometheus_request,
            )

            return web.json_response(
                status=prometheus_response.http_status,
                data=prometheus_response.to_dict(),
            )

        aiohttp_response = await self.loop.run_in_executor(
            self.executor,
            _get_aiohttp_response,
        )

        return aiohttp_response

    # prometheus HTTP API #####################################################
    def handle_prometheus_request(self, prometheus_request):
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
            self._run_plugin_hook(
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
