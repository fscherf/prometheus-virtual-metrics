import asyncio
import inspect
import logging

from prometheus_virtual_metrics import default_settings

default_logger = logging.getLogger('prometheus-virtual-metrics.plugins')


class PrometheusVirtualMetricsPluginManager:
    HOOK_NAMES = [

        # server hooks
        'on_startup',
        'on_shutdown',

        # prometheus API hooks
        'on_query_request',
        'on_query_range_request',
        'on_metric_names_request',
        'on_label_names_request',
        'on_label_values_request',
    ]

    def __init__(self, server, logger=None):
        self.server = server
        self.logger = logger

        self._plugin_hooks = {}

        if not self.logger:
            self.logger = default_logger

        # discover plugin hooks
        self.logger.debug('discovering plugin hooks')

        plugins = getattr(
            self.server.settings,
            'PLUGINS',
            default_settings.PLUGINS,
        )

        for hook_name in self.HOOK_NAMES:
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

    def pformat_callback(self, callback):

        # method
        if inspect.ismethod(callback):
            return f'{callback.__self__.__class__.__module__}.{callback.__self__.__class__.__name__}.{callback.__name__}()'  # NOQA

        # function
        return f'{callback.__module__}.{callback.__name__}()'

    async def run_hook(self, hook_name, hook_args=None, hook_kwargs=None):
        hook_args = hook_args or tuple()
        hook_kwargs = hook_kwargs or dict()

        self.logger.debug(
            'running plugin hook %s with %s %s',
            hook_name,
            hook_args,
            hook_kwargs,
        )

        if hook_name not in self.HOOK_NAMES:
            raise RuntimeError(f'unknown hook name: {hook_name}')

        for is_async, hook in self._plugin_hooks[hook_name]:
            try:
                if is_async:
                    await hook(*hook_args, **hook_kwargs)

                else:
                    await self.server.loop.run_in_executor(
                        self.server.executor,
                        lambda: hook(*hook_args, **hook_kwargs),
                    )

            except Exception:
                self.logger.exception(
                    'exception raised while running %s',
                    self.pformat_callback(hook),
                )
