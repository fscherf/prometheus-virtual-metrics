def test_django_middleware():
    import datetime
    import base64

    from django.conf import settings
    from django.test import Client

    client = Client()

    def request_instant(query_string, auth=''):
        headers = {}

        if auth:
            credentials = base64.b64encode(auth.encode()).decode()

            headers['Authorization'] = f'Basic {credentials}'

        return client.post(
            path='/api/v1/query',
            data={
                'query': query_string,
                'time': datetime.datetime(1970, 1, 1, 0, 0, 30).timestamp(),
            },
            headers=headers,
        )

    # request with no auth
    response = request_instant('metric_1')

    assert response.status_code == 401

    assert response.json() == {
        'status': 'error',
        'errorType': 'HTTP',
        'error': 'ForbiddenError()',
    }

    # request with wrong credentials
    response = request_instant('metric_1', auth='foo:bar')

    assert response.status_code == 401

    assert response.json() == {
        'status': 'error',
        'errorType': 'HTTP',
        'error': 'ForbiddenError()',
    }

    # request with correct credentials
    response = request_instant('metric_1', auth='username:password')

    assert response.status_code == 200

    assert response.json() == {
        'data': {
            'resultType': 'vector',
            'result': [
                {
                    'metric': {
                        '__name__': 'metric_1',
                    },
                    'values': [
                        [30.0, '1'],
                    ]
                }
            ],
        },
        'infos': [],
        'status': 'success',
        'warnings': [],
    }

    # request that results in a crash
    response = request_instant('metric_2', auth='username:password')

    assert response.status_code == 200

    assert response.json() == {
        'status': 'error',
        'errorType': 'Python Exception',
        'error': "RuntimeError('This crash is on purpose')",
    }

    # check whether the plugin startup hook ran
    assert settings.PLUGIN_STARTUP_RAN is True
