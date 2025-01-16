from concurrent.futures import ThreadPoolExecutor
import logging

from aiohttp import web

from prometheus_virtual_metrics.request import PrometheusRequest
from prometheus_virtual_metrics import default_settings

from prometheus_virtual_metrics.responses import (
    PrometheusVectorResponse,
    PrometheusMatrixResponse,
    PrometheusSeriesResponse,
    PrometheusDataResponse,
)

from prometheus_virtual_metrics.plugin_manager import (
    PrometheusVirtualMetricsPluginManager,
)

default_logger = logging.getLogger('prometheus-virtual-metrics')


class PrometheusVirtualMetricsServer:
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
            r'/api/v1/{path:.*}',
            self.handle_prometheus_request,
        )

        self.aiohttp_app.on_startup.append(self.on_startup)
        self.aiohttp_app.on_shutdown.append(self.on_shutdown)

        # setup plugins
        self.plugin_manager = PrometheusVirtualMetricsPluginManager(
            server=self,
        )

    @property
    def loop(self):
        return self.aiohttp_app.loop

    async def on_startup(self, app):
        await self.plugin_manager.run_hook(
            hook_name='on_startup',
            hook_args=(self, ),
        )

    async def on_shutdown(self, app):
        await self.plugin_manager.run_hook(
            hook_name='on_shutdown',
            hook_args=(self, ),
        )

        self.executor.shutdown()

    async def handle_prometheus_request(self, http_request):
        try:

            # parse endpoint path
            path = [
                i.strip()
                for i in http_request.match_info['path'].split('/')
                if i
            ]

            # unknown endpoint; return empty response
            if path[0] not in ('query', 'query_range', 'series',
                               'labels', 'label'):

                return web.json_response({})

            # parse prometheus request
            prometheus_request = PrometheusRequest(
                server=self,
                http_headers=dict(http_request.headers),
                http_path=http_request.path,
                http_post_data=dict(await http_request.post()),
                http_query=dict(http_request.query),
                path=path,
            )

            # prepare prometheus response
            prometheus_response = None
            hook_name = ''

            # /api/v1/query
            if path[0] == 'query':
                hook_name = 'on_query_request'

                prometheus_response = PrometheusVectorResponse(
                    request=prometheus_request,
                )

            # /api/v1/query_range
            elif path[0] == 'query_range':
                hook_name = 'on_query_range_request'

                prometheus_response = PrometheusMatrixResponse(
                    request=prometheus_request,
                )

            # /api/v1/labels
            elif path[0] == 'labels':
                hook_name = 'on_label_names_request'

                prometheus_response = PrometheusDataResponse(
                    request=prometheus_request,
                )

            # /api/v1/label/foo/values
            # /api/v1/label/__name__/values
            elif path[0] == 'label':
                if path[1] == '__name__':
                    hook_name = 'on_metric_names_request'

                else:
                    hook_name = 'on_label_values_request'

                prometheus_response = PrometheusDataResponse(
                    request=prometheus_request,
                )

            # /api/v1/series
            elif path[0] == 'series':
                hook_name = 'on_metric_names_request'

                prometheus_response = PrometheusSeriesResponse(
                    request=prometheus_request,
                )

            # run plugin hooks
            await self.plugin_manager.run_hook(
                hook_name=hook_name,
                hook_args=(
                    prometheus_request,
                    prometheus_response,
                ),
            )

            # send response
            return prometheus_response.to_http_response()

        except Exception as exception:
            self.logger.exception(
                'exception raised while running processing %s request',
                path[0],
            )

            return web.json_response({
                'status': 'error',
                'errorType': 'Python Exception',
                'error': repr(exception),
            })
