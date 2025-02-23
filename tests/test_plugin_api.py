from types import SimpleNamespace
from datetime import datetime

import requests
import pytest


def test_unknown_endpoints(prometheus_virtual_metrics_context_factory):
    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(),
    )

    assert requests.get(
        context.get_url('/api/v1/foo'),
    ).json() == {}

    assert requests.post(
        context.get_url('/api/v1/foo/bar'),
    ).json() == {}


@pytest.mark.parametrize('async_api', [True, False])
def test_errors_in_requests(
        async_api,
        prometheus_virtual_metrics_context_factory,
):

    if async_api:
        class Plugin:
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
        class Plugin:
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
            ],
        ),
    )

    # on_metric_names_request
    response = context.request_metric_names()

    assert response['status'] == 'error'
    assert response['errorType'] == 'Python Exception'
    assert response['error'] == "ValueError('on_metric_names_request')"

    # on_instant_query_request
    response = context.request_instant(
        'foo',
        time=datetime(1970, 1, 1, 0, 0, 0),
    )

    assert response['status'] == 'error'
    assert response['errorType'] == 'Python Exception'
    assert response['error'] == "ValueError('on_instant_query_request')"

    # on_range_query_request
    response = context.request_range(
        'foo',
        start=datetime(1970, 1, 1, 0, 0, 0),
        end=datetime(1970, 1, 1, 0, 0, 30),
    )

    assert response['status'] == 'error'
    assert response['errorType'] == 'Python Exception'
    assert response['error'] == "ValueError('on_range_query_request')"


@pytest.mark.parametrize('async_api', [True, False])
def test_metric_names_requests(
        async_api,
        prometheus_virtual_metrics_context_factory,
):

    if async_api:
        class Plugin1:
            async def on_metric_names_request(self, request, response):
                if not request.query.name_matches('metric_1'):
                    return

                response.add_value('metric_1')

        class Plugin2:
            async def on_metric_names_request(self, request, response):
                if not request.query.name_matches('metric_2'):
                    return

                response.add_value('metric_2')

    else:
        class Plugin1:
            def on_metric_names_request(self, request, response):
                if not request.query.name_matches('metric_1'):
                    return

                response.add_value('metric_1')

        class Plugin2:
            def on_metric_names_request(self, request, response):
                if not request.query.name_matches('metric_2'):
                    return

                response.add_value('metric_2')

    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            PLUGINS=[
                Plugin1(),
                Plugin2(),
            ],
        ),
    )

    assert context.request_metric_names(
        query_string='metric_1',
        request_series=False,
    )['data'] == [
        'metric_1',
    ]

    assert context.request_metric_names(
        query_string='{__name__=~"metric_.*"}',
        request_series=False,
    )['data'] == [
        'metric_1',
        'metric_2',
    ]

    assert context.request_metric_names(
        query_string='{__name__=~"metric_.*"}',
        request_series=True,
    )['data'] == [
        {'__name__': 'metric_1'},
        {'__name__': 'metric_2'},
    ]

    assert context.request_metric_names(
        query_string='metric_1',
        request_series=True,
    )['data'] == [
        {'__name__': 'metric_1'},
    ]


@pytest.mark.parametrize('async_api', [True, False])
def test_label_names_requests(
        async_api,
        prometheus_virtual_metrics_context_factory,
):

    if async_api:
        class Plugin1:
            async def on_label_names_request(self, request, response):
                if not request.query.name_matches('metric_1'):
                    return

                response.add_value('label1')

        class Plugin2:
            async def on_label_names_request(self, request, response):
                if not request.query.name_matches('metric_2'):
                    return

                response.add_value('label2')

    else:
        class Plugin1:
            def on_label_names_request(self, request, response):
                if not request.query.name_matches('metric_1'):
                    return

                response.add_value('label1')

        class Plugin2:
            def on_label_names_request(self, request, response):
                if not request.query.name_matches('metric_2'):
                    return

                response.add_value('label2')

    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            PLUGINS=[
                Plugin1(),
                Plugin2(),
            ],
        ),
    )

    assert context.request_label_names(
        query_string='metric_1',
    )['data'] == [
        'label1',
    ]

    assert context.request_label_names(
        query_string='{__name__=~"metric_.*"}',
    )['data'] == [
        'label1',
        'label2',
    ]


@pytest.mark.parametrize('async_api', [True, False])
def test_label_values_requests(
        async_api,
        prometheus_virtual_metrics_context_factory,
):

    if async_api:
        class Plugin1:
            async def on_label_values_request(self, request, response):
                if request.label_name != 'label1':
                    return

                response.add_value('value1')

        class Plugin2:
            async def on_label_values_request(self, request, response):
                if request.label_name != 'label2':
                    return

                response.add_value('value2')

    else:
        class Plugin1:
            def on_label_values_request(self, request, response):
                if request.label_name != 'label1':
                    return

                response.add_value('value1')

        class Plugin2:
            def on_label_values_request(self, request, response):
                if request.label_name != 'label2':
                    return

                response.add_value('value2')

    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            PLUGINS=[
                Plugin1(),
                Plugin2(),
            ],
        ),
    )

    assert context.request_label_values(
        label_name='label1'
    )['data'] == [
        'value1',
    ]

    assert context.request_label_values(
        label_name='label2'
    )['data'] == [
        'value2',
    ]


@pytest.mark.parametrize('async_api', [True, False])
def test_instant_query_requests(
        async_api,
        prometheus_virtual_metrics_context_factory,
):

    if async_api:
        class Plugin1:
            async def on_instant_query_request(self, request, response):
                response.add_sample(
                    metric_name='metric_1',
                    metric_value=1,
                    metric_labels={
                        'foo': 'bar',
                    },
                    timestamp=request.time,
                )

        class Plugin2:
            async def on_instant_query_request(self, request, response):
                response.add_sample(
                    metric_name='metric_2',
                    metric_value=2,
                    metric_labels={
                        'bar': 'baz',
                    },
                    timestamp=request.time,
                )
    else:
        class Plugin1:
            def on_instant_query_request(self, request, response):
                response.add_sample(
                    metric_name='metric_1',
                    metric_value=1,
                    metric_labels={
                        'foo': 'bar',
                    },
                    timestamp=request.time,
                )

        class Plugin2:
            def on_instant_query_request(self, request, response):
                response.add_sample(
                    metric_name='metric_2',
                    metric_value=2,
                    metric_labels={
                        'bar': 'baz',
                    },
                    timestamp=request.time,
                )

    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            PLUGINS=[
                Plugin1(),
                Plugin2(),
            ],
        ),
    )

    # metric_1
    response = context.request_instant(
        'metric_1',
        time=datetime(1970, 1, 1, 0, 0, 30),
    )

    assert response['data']['result'] == [
        {
            'metric': {
                '__name__': 'metric_1',
                'foo': 'bar',
            },
            'values': [
                [30.0, '1'],
            ],
        },
    ]

    # metric_2
    response = context.request_instant(
        'metric_2',
        time=datetime(1970, 1, 1, 0, 1, 0),
    )

    assert response['data']['result'] == [
        {
            'metric': {
                '__name__': 'metric_2',
                'bar': 'baz',
            },
            'values': [
                [60.0, '2'],
            ],
        },
    ]

    # metric_*
    response = context.request_instant(
        '{__name__=~"metric_.*"}',
        time=datetime(1970, 1, 1, 0, 0, 30),
    )

    assert response['data']['result'] == [
        {
            'metric': {
                '__name__': 'metric_1',
                'foo': 'bar',
            },
            'values': [
                [30.0, '1'],
            ]
        },
        {
            'metric': {
                '__name__': 'metric_2',
                'bar': 'baz',
            },
            'values': [
                [30.0, '2'],
            ]
        }
    ]


@pytest.mark.parametrize('async_api', [True, False])
def test_range_query_requests(
        async_api,
        prometheus_virtual_metrics_context_factory,
):

    if async_api:
        class Plugin1:
            async def on_range_query_request(self, request, response):
                for timestamp in request.timestamps:
                    response.add_sample(
                        metric_name='metric_1',
                        metric_value=1,
                        metric_labels={
                            'foo': 'bar',
                        },
                        timestamp=timestamp,
                    )

        class Plugin2:
            async def on_range_query_request(self, request, response):
                for timestamp in request.timestamps:
                    response.add_sample(
                        metric_name='metric_2',
                        metric_value=2,
                        metric_labels={
                            'bar': 'baz',
                        },
                        timestamp=timestamp,
                    )

    else:
        class Plugin1:
            def on_range_query_request(self, request, response):
                for timestamp in request.timestamps:
                    response.add_sample(
                        metric_name='metric_1',
                        metric_value=1,
                        metric_labels={
                            'foo': 'bar',
                        },
                        timestamp=timestamp,
                    )

        class Plugin2:
            def on_range_query_request(self, request, response):
                for timestamp in request.timestamps:
                    response.add_sample(
                        metric_name='metric_2',
                        metric_value=2,
                        metric_labels={
                            'bar': 'baz',
                        },
                        timestamp=timestamp,
                    )

    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            PLUGINS=[
                Plugin1(),
                Plugin2(),
            ],
        ),
    )

    # metric_1, 30s interval
    response = context.request_range(
        'metric_1',
        start=datetime(1970, 1, 1, 0, 0, 0),
        end=datetime(1970, 1, 1, 0, 0, 30),
        step=30,
    )

    assert response['data']['result'] == [
        {
            'metric': {
                '__name__': 'metric_1',
                'foo': 'bar',
            },
            'values': [
                [0.0, '1'],
                [30.0, '1'],
            ],
        },
    ]

    # metric_2, 5s interval
    response = context.request_range(
        'metric_2',
        start=datetime(1970, 1, 1, 0, 0, 0),
        end=datetime(1970, 1, 1, 0, 0, 30),
        step=5,
    )

    assert response['data']['result'] == [
        {
            'metric': {
                '__name__': 'metric_2',
                'bar': 'baz',
            },
            'values': [
                [0.0, '2'],
                [5.0, '2'],
                [10.0, '2'],
                [15.0, '2'],
                [20.0, '2'],
                [25.0, '2'],
                [30.0, '2'],
            ],
        },
    ]

    # metric_*, 30s interval
    response = context.request_range(
        '{__name__=~"metric_.*"}',
        start=datetime(1970, 1, 1, 0, 0, 0),
        end=datetime(1970, 1, 1, 0, 0, 30),
        step=30,
    )

    assert response['data']['result'] == [
        {
            'metric': {
                '__name__': 'metric_1',
                'foo': 'bar',
            },
            'values': [
                [0.0, '1'],
                [30.0, '1'],
            ]
        },
        {
            'metric': {
                '__name__': 'metric_2',
                'bar': 'baz',
            },
            'values': [
                [0.0, '2'],
                [30.0, '2'],
            ]
        }
    ]
