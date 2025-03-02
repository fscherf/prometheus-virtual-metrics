import threading

import rlpython


class rlpythonPlugin:
    """
    Args:
        embed_kwargs (kwargs): kwargs for `rlpython.embed()`

    Examples:
        >>> rlpythonPlugin(bind='127.0.0.1:5000')  # binds to a network port

        >>> rlpythonPlugin(bind='file:///app/socket')  # binds to a UNIX domain socket in `/app/socket`
    """

    def __init__(self, **embed_kwargs):
        self.embed_kwargs = embed_kwargs

    def on_startup(self, server):
        def _run_shell_server():
            rlpython.embed(
                locals={
                    'server': server,
                },
                **self.embed_kwargs,
            )

        threading.Thread(
            target=_run_shell_server,
            daemon=True,
        ).start()
