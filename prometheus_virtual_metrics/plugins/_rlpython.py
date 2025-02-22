import threading

import rlpython


class rlpythonPlugin:
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
