import datetime

from multidict import CIMultiDict

from prometheus_virtual_metrics.promql import PromqlQuery


class PrometheusRequest:
    def __init__(
            self,
            server=None,
            http_headers=None,
            http_query=None,
            http_post_data=None,
            http_path=None,
            path=None,
            query_string='',
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

        # start
        if not self.start:
            self.start = self.http_post_data.get('start', None)

        if self.start is not None:
            self.start = datetime.datetime.fromtimestamp(
                float(self.start),
            )

        # end
        if not self.end:
            self.end = self.http_post_data.get('end', None)

        if self.end is not None:
            self.end = datetime.datetime.fromtimestamp(
                float(self.end),
            )

        # step
        if not self.step:
            self.step = self.http_post_data.get('step', None)

        if self.step is not None:
            self.step = int(self.http_post_data['step'])

    def __repr__(self):
        return f'<PrometheusRequest({self.http_path!r}, query={self.query!r}), start={self.start!r}, end={self.end!r}, step={self.duration_string}>'  # NOQA

    @property
    def duration_string(self):
        return f'{self.step or 0}s'

    @property
    def timestamps(self):
        # FIXME: fix name (iter_datetimes or so)
        # FIXME: add checks whether the call can end in an endless loop

        timedelta = datetime.timedelta(seconds=self.step)
        timestamp = self.start

        while timestamp <= self.end:
            yield timestamp

            timestamp += timedelta
