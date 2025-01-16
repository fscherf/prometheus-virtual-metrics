import concurrent
import threading
import asyncio
import logging

from aiohttp.web import Application, AppRunner, TCPSite
import requests
import pytest

from prometheus_virtual_metrics.server import PrometheusVirtualMetricsServer


class BackgroundLoop:
    async def _loop_main(self):
        self._stopped = asyncio.Future()
        self._started.set_result(None)

        # main loop
        await self._stopped

        # shutdown
        # cancel tasks
        canceled_tasks = []
        current_task = asyncio.current_task(loop=self.loop)

        for task in asyncio.all_tasks():
            if task.done() or task is current_task:
                continue

            task.cancel()
            canceled_tasks.append(task)

        for task in canceled_tasks:
            try:
                await task

            except asyncio.CancelledError:
                self.logger.debug(
                    'CancelledError was thrown while shutting down %s',
                    task,
                )

    def _thread_main(self):
        self.loop = asyncio.new_event_loop()

        asyncio.set_event_loop(self.loop)

        try:
            main_task = self.loop.create_task(
                coro=self._loop_main(),
                name='main',
            )

            self.loop.run_until_complete(main_task)

        except asyncio.CancelledError:
            self.logger.debug(
                'CancelledError was thrown while loop was running',
            )

        finally:
            self.loop.stop()
            self.loop.close()

    def start(self):
        self.logger = logging.getLogger('background_loop')
        self.loop = None

        self._started = concurrent.futures.Future()
        self._stopped = None

        # start loop thread
        self.thread = threading.Thread(
            target=self._thread_main,
            daemon=True,
        )

        self.thread.start()

        # wait for loop to start
        self._started.result()

    def stop(self):
        async def _async_stop():
            self._stopped.set_result(None)

        if self._stopped.done():
            raise RuntimeError('loop is already stopped')

        concurrent_future = asyncio.run_coroutine_threadsafe(
            coro=_async_stop(),
            loop=self.loop,
        )

        return concurrent_future.result()


class PrometheusVirtualMetricsContext:
    def __init__(self, loop, settings):
        self.loop = loop
        self.settings = settings

    def start(self, host='127.0.0.1', port=0):
        async def _start():
            aiohttp_app = Application()

            self.server = PrometheusVirtualMetricsServer(
                settings=self.settings,
                aiohttp_app=aiohttp_app,
            )

            self.app_runner = AppRunner(
                app=aiohttp_app,
            )

            await self.app_runner.setup()

            self.site = TCPSite(
                runner=self.app_runner,
                host=host,
                port=port,
                reuse_port=True,
            )

            await self.site.start()

        return asyncio.run_coroutine_threadsafe(
            coro=_start(),
            loop=self.loop,
        ).result()

    def stop(self):
        async def _stop():
            await self.site.stop()
            await self.app_runner.cleanup()

        return asyncio.run_coroutine_threadsafe(
            coro=_stop(),
            loop=self.loop,
        ).result()

    def get_url(self, path):
        host, port = self.app_runner.addresses[0]

        return f'http://{host}:{port}{path}'

    def query_range(self, query_string, start, end):
        return requests.post(
            self.get_url('/api/v1/query_range'),
            data={
                'query': query_string,
                'start': start.timestamp(),
                'end': end.timestamp(),
                'step': 60,
            },
        ).json()


@pytest.fixture
def prometheus_virtual_metrics_context_factory():
    background_loop = BackgroundLoop()
    contexts = []

    background_loop.start()

    def _factory(settings):
        context = PrometheusVirtualMetricsContext(
            loop=background_loop.loop,
            settings=settings,
        )

        context.start()

        contexts.append(context)

        return context

    yield _factory

    # shutdown
    for context in contexts:
        context.stop()

    background_loop.stop()
