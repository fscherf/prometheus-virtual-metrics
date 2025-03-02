from decimal import Decimal
import datetime

import pytest

from prometheus_virtual_metrics.request import PrometheusRequest

from prometheus_virtual_metrics.response import (
    PROMETHEUS_RESPONSE_TYPE,
    PrometheusResponse,
)


@pytest.mark.parametrize('response_type', [
    PROMETHEUS_RESPONSE_TYPE.VECTOR,
    PROMETHEUS_RESPONSE_TYPE.MATRIX,
])
def test_sample_responses(response_type):

    # valid metric name
    response = PrometheusResponse(
        response_type=response_type,
        request=PrometheusRequest(),
    )

    response.add_sample(
        metric_name='foo',
        metric_value=1,
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    # invalid metric name
    response = PrometheusResponse(
        response_type=response_type,
        request=PrometheusRequest(),
    )

    with pytest.raises(TypeError) as exc_info:
        response.add_sample(
            metric_name=True,
            metric_value=1,
            timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
        )

    assert str(exc_info.value).startswith('metric_name ')

    # valid metric values
    for value in (1, 1.0, Decimal('1.0')):
        response = PrometheusResponse(
            response_type=response_type,
            request=PrometheusRequest(),
        )

        response.add_sample(
            metric_name='foo',
            metric_value=value,
            timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
        )

    # invalid metric values
    for value in ('1', True, {}, []):
        response = PrometheusResponse(
            response_type=response_type,
            request=PrometheusRequest(),
        )

        with pytest.raises(TypeError) as exc_info:
            response.add_sample(
                metric_name='foo',
                metric_value=value,
                timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
            )

        assert str(exc_info.value).startswith('metric_value ')

    # valid timestamps
    valid_timestamps = [
        datetime.datetime(1970, 1, 1, 0, 0, 0).timestamp(),
        datetime.datetime(1970, 1, 1, 0, 0, 0),
    ]

    for timestamp in valid_timestamps:
        response = PrometheusResponse(
            response_type=response_type,
            request=PrometheusRequest(),
        )

        response.add_sample(
            metric_name='foo',
            metric_value=1,
            timestamp=timestamp,
        )

    # invalid timestamps
    invalid_timestamps = [
        str(datetime.datetime(1970, 1, 1, 0, 0, 0).timestamp()),
        str(datetime.datetime(1970, 1, 1, 0, 0, 0)),
        '',
        True,
    ]

    with pytest.raises(TypeError) as exc_info:
        for timestamp in invalid_timestamps:
            response.add_sample(
                metric_name='foo',
                metric_value=1,
                timestamp=timestamp,
            )

    assert str(exc_info.value).startswith('timestamp ')

    # valid metric labels
    response = PrometheusResponse(
        response_type=response_type,
        request=PrometheusRequest(),
    )

    response.add_sample(
        metric_name='foo',
        metric_value=1,
        metric_labels={
            'foo': 'bar',
            'bar': 'baz',
        },
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    # invalid metric labels
    invalid_label_values = [
        True,
        {'foo': True},
        {True: 'foo'},
        {1: 'foo'},
        {'foo': 'bar', 'bar': True},
        {'foo': 'bar', True: 'bar'},
        {'foo': 'bar', 1: 'bar'},
    ]

    for invalid_labels in invalid_label_values:
        response = PrometheusResponse(
            response_type=response_type,
            request=PrometheusRequest(),
        )

        with pytest.raises(TypeError) as exc_info:
            response.add_sample(
                metric_name='foo',
                metric_value=1,
                metric_labels=invalid_labels,
                timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
            )

        assert str(exc_info.value).startswith('metric_labels ')

    # check query match
    response = PrometheusResponse(
        response_type=response_type,
        request=PrometheusRequest(
            query_string='{__name__=~"foo|bar"}',
        ),
    )

    assert len(response._samples) == 0

    assert response.add_sample(
        metric_name='foo',
        metric_value=1,
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    assert len(response._samples) == 1

    assert response.add_sample(
        metric_name='bar',
        metric_value=1,
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    assert len(response._samples) == 2

    assert not response.add_sample(
        metric_name='baz',
        metric_value=1,
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    assert len(response._samples) == 2


def test_sample_response_label_mismatch():
    response = PrometheusResponse(
        response_type=PROMETHEUS_RESPONSE_TYPE.MATRIX,
        request=PrometheusRequest(),
    )

    valid_label_values = [
        {'label1': 'foo', 'label2': 'bar'},
        {'label1': 'foobar', 'label2': 'bazbar'},
    ]

    invalid_label_values = [
        {'label1': 'foo'},
        {'label2': 'bar'},
        {'label3': 'baz'},
        {'label1': 'foo', 'label2': 'bar', 'label3': 'baz'},
        {'label2': 'bar', 'label3': 'baz'},
    ]

    # valid labels
    for labels in valid_label_values:
        response.add_sample(
            metric_name='foo',
            metric_value=1,
            metric_labels=labels,
            timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
        )

    # invalid labels
    for labels in invalid_label_values:
        with pytest.raises(ValueError) as exc_info:
            response.add_sample(
                metric_name='foo',
                metric_value=1,
                metric_labels=labels,
                timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
            )

        assert 'label mismatch' in str(exc_info.value)


def test_sample_response_label_duplicates():
    response = PrometheusResponse(
        response_type=PROMETHEUS_RESPONSE_TYPE.VECTOR,
        request=PrometheusRequest(),
    )

    response.add_sample(
        metric_name='foo',
        metric_value=1,
        metric_labels={'foo': 'foo'},
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    response.add_sample(
        metric_name='foo',
        metric_value=1,
        metric_labels={'foo': 'bar'},
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    with pytest.raises(ValueError) as exc_info:
        response.add_sample(
            metric_name='foo',
            metric_value=1,
            metric_labels={'foo': 'bar'},
            timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
        )

    assert 'duplicate labels' in str(exc_info.value)


def test_sample_response_query_checks():
    response = PrometheusResponse(
        response_type=PROMETHEUS_RESPONSE_TYPE.VECTOR,
        request=PrometheusRequest(
            query_string='foo',
        ),
    )

    assert response.result_count == 0

    # matching sample
    sample_added = response.add_sample(
        metric_name='foo',
        metric_value=1,
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    assert sample_added
    assert response.result_count == 1

    # non matching sample
    sample_added = response.add_sample(
        metric_name='bar',
        metric_value=1,
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
    )

    assert not sample_added
    assert response.result_count == 1

    # non matching sample; skipping query checks
    sample_added = response.add_sample(
        metric_name='bar',
        metric_value=1,
        timestamp=datetime.datetime(1970, 1, 1, 0, 0, 0),
        skip_query_checks=True,
    )

    assert sample_added
    assert response.result_count == 2


@pytest.mark.parametrize('response_type', [
    PROMETHEUS_RESPONSE_TYPE.DATA,
    PROMETHEUS_RESPONSE_TYPE.SERIES,
])
def test_data_responses(response_type):
    response = PrometheusResponse(
        response_type=response_type,
        request=PrometheusRequest(),
    )

    response.add_value('foo')
    response.add_value(['bar', 'baz'])

    invalid_values = [
        1,
        ['foo', 1],
        [['foo'], ['foo']],
    ]

    for values in invalid_values:
        with pytest.raises(TypeError) as exc_info:
            response.add_value(values)

        assert str(exc_info.value) == 'value has to be a string or a list of strings'  # NOQA


def test_sample_response_encoding():

    # empty response
    response = PrometheusResponse(
        response_type=PROMETHEUS_RESPONSE_TYPE.MATRIX,
        request=PrometheusRequest(),
    )

    assert response.to_dict() == {
        'status': 'success',
        'data': {
            'resultType': 'matrix',
            'result': [],
        },
        'infos': [],
        'warnings': [],
    }

    # filled response
    response.add_sample(
        metric_name='metric1',
        metric_value=1,
        metric_labels={
            'label1': 'foo',
            'label2': 'bar',
        },
        timestamp=datetime.datetime(1970, 1, 1, 0, 5, 0),
    )

    response.add_sample(
        metric_name='metric1',
        metric_value=2,
        metric_labels={
            'label1': 'foo',
            'label2': 'bar',
        },
        timestamp=datetime.datetime(1970, 1, 1, 0, 10, 0),
    )

    response.add_sample(
        metric_name='metric1',
        metric_value=1,
        metric_labels={
            'label1': 'foobar',
            'label2': 'barbaz',
        },
        timestamp=datetime.datetime(1970, 1, 1, 0, 15, 0),
    )

    response.add_sample(
        metric_name='metric2',
        metric_value=lambda: 2,
        timestamp=datetime.datetime(1970, 1, 1, 0, 20, 0),
    )

    response.add_info('info1')
    response.add_info(['info2', 'info3'])

    response.add_warning('warning1')
    response.add_warning(['warning2', 'warning3'])

    assert response.to_dict() == {
        'status': 'success',
        'data': {
            'resultType': 'matrix',
            'result': [
                {
                    'metric': {
                        '__name__': 'metric1',
                        'label1': 'foo',
                        'label2': 'bar',
                    },
                    'values': [
                        [300.0, '1'],
                        [600.0, '2'],
                    ]
                },
                {
                    'metric': {
                        '__name__': 'metric1',
                        'label1': 'foobar',
                        'label2': 'barbaz',
                    },
                    'values': [
                        [900.0, '1'],
                    ]
                },
                {
                    'metric': {
                        '__name__': 'metric2',
                    },
                    'values': [
                        [1200.0, '2']
                    ]
                },
            ],
        },
        'infos': [
            'info1',
            'info2',
            'info3',
        ],
        'warnings': [
            'warning1',
            'warning2',
            'warning3',
        ],
    }

    # skip type checks
    response = PrometheusResponse(
        response_type=PROMETHEUS_RESPONSE_TYPE.MATRIX,
        request=PrometheusRequest(),
    )

    response.add_sample(
        metric_name=None,
        metric_value=None,
        metric_labels={
            'label1': None,
        },
        timestamp=None,
        skip_type_checks=True,
    )

    response.add_info(None, skip_type_checks=True)
    response.add_warning(None, skip_type_checks=True)

    assert response.to_dict() == {
        'status': 'success',
        'data': {
            'resultType': 'matrix',
            'result': [
                {
                    'metric': {
                        '__name__': None,
                        'label1': None,
                    },
                    'values': [
                        [None, 'None'],
                    ]
                },
            ],
        },
        'infos': [
            None,
        ],
        'warnings': [
            None,
        ],
    }


def test_data_response_encoding():

    # empty response
    response = PrometheusResponse(
        response_type=PROMETHEUS_RESPONSE_TYPE.DATA,
        request=PrometheusRequest(),
    )

    assert response.to_dict() == {
        'status': 'success',
        'data': [],
        'infos': [],
        'warnings': [],
    }

    # filled response
    response.add_value('foo')
    response.add_value(['bar', 'baz'])

    response.add_info('info1')
    response.add_info(['info2', 'info3'])

    response.add_warning('warning1')
    response.add_warning(['warning2', 'warning3'])

    assert response.to_dict() == {
        'status': 'success',
        'data': [
            'foo',
            'bar',
            'baz',
        ],
        'infos': [
            'info1',
            'info2',
            'info3',
        ],
        'warnings': [
            'warning1',
            'warning2',
            'warning3',
        ],
    }

    # skip type checks
    response = PrometheusResponse(
        response_type=PROMETHEUS_RESPONSE_TYPE.DATA,
        request=PrometheusRequest(),
    )

    response.add_value(None, skip_type_checks=True)
    response.add_info(None, skip_type_checks=True)
    response.add_warning(None, skip_type_checks=True)

    assert response.to_dict() == {
        'status': 'success',
        'data': [
            None,
        ],
        'infos': [
            None,
        ],
        'warnings': [
            None,
        ],
    }


def test_series_response_encoding():

    # empty response
    response = PrometheusResponse(
        response_type=PROMETHEUS_RESPONSE_TYPE.SERIES,
        request=PrometheusRequest(),
    )

    assert response.to_dict() == {
        'status': 'success',
        'data': [],
        'infos': [],
        'warnings': [],
    }

    # filled response
    response.add_value('foo')
    response.add_value(['bar', 'baz'])

    response.add_info('info1')
    response.add_info(['info2', 'info3'])

    response.add_warning('warning1')
    response.add_warning(['warning2', 'warning3'])

    assert response.to_dict() == {
        'status': 'success',
        'data': [
            {'__name__': 'foo'},
            {'__name__': 'bar'},
            {'__name__': 'baz'},
        ],
        'infos': [
            'info1',
            'info2',
            'info3',
        ],
        'warnings': [
            'warning1',
            'warning2',
            'warning3',
        ],
    }
