from types import SimpleNamespace
from datetime import datetime


def test_server(prometheus_virtual_metrics_context_factory):
    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(),
    )

    response = context.query_range(
        '{__name__=~"prom.*"}',
        start=datetime(1970, 1, 1, 0, 0, 0),
        end=datetime(1970, 1, 1, 1, 0, 0),
    )

    assert response['status'] == 'success'
