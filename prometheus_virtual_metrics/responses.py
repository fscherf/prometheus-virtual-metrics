from typing import Callable
from threading import RLock
from numbers import Number
import datetime


class PrometheusResponse:
    """
    https://prometheus.io/docs/prometheus/latest/querying/api/
    """

    def to_dict(self):
        raise NotImplementedError()  # pragma: no cover

    def _add_values(self, values, skip_type_checks, values_list, name):
        if not isinstance(values, list):
            values = [values]

        if not skip_type_checks:
            for value in values:
                if not isinstance(value, str):
                    raise TypeError(
                        f'{name} has to be a string or a list of strings',
                    )

        values_list.extend(values)

    def add_info(
            self,
            message: str | list[str],
            skip_type_checks: bool = False,
    ):

        self._add_values(
            values=message,
            skip_type_checks=skip_type_checks,
            values_list=self._infos,
            name='message',
        )

    def add_warning(
            self,
            message: str | list[str],
            skip_type_checks: bool = False,
    ):

        self._add_values(
            values=message,
            skip_type_checks=skip_type_checks,
            values_list=self._warnings,
            name='message',
        )


class PrometheusSampleResponse(PrometheusResponse):
    RESULT_TYPE = ''

    def __init__(self, request):
        self.request = request

        self._lock = RLock()
        self._metrics = {}
        self._samples = {}
        self._samples_count = 0
        self._infos = []
        self._warnings = []

    @property
    def result_count(self):
        return self._samples_count

    def to_dict(self):
        results = []

        for metric in self._samples.values():
            for sample in metric.values():
                results.append(sample)

        return {
            'status': 'success',
            'data': {
                'resultType': self.RESULT_TYPE,
                'result': results,
            },
            'infos': self._infos,
            'warnings': self._warnings,
        }

    def add_sample(
            self,
            metric_name: str,
            metric_value: Number | Callable[None, Number],
            timestamp: datetime.datetime | Number,
            metric_labels: dict[str, str] | None = None,
            skip_type_checks: bool = False,
            skip_query_checks: bool = False,
    ):

        # metric name
        if not skip_type_checks:
            if not isinstance(metric_name, str):
                raise TypeError(
                    'metric_name has to be a string',
                )

        # metric value
        if callable(metric_value):
            metric_value = metric_value()

        if not skip_type_checks:
            if (not isinstance(metric_value, Number) or
                    isinstance(metric_value, bool)):

                raise TypeError(
                    'metric_value has to be a number',
                )

        metric_value = str(metric_value)

        # timestamp
        if not skip_type_checks:
            if not isinstance(timestamp, (datetime.datetime, Number)):
                raise TypeError(
                    'timestamp has to be a datetime.datetime object or a number',  # NOQA
                )

        if isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.timestamp()

        # metric labels
        if metric_labels is None:
            metric_labels = {}

        elif not skip_type_checks:
            if not isinstance(metric_labels, dict):
                raise TypeError('metric_labels has to be a dict')

            for key, value in metric_labels.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise TypeError(
                        'metric_labels may only contain strings',
                    )

        # query checks
        if not skip_query_checks:
            matches_query = self.request.query.matches(
                name=metric_name,
                labels=metric_labels,
            )

            if not matches_query:
                return False

        # add sample
        label_names = tuple(
            sorted([str(i) for i in metric_labels.keys()])
        )

        label_values = tuple(
            sorted([str(i) for i in metric_labels.values()])
        )

        with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = label_names

            if label_names != self._metrics[metric_name]:
                raise ValueError(
                    f'metric {metric_name}: label mismatch. expected: {self._metrics[metric_name]}, got: {label_names}',  # NOQA
                )

            if metric_name not in self._samples:
                self._samples[metric_name] = {}

            if label_values not in self._samples[metric_name]:
                self._samples[metric_name][label_values] = {
                    'metric': {
                        '__name__': metric_name,
                        **metric_labels,
                    },
                    'values': [],
                }

            values = self._samples[metric_name][label_values]['values']

            if self.RESULT_TYPE == 'vector' and len(values) > 0:
                raise ValueError(
                    f'metric {metric_name}: duplicate labels: {label_names}',
                )

            self._samples[metric_name][label_values]['values'].append(
                [timestamp, metric_value],
            )

            self._samples_count += 1

        return True


class PrometheusVectorResponse(PrometheusSampleResponse):
    RESULT_TYPE = 'vector'


class PrometheusMatrixResponse(PrometheusSampleResponse):
    RESULT_TYPE = 'matrix'


class PrometheusDataResponse(PrometheusResponse):
    def __init__(self, request):
        self.request = request

        self._data = []
        self._infos = []
        self._warnings = []

    @property
    def result_count(self):
        return len(self._data)

    def to_dict(self):
        return {
            'status': 'success',
            'data': [
                *self._data,
            ],
            'infos': self._infos,
            'warnings': self._warnings,
        }

    def add_value(
            self,
            value: str | list[str],
            skip_type_checks: bool = False,
    ):

        self._add_values(
            values=value,
            skip_type_checks=skip_type_checks,
            values_list=self._data,
            name='value',
        )


class PrometheusSeriesResponse(PrometheusDataResponse):
    def to_dict(self):
        return {
            'status': 'success',
            'data': [
                {'__name__': str(value)} for value in self._data
            ],
            'infos': self._infos,
            'warnings': self._warnings,
        }
