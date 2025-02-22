import datetime
import pytest


@pytest.mark.parametrize('hook', [
    ('request_metric_names', {}),
    ('request_label_names', {}),

    ('request_label_values', {
        'label_name': 'label1',
    }),

    ('request_instant', {
        'query_string': 'metric1',
        'time': datetime.datetime(1970, 1, 1, 0, 0, 0),
    }),

    ('request_range', {
        'query_string': 'metric1',
        'start': datetime.datetime(1970, 1, 1, 0, 0, 0),
        'end': datetime.datetime(1970, 1, 1, 0, 0, 30),
    }),
])
@pytest.mark.parametrize('custom_credentials_method', [True, False])
@pytest.mark.parametrize('raise_exception', [True, False])
def test_basic_auth(
        hook,
        custom_credentials_method,
        raise_exception,
        prometheus_virtual_metrics_context_factory,
):

    from types import SimpleNamespace

    from prometheus_virtual_metrics.plugins import BasicAuthPlugin

    AUTH = ('username', 'password')

    hook_name, hook_kwargs = hook

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

    class CustomBasicAuthPlugin(BasicAuthPlugin):
        def check_credentials(self, username, password):
            if raise_exception:
                raise ValueError()

            return (username, password) == AUTH

    if custom_credentials_method:
        plugins = [
            CustomBasicAuthPlugin(),
            Plugin(),
        ]

    else:
        plugins = [
            BasicAuthPlugin(credentials={
                AUTH[0]: AUTH[1],
            }),
            Plugin(),
        ]

    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            PLUGINS=plugins,
        ),
    )

    function = getattr(context, hook_name)

    # without credentials
    assert function(
        **hook_kwargs,
    ) == {
        'status': 'error',
        'errorType': 'HTTP',
        'error': 'ForbiddenError()',
    }

    # wrong credentials
    assert function(**{
        **hook_kwargs,
        'auth': ('foo', 'bar'),
    }) == {
        'status': 'error',
        'errorType': 'HTTP',
        'error': 'ForbiddenError()',
    }

    # correct credentials but crash in auth method
    if custom_credentials_method and raise_exception:
        assert function(**{
            **hook_kwargs,
            'auth': ('foo', 'bar'),
        }) == {
            'status': 'error',
            'errorType': 'HTTP',
            'error': 'ForbiddenError()',
        }

    # correct credentials
    else:
        assert function(**{
            **hook_kwargs,
            'auth': AUTH,
        })['status'] == 'success'
