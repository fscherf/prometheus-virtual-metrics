from threading import RLock
import datetime

from aiohttp import web


class PrometheusResponse:
    def __init__(self, request):
        self.request = request

    @property
    def query(self):
        return self.request.query

    def _to_dict(self):
        raise NotImplementedError()

    def to_http_response(self):
        return web.json_response(self._to_dict())


class PrometheusSampleResponse(PrometheusResponse):
    def __init__(self, request):
        self.request = request

        self._lock = RLock()
        self._metrics = {}
        self._samples = {}

    def _get_result_type(self):
        raise NotImplementedError()

    def _to_dict(self):
        results = []

        for metric in self._samples.values():
            for sample in metric.values():
                results.append(sample)

        return {
            'status': 'success',
            'data': {
                'resultType': self._get_result_type(),
                'result': results,
            },
        }

    def add_sample(
            self,
            metric_name,
            metric_value,
            timestamp,
            metric_labels=None,
            check_labels=True,
    ):

        # check input
        # metric name
        if not isinstance(metric_name, str):
            raise ValueError(
                'metric_name has to be a string',
            )

        # metric labels
        metric_labels = metric_labels or {}

        for key, value in metric_labels.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(
                    'metric_labels has to be a dict containing only strings',
                )

        # timestamp
        if not isinstance(timestamp, datetime.datetime):
            raise ValueError(
                'timestamp has to be a datetime.datetime object',
            )

        with self._lock:
            label_names = tuple(
                sorted([str(i) for i in metric_labels.keys()])
            )

            label_values = tuple(
                sorted([str(i) for i in metric_labels.values()])
            )

            # new metric
            if metric_name not in self._metrics:
                self._metrics[metric_name] = label_names

            # check labels
            if label_names != self._metrics[metric_name]:
                raise RuntimeError(
                    f'metric {metric_name}: label mismatch. expected: {self._metrics[metric_name]}, got: {label_names}',  # NOQA
                )

            if check_labels:
                if (not self.request.query.matches(
                        name=metric_name,
                        labels=metric_labels)):

                    return False

            # prepare value
            if callable(metric_value):
                metric_value = metric_value()

            metric_value = str(metric_value)

            # add sample
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

            self._samples[metric_name][label_values]['values'].append(
                [timestamp.timestamp(), metric_value],
            )

            return True


class PrometheusVectorResponse(PrometheusSampleResponse):
    def _get_result_type(self):
        return 'vector'


class PrometheusMatrixResponse(PrometheusSampleResponse):
    def _get_result_type(self):
        return 'matrix'


class PrometheusDataResponse(PrometheusResponse):
    def __init__(self, request):
        self.request = request

        self._data = []

    def _to_dict(self):
        return {
            'status': 'success',
            'data': [
                *self._data,
            ],
        }

    def add_values(self, values):
        for value in values:
            if not isinstance(value, str):
                raise ValueError('values has to be a list of strings')

        self._data.extend(values)


class PrometheusSeriesResponse(PrometheusDataResponse):
    def _to_dict(self):
        return {
            'status': 'success',
            'data': [
                {'__name__': str(value)} for value in self._data
            ]
        }
