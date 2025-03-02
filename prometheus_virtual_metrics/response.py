from threading import RLock
from enum import Enum, auto
from numbers import Number
import datetime


class PROMETHEUS_RESPONSE_TYPE(Enum):
    VECTOR = auto()
    MATRIX = auto()
    DATA = auto()
    SERIES = auto()


class PrometheusResponse:
    """
    Attributes:
        response_type (prometheus_virtual_metrics.PROMETHEUS_RESPONSE_TYPE): Response type
        request (prometheus_virtual_metrics.Request): Prometheus request
        result_count (int): Count of added results/samples
    """  # NOQA

    def __init__(self, response_type, request):
        self.response_type = response_type
        self.request = request

        self._lock = RLock()
        self._metrics = {}
        self._data = []
        self._samples = {}
        self._samples_count = 0
        self._infos = []
        self._warnings = []

    @property
    def result_count(self):

        # sample response
        if (
            self.response_type in (
                PROMETHEUS_RESPONSE_TYPE.DATA,
                PROMETHEUS_RESPONSE_TYPE.SERIES,
            )
        ):

            return len(self._data)

        # data response
        return self._samples_count

    def __repr__(self):
        return f'<PrometheusResponse({self.response_type!r})>'

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

    def add_info(self, message, skip_type_checks=False):
        """
        Add info message

        Args:
            message (list[str] | str): Info message
            skip_type_checks (bool): Skip type checks
        """

        self._add_values(
            values=message,
            skip_type_checks=skip_type_checks,
            values_list=self._infos,
            name='message',
        )

    def add_warning(self, message, skip_type_checks=False):
        """
        Add warning message

        Args:
            message (list[str] | str): Info message
            skip_type_checks (bool): Skip type checks
        """

        self._add_values(
            values=message,
            skip_type_checks=skip_type_checks,
            values_list=self._warnings,
            name='message',
        )

    def add_value(self, value, skip_type_checks=False):
        """
        Add value. Only available in data and series responses.

        Args:
            value (str): Value
            skip_type_checks (bool): Skip type checks

        Raises:
            ValueError: If response is not a data or series response
        """

        # check response type
        if (
            self.response_type not in (
                PROMETHEUS_RESPONSE_TYPE.DATA,
                PROMETHEUS_RESPONSE_TYPE.SERIES,
            )
        ):

            raise TypeError('response is not a data response')

        self._add_values(
            values=value,
            skip_type_checks=skip_type_checks,
            values_list=self._data,
            name='value',
        )

    def add_sample(
            self,
            metric_name,
            metric_value,
            timestamp,
            metric_labels=None,
            skip_type_checks=False,
            skip_query_checks=False,
    ):
        """
        Add sample. Only available in vector and matrix responses.

        When `skip_query_checks` is not disabled, `add_sample` will check
        whether the added sample (metric name + metric labels) matches the
        PromQL query. If not, the sample is skipped.
        If you have computational metric values, you can provide a callback
        for `metric_value`, which then is only called if the added sample is
        not skipped.

        Args:
            metric_name (str): Metric name
            metric_value (Number | Callable[None, Number]): Metric value
            timestamp (datetime.datetime | float): Timestamp
            metric_labels (dict[str, str] | None): Metric labels
            skip_type_checks (bool): Skip type checks
            skip_query_checks (bool): Skip query checks

        Returns:
            sample_added (bool): Returns `True` if the sample was not skipped
        """

        # check response type
        if (
            self.response_type not in (
                PROMETHEUS_RESPONSE_TYPE.VECTOR,
                PROMETHEUS_RESPONSE_TYPE.MATRIX,
            )
        ):

            raise TypeError('response is not a sample response')

        # check metric name
        if not skip_type_checks:
            if not isinstance(metric_name, str):
                raise TypeError('metric_name has to be a string')

        # check metric value
        if callable(metric_value):
            metric_value = metric_value()

        if not skip_type_checks:
            if (not isinstance(metric_value, Number) or
                    isinstance(metric_value, bool)):

                raise TypeError('metric_value has to be a number')

        metric_value = str(metric_value)

        # check timestamp
        if not skip_type_checks:
            if not isinstance(timestamp, (datetime.datetime, Number)):
                raise TypeError(
                    'timestamp has to be a datetime.datetime object or a number',  # NOQA
                )

        if isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.timestamp()

        # check metric labels
        if metric_labels is None:
            metric_labels = {}

        elif not skip_type_checks:
            if not isinstance(metric_labels, dict):
                raise TypeError('metric_labels has to be a dict')

            for key, value in metric_labels.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise TypeError('metric_labels may only contain strings')

        # check query
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

            if (
                    self.response_type is PROMETHEUS_RESPONSE_TYPE.VECTOR and
                    len(values) > 0
            ):

                raise ValueError(
                    f'metric {metric_name}: duplicate labels: {label_names}',
                )

            self._samples[metric_name][label_values]['values'].append(
                [timestamp, metric_value],
            )

            self._samples_count += 1

        return True

    def to_dict(self):

        # sample response
        if (
            self.response_type in (
                PROMETHEUS_RESPONSE_TYPE.VECTOR,
                PROMETHEUS_RESPONSE_TYPE.MATRIX,
            )
        ):

            result_type = 'vector'
            results = []

            if self.response_type is PROMETHEUS_RESPONSE_TYPE.MATRIX:
                result_type = 'matrix'

            for metric in self._samples.values():
                for sample in metric.values():
                    results.append(sample)

            return {
                'status': 'success',
                'data': {
                    'resultType': result_type,
                    'result': results,
                },
                'infos': self._infos,
                'warnings': self._warnings,
            }

        # series response
        elif self.response_type is PROMETHEUS_RESPONSE_TYPE.SERIES:
            return {
                'status': 'success',
                'data': [
                    {'__name__': str(value)} for value in self._data
                ],
                'infos': self._infos,
                'warnings': self._warnings,
            }

        # data response
        else:
            return {
                'status': 'success',
                'data': [
                    *self._data,
                ],
                'infos': self._infos,
                'warnings': self._warnings,
            }
