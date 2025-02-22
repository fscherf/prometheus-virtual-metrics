from importlib import import_module
from argparse import ArgumentParser
import socket
import sys
import os

import simple_logging_setup
from aiohttp import web

from prometheus_virtual_metrics.server import PrometheusVirtualMetricsServer
from prometheus_virtual_metrics import default_settings


if __name__ == '__main__':
    parser = ArgumentParser(
        prog='prometheus_virtual_metrics',
    )

    parser.add_argument(
        '-s',
        '--settings',
        default=os.environ.get(
            'PROMETHEUS_VIRTUAL_METRICS_SETTINGS',
            'prometheus_virtual_metrics.default_settings',
        ),
    )

    # parse argv
    args = parser.parse_args()

    # load settings
    settings = import_module(args.settings)

    # setup logging
    setup_logging = getattr(
        settings,
        'SETUP_LOGGING',
        default_settings.SETUP_LOGGING,
    )

    if setup_logging:
        simple_logging_setup.setup(
            level=getattr(
                settings,
                'LOG_LEVEL',
                default_settings.LOG_LEVEL,
            ),
            preset='service',
        )

    # setup server
    aiohttp_app = web.Application()

    PrometheusVirtualMetricsServer(
        aiohttp_app=aiohttp_app,
        settings=settings,
    )

    # run server
    try:
        web.run_app(
            app=aiohttp_app,
            host=getattr(
                settings,
                'HOST',
                default_settings.HOST,
            ),
            port=getattr(
                settings,
                'PORT',
                default_settings.PORT,
            ),
            access_log=None,
        )

    except (OSError, socket.gaierror) as exception:
        print(exception)

        sys.exit(1)
