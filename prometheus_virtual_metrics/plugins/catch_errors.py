import functools
import asyncio
import logging

from prometheus_virtual_metrics.constants import PLUGIN_HOOK_NAMES

logger = logging.getLogger('prometheus-virtual-metrics')


class CatchErrorsPlugin:
    """
    Args:
        plugin (Plugin): prometheus-virtual-metrics plugin object (not class).
        plugin_hook_names (list[str] | None): List of hooks that should be shielded. If not set, all hooks are shielded.
        send_warnings (bool): If set to `True` warnings are added to prometheus responses.
        logger (logger): logger
    """

    def __init__(
            self,
            plugin,
            plugin_hook_names=None,
            send_warnings=True,
            logger=logger,
    ):

        self._ce_plugin = plugin
        self._ce_plugin_hook_names = plugin_hook_names or PLUGIN_HOOK_NAMES
        self._ce_send_warnings = send_warnings
        self._ce_logger = logger

    def __getattr__(self, name):
        if (
                name.startswith('_ce_') or
                name not in self._ce_plugin_hook_names or
                not hasattr(self._ce_plugin, name)
        ):

            return super().__getattribute__(name)

        hook = getattr(self._ce_plugin, name)

        def handle_exception(exception, hook_args, hook_kwargs):
            self._ce_logger.exception(
                'exception raised while running %s',
                hook,
            )

            if not self._ce_send_warnings or 'request' not in name:
                return

            response = hook_kwargs.get('response')

            response.add_warning(
                 f'PythonException: {repr(exception)} raised while running {hook.__self__.__class__.__module__}.{hook.__self__.__class__.__name__}.{hook.__name__}()',  # NOQA
            )

        @functools.wraps(hook)
        def sync_wrapper(*args, **kwargs):
            try:
                return hook(*args, **kwargs)

            except Exception as exception:
                handle_exception(
                    exception=exception,
                    hook_args=args,
                    hook_kwargs=kwargs,
                )

        @functools.wraps(hook)
        async def async_wrapper(*args, **kwargs):
            try:
                return await hook(*args, **kwargs)

            except Exception as exception:
                handle_exception(
                    exception=exception,
                    hook_args=args,
                    hook_kwargs=kwargs,
                )

        if asyncio.iscoroutinefunction(hook):
            return async_wrapper

        return sync_wrapper

    def __repr__(self):
        return f'<CatchErrors({repr(self._ce_plugin)})>'
