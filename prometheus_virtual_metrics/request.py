import datetime

from multidict import CIMultiDict

from prometheus_virtual_metrics.promql import PromqlQuery


class PrometheusRequest:
    """
    Attributes:
        query_string (str): PromQl query of incoming request as string
        query (prometheus_virtual_metrics.PromqlQuery): PromQl query of incoming request
        time (datetime.datetime | None): Requested time. Is only set on instant queries
        start (datetime.datetime | None): Start of the requested time range. Is only set on range queries
        end (datetime.datetime |None): End of the requested time range. Is only set on range queries
        step (int | None): Requested interval between samples. Is only set on range queries
        label_name (str): Requested label. Is only set label value requests
        timestamps (Generator[datetime.datetime]): List of timestamps between `start` and `end` with an interval of `step`
        duration_string (str): `step` as duration string. Example: `30s` (30 Seconds)

        server (prometheus_virtual_metrics.PrometheusVirtualMetricsServer): Running Server. Contains the server settings in `server.settings`

        http_headers (multidict.CIMultiDict): HTTP header of incoming request
        http_path (str): HTTP path of incoming request
        http_query (multidict.CIMultiDict): HTTP query of incoming request
        http_post_data (multidict.CIMultiDict): HTTP post data of incoming request
    """

    def __init__(
            self,
            server=None,
            http_headers=None,
            http_query=None,
            http_post_data=None,
            http_path=None,
            path=None,
            query_string='',
            time=None,
            start=None,
            end=None,
            step=None,
    ):

        self.server = server
        self.http_headers = CIMultiDict(http_headers or {})
        self.http_query = CIMultiDict(http_query or {})
        self.http_post_data = CIMultiDict(http_post_data or {})
        self.http_path = http_path or ''
        self.path = path or []

        self.query_string = query_string
        self.time = time
        self.start = start
        self.end = end
        self.step = step

        # promql query
        self.query = None

        if not self.query_string:
            if 'query' in self.http_post_data:
                self.query_string = self.http_post_data['query']

            elif 'match[]' in self.http_post_data:
                self.query_string = self.http_post_data['match[]']

            elif 'match[]' in self.http_query:
                self.query_string = self.http_query['match[]']

        self.query = PromqlQuery(
            query_string=self.query_string,
        )

        # label name
        self.label_name = ''

        if (
                len(self.path) == 3 and
                self.path[0] == 'label' and
                self.path[2] == 'values'
        ):

            self.label_name = self.path[1]

        # time
        if self.time is None:
            self.time = self.http_post_data.get('time', None)

        if self.time is not None:
            self.time = datetime.datetime.fromtimestamp(
                float(self.time),
            )

        # start
        if self.start is None:
            self.start = self.http_post_data.get('start', None)

        if self.start is not None:
            self.start = datetime.datetime.fromtimestamp(
                float(self.start),
            )

        # end
        if self.end is None:
            self.end = self.http_post_data.get('end', None)

        if self.end is not None:
            self.end = datetime.datetime.fromtimestamp(
                float(self.end),
            )

        # step
        if self.step is None:
            self.step = self.http_post_data.get('step', None)

        if self.step is not None:
            self.step = int(self.step)

    def __repr__(self):
        return f'<PrometheusRequest({self.http_path!r}, query={self.query!r}), start={self.start!r}, end={self.end!r}, step={self.duration_string}>'  # NOQA

    @property
    def duration_string(self):
        return f'{self.step or 0}s'

    @property
    def timestamps(self):
        if self.start >= self.end:
            raise ValueError(
                f"invalid time range: start must be earlier than end (start{self.start}: , end: {self.end})",  # NOQA
            )

        timedelta = datetime.timedelta(seconds=self.step)
        timestamp = self.start

        while timestamp <= self.end:
            yield timestamp

            timestamp += timedelta
