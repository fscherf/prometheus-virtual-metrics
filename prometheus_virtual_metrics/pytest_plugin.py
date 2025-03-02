import concurrent
import threading
import asyncio
import logging

from aiohttp.web import Application, AppRunner, TCPSite
import requests
import pytest

from prometheus_virtual_metrics.server import PrometheusVirtualMetricsServer

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 0


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
    """
    Attributes:
        loop (asyncio.EventLoop): asyncio event loop
        settings (module | namespace): settings
    """

    def __init__(self, loop, settings):
        self.loop = loop
        self.settings = settings

    def start(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        """
        Starts the test server. Is called implicitly when using
        the pytest fixture.
        """

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
        """
        Stops the running test server. Is called implicitly when using
        the pytest fixture.
        """

        async def _stop():
            await self.site.stop()
            await self.app_runner.cleanup()

        return asyncio.run_coroutine_threadsafe(
            coro=_stop(),
            loop=self.loop,
        ).result()

    def get_url(self, path):
        """
        Returns absolute URL to running test server.

        Args:
            path (str): Path as string

        Returns:
            URL (str): URL as string
        """

        host, port = self.app_runner.addresses[0]

        return f'http://{host}:{port}{path}'

    def request_metric_names(
            self,
            query_string=None,
            start=None,
            end=None,
            request_series=False,
            auth=None,
    ):

        """
        Request metric names.

          - URL: `/api/v1/${label}/__name__/` or `/api/v1/series`
          - Hook: on_metric_names_request

        Args:
            query_string (str | None): PromQl query as string
            start (datetime.datetime | None): start as datetime.datetime
            end (datetime.datetime | None): end as datetime.datetime
            request_series (bool): Use timeseries request
            auth (tuple[str], None): Basic auth username and password

        Returns:
            response (dict): HTTP response as dict
        """

        data = {}

        if query_string is not None:
            data['query'] = query_string

        if start is not None:
            data['start'] = start

        if end is not None:
            data['end'] = end

        if request_series:
            url = self.get_url('/api/v1/series')

        else:
            url = self.get_url('/api/v1/label/__name__/')

        return requests.post(
            url=url,
            data=data,
            auth=auth,
        ).json()

    def request_label_names(
            self,
            query_string=None,
            start=None,
            end=None,
            auth=None,
    ):

        """
        Request label names.

          - URL: `/api/v1/labels`
          - Hook: on_label_names_request

        Args:
            query_string (str | None): PromQl query as string
            start (datetime.datetime | None): start as datetime.datetime
            end (datetime.datetime | None): end as datetime.datetime
            auth (tuple[str], None): Basic auth username and password

        Returns:
            response (dict): HTTP response as dict
        """

        data = {}

        if query_string is not None:
            data['query'] = query_string

        if start is not None:
            data['start'] = start

        if end is not None:
            data['end'] = end

        return requests.post(
            url=self.get_url('/api/v1/labels'),
            data=data,
            auth=auth,
        ).json()

    def request_label_values(
            self,
            label_name,
            query_string=None,
            start=None,
            end=None,
            auth=None,
    ):

        """
        Request label values.

          - URL: `/api/v1/label/${label}/values`
          - Hook: on_label_values_request

        Args:
            label_name (str): Label name
            query_string (str | None): PromQl query as string
            start (datetime.datetime | None): start as datetime.datetime
            end (datetime.datetime | None): end as datetime.datetime
            auth (tuple[str], None): Basic auth username and password

        Returns:
            response (dict): HTTP response as dict
        """

        data = {}

        if query_string is not None:
            data['query'] = query_string

        if start is not None:
            data['start'] = start

        if end is not None:
            data['end'] = end

        return requests.post(
            url=self.get_url(f'/api/v1/label/{label_name}/values'),
            data=data,
            auth=auth,
        ).json()

    def request_instant(
            self,
            query_string,
            time,
            step=15,
            auth=None,
    ):

        """
        Request data at timestamp.

          - URL: `/api/v1/query`
          - Hook: on_instant_query_request

        Args:
            query_string (str | None): PromQl query as string
            time (datetime.datetime): Timstamp
            step (float): Interval between timestamps
            auth (tuple[str], None): Basic auth username and password

        Returns:
            response (dict): HTTP response as dict
        """

        return requests.post(
            self.get_url('/api/v1/query'),
            data={
                'query': query_string,
                'time': time.timestamp(),
                'step': step,
            },
            auth=auth,
        ).json()

    def request_range(
            self,
            query_string,
            start,
            end,
            step=15,
            auth=None,
    ):

        """
        Request data in time range.

          - URL: `/api/v1/query_range`
          - Hook: on_range_query_request

        Args:
            query_string (str | None): PromQl query as string
            start (datetime.datetime | None): start as datetime.datetime
            end (datetime.datetime | None): end as datetime.datetime
            step (float): Interval between timestamps
            auth (tuple[str], None): Basic auth username and password

        Returns:
            response (dict): HTTP response as dict
        """

        return requests.post(
            self.get_url('/api/v1/query_range'),
            data={
                'query': query_string,
                'start': start.timestamp(),
                'end': end.timestamp(),
                'step': step,
            },
            auth=auth,
        ).json()


@pytest.fixture
def prometheus_virtual_metrics_context_factory():
    background_loop = BackgroundLoop()
    contexts = []

    background_loop.start()

    def _factory(settings, host=DEFAULT_HOST, port=DEFAULT_PORT):
        context = PrometheusVirtualMetricsContext(
            loop=background_loop.loop,
            settings=settings,
        )

        context.start(
            host=host,
            port=port,
        )

        contexts.append(context)

        return context

    yield _factory

    # shutdown
    for context in contexts:
        context.stop()

    background_loop.stop()
