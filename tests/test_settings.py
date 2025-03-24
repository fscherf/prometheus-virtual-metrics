from types import SimpleNamespace
import os

import pytest


@pytest.mark.parametrize('config', [
    {
        'prefix': '',
        'valid_paths': [
            '/api/v1/query',
        ],
        'invalid_paths': [
            '/prometheus/api/v1/query',
        ],
    },
    {
        'prefix': '/',
        'valid_paths': [
            '/api/v1/query',
        ],
        'invalid_paths': [
            '/prometheus/api/v1/query',
            '/prometheus/foo/bar/baz/api/v1/query',
        ],
    },
    {
        'prefix': '/prometheus',
        'valid_paths': [
            '/prometheus/api/v1/query',
        ],
        'invalid_paths': [
            '/api/v1/query',
            '/prometheus/foo/bar/baz/api/v1/query',
        ],
    },
    {
        'prefix': 'prometheus',
        'valid_paths': [
            '/prometheus/api/v1/query',
        ],
        'invalid_paths': [
            '/api/v1/query',
            '/prometheus/foo/bar/baz/api/v1/query',
        ],
    },
    {
        'prefix': 'prometheus/foo/bar/baz/',
        'valid_paths': [
            '/prometheus/foo/bar/baz/api/v1/query',
        ],
        'invalid_paths': [
            '/api/v1/query',
            '/prometheus/foo/api/v1/query',
        ],
    },
])
def test_api_url_prefix(config, prometheus_virtual_metrics_context_factory):
    import requests

    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            API_URL_PREFIX=config['prefix'],
        ),
    )

    def get_data(path):
        host, port = context.app_runner.addresses[0]
        url = f'http://{host}:{port}{path}'

        return requests.post(url, data={}).json().get('data', None)

    for path in config['valid_paths']:
        assert get_data(path)

    for path in config['invalid_paths']:
        assert not get_data(path)
