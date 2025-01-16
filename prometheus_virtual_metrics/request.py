import datetime

from prometheus_virtual_metrics.promql import PromqlQuery


class PrometheusRequest:
    def __init__(
            self,
            server,
            http_headers,
            http_path,
            http_post_data,
            http_query,
            path,
    ):

        self.server = server
        self.http_headers = http_headers
        self.http_path = http_path
        self.http_post_data = http_post_data
        self.http_query = http_query
        self.path = path

        # promql query
        self.query = None
        query_string = ''

        if 'query' in self.http_post_data:
            query_string = self.http_post_data['query']

        elif 'match[]' in self.http_post_data:
            query_string = self.http_post_data['match[]']

        elif 'match[]' in self.http_query:
            query_string = self.http_query['match[]']

        self.query = PromqlQuery(
            query_string=query_string,
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
        self.start = self.http_post_data.get('start', None)

        if self.start is not None:
            self.start = datetime.datetime.fromtimestamp(
                float(self.start),
            )

        # end
        self.end = self.http_post_data.get('end', None)

        if self.end is not None:
            self.end = datetime.datetime.fromtimestamp(
                float(self.end),
            )

        # step
        self.step = self.http_post_data.get('step', None)

        if self.step is not None:
            self.step = int(self.http_post_data['step'])

    def __repr__(self):
        return f'<PrometheusRequest({self.http_path}, query={self.query!r}), start={self.start!r}, end={self.end!r}, step={self.duration_string}>'  # NOQA

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
