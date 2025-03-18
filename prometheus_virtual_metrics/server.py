from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging

from multidict import CIMultiDict
from aiohttp import web

from prometheus_virtual_metrics.context import PrometheusVirtualMetricsContext
from prometheus_virtual_metrics.request import PrometheusRequest
from prometheus_virtual_metrics import default_settings

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

        self.context = PrometheusVirtualMetricsContext(
            settings=settings,
            run_coroutine_sync=self.run_coroutine_sync,
            logger=self.logger,
        )

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
            lambda: self.context.run_plugin_hook(
                hook_name='on_startup',
                hook_kwargs={
                    'context': self.context,
                },
            ),
        )

    async def on_shutdown(self, app):
        try:
            await self.loop.run_in_executor(
                self.executor,
                lambda: self.context.run_plugin_hook(
                    hook_name='on_shutdown',
                    hook_kwargs={
                        'context': self.context,
                    },
                )
            )

        finally:
            self.executor.shutdown()

    async def handle_http_request(self, http_request):
        post_data = await http_request.post()

        def _get_aiohttp_response():

            # unknown endpoint; return empty response
            if not self.context.valid_prometheus_request_path(
                http_request.path,
            ):

                return web.json_response({})

            prometheus_request = PrometheusRequest(
                context=self.context,
                http_remote=http_request.remote,
                http_headers=CIMultiDict(http_request.headers),
                http_query=CIMultiDict(http_request.query),
                http_post_data=CIMultiDict(post_data),
                http_path=http_request.path,
            )

            prometheus_response = self.context.handle_prometheus_request(
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
