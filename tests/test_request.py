import datetime

import pytest

from prometheus_virtual_metrics.request import PrometheusRequest


def test_timestamps_iterator():

    # valid start and ends
    request = PrometheusRequest(
        start=datetime.datetime(1970, 1, 1, 0, 0, 0).timestamp(),
        end=datetime.datetime(1970, 1, 1, 0, 1, 0).timestamp(),
        step=30,
    )

    assert list(request.timestamps) == [
        datetime.datetime(1970, 1, 1, 0, 0),
        datetime.datetime(1970, 1, 1, 0, 0, 30),
        datetime.datetime(1970, 1, 1, 0, 1),
    ]

    request = PrometheusRequest(
        start=datetime.datetime(1970, 1, 1, 0, 0, 0).timestamp(),
        end=datetime.datetime(1970, 1, 1, 0, 1, 0).timestamp(),
        step=15,
    )

    assert list(request.timestamps) == [
        datetime.datetime(1970, 1, 1, 0, 0),
        datetime.datetime(1970, 1, 1, 0, 0, 15),
        datetime.datetime(1970, 1, 1, 0, 0, 30),
        datetime.datetime(1970, 1, 1, 0, 0, 45),
        datetime.datetime(1970, 1, 1, 0, 1),
    ]

    # end before start
    request = PrometheusRequest(
        start=datetime.datetime(1970, 1, 1, 0, 1, 0).timestamp(),
        end=datetime.datetime(1970, 1, 1, 0, 0, 0).timestamp(),
        step=15,
    )

    with pytest.raises(ValueError) as exc_info:
        list(request.timestamps)

    assert str(exc_info.value).startswith('invalid time range: ')
