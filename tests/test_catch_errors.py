from types import SimpleNamespace
import datetime
import pytest


@pytest.mark.parametrize('async_api', [False, True])
def test_catch_errors(async_api, prometheus_virtual_metrics_context_factory):
    from prometheus_virtual_metrics.plugins import CatchErrorsPlugin

    class Plugin:
        def on_metric_names_request(self, request, response):
            response.add_value('metric1')

        def on_label_names_request(self, request, response):
            response.add_value('label1')

        def on_label_values_request(self, request, response):
            response.add_value('value1')

        def on_instant_query_request(self, request, response):
            response.add_sample(
                request.query.name,
                1,
                timestamp=request.time,
            )

        def on_range_query_request(self, request, response):
            response.add_sample(
                request.query.name,
                1,
                timestamp=next(request.timestamps),
            )

    if async_api:
        class CrashingPlugin:
            async def on_metric_names_request(self, request, response):
                raise ValueError('on_metric_names_request')

            async def on_label_names_request(self, request, response):
                raise ValueError('on_label_names_request')

            async def on_label_values_request(self, request, response):
                raise ValueError('on_label_values_request')

            async def on_instant_query_request(self, request, response):
                raise ValueError('on_instant_query_request')

            async def on_range_query_request(self, request, response):
                raise ValueError('on_range_query_request')

    else:
        class CrashingPlugin:
            def on_metric_names_request(self, request, response):
                raise ValueError('on_metric_names_request')

            def on_label_names_request(self, request, response):
                raise ValueError('on_label_names_request')

            def on_label_values_request(self, request, response):
                raise ValueError('on_label_values_request')

            def on_instant_query_request(self, request, response):
                raise ValueError('on_instant_query_request')

            def on_range_query_request(self, request, response):
                raise ValueError('on_range_query_request')

    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            PLUGINS=[
                Plugin(),
                CatchErrorsPlugin(
                    CrashingPlugin(),
                ),
            ],
        ),
    )

    # metric names
    response = context.request_metric_names()

    assert response['status'] == 'success'
    assert response['data']
    assert len(response['warnings']) == 1
    assert "ValueError('on_metric_names_request')" in response['warnings'][0]

    # label names
    response = context.request_label_names()

    assert response['status'] == 'success'
    assert response['data']
    assert len(response['warnings']) == 1
    assert "ValueError('on_label_names_request')" in response['warnings'][0]

    # label values
    response = context.request_label_values(
        label_name='label1',
    )

    assert response['status'] == 'success'
    assert response['data']
    assert len(response['warnings']) == 1
    assert "ValueError('on_label_values_request')" in response['warnings'][0]

    # instant request
    response = context.request_instant(
        query_string='metric1',
        time=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    assert response['status'] == 'success'
    assert response['data']
    assert len(response['warnings']) == 1
    assert "ValueError('on_instant_query_request')" in response['warnings'][0]

    # range request
    response = context.request_range(
        query_string='metric1',
        start=datetime.datetime(1970, 1, 1, 0, 0, 0),
        end=datetime.datetime(1970, 1, 1, 0, 0, 30),
    )

    assert response['status'] == 'success'
    assert response['data']
    assert len(response['warnings']) == 1
    assert "ValueError('on_range_query_request')" in response['warnings'][0]
