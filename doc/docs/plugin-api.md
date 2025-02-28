# Plugin API

prometheus-virtual-metrics plugins are simple Python classes than can define
hooks that get called on certain Grafana requests. A Grafana request can be
a query for data or metric meta data.

All hooks are optional. None of them has to be implemented. To get started,
and to see something in Grafana, `on_range_query_request()` will be enough as
a starting point.

All hooks can be async and none of them has to return something. Most hooks get
injected a `request` and a `response` which contain all API you will need.

prometheus-virtual-metrics does no other error handling than logging it when a
plugin hook crashes. If this happens in a startup hook, the server crashes and
stops. If this happens in a request hook, a HTTP 500 is returned.
If you have flaky plugins and you want to shield the other plugins from them,
use [CatchErrorsPlugin](plugins/catch-errors.md).
```python
class ExamplePlugin:

    # data request hooks
    def on_range_query_request(self, request, response):
        """
        Gets called for every PromQL range query.

        Args:
            request (prometheus_virtual_metrics.PrometheusRequest): Prometheus request
            response (prometheus_virtual_metrics.PrometheusResponse): Prometheus response
        """

        # We can check whether the our metric matches the requested metrics.
        # This is not strictly necessary because `response.add_sample()` checks
        # this too but it can help with performance when adding a lot
        # of samples
        if not request.query.name_matches(self.METRIC_NAME):
            return

        # `PrometheusRequest.timestamps` yields all timestamps between
        # `PrometheusRequest.start` and `PrometheusRequest.end`
        for timestamp in request.timestamps:
            response.add_sample(
                'example_metric',
                metric_value=1,
                metric_labels={
                    'label1': 'value1',
                },
                timestamp=timestamp,
            )

    def on_instant_query_request(self, request, response):
        """
        Gets called for every PromQL instant query (singular value per metric
        at given time).

        Args:
            request (prometheus_virtual_metrics.PrometheusRequest): Prometheus request
            response (prometheus_virtual_metrics.PrometheusResponse): Prometheus response
        """

        if not request.query.name_matches(self.METRIC_NAME):
            return

        response.add_sample(
            'example_metric',
            metric_value=1,
            metric_labels={
                'label1': 'value1',
            },
            timestamp=request.time,
        )

    # metrics and label discovery hooks
    def on_metric_names_request(self, request, response):
        """
        Gets called when Grafana tries to explore all available metrics for
        a certain point in time or in a time range.

        Args:
            request (prometheus_virtual_metrics.PrometheusRequest): Prometheus request
            response (prometheus_virtual_metrics.PrometheusResponse): Prometheus response
        """

        # we can check whether the requested metrics name or name part
        # match our metric name
        if not request.query.name_matches('example_metric'):
            return

        response.add_value('example_metric')

    def on_label_names_request(self, request, response):
        """
        Gets called when Grafana tries to explore all available label names
        for a metric at a certain point in time or in a time range.

        Args:
            request (prometheus_virtual_metrics.PrometheusRequest): Prometheus request
            response (prometheus_virtual_metrics.PrometheusResponse): Prometheus response
        """

        if not request.query.name_matches('example_metric'):
            return

        response.add_value([
            'label1',
            'label2',
        ])

    def on_label_values_request(self, request, response):
        """
        Gets called when Grafana tries to explore all available label values
        for a metric and label at a certain point in time or in a time range.

        Args:
            request (prometheus_virtual_metrics.PrometheusRequest): Prometheus request
            response (prometheus_virtual_metrics.PrometheusResponse): Prometheus response
        """

        if not request.query.name_matches(self.METRIC_NAME):
            return

        if request.label_name == 'label1':
            response.add_value('value1')

        elif request.label_name == 'label2':
            response.add_value([
                'value2.1',
                'value2.2',
            ])

    # server hooks
    def on_startup(self, server):
        """
        Gets called on server startup.

        server (prometheus_virtual_metrics.PrometheusVirtualMetricsServer): prometheus-virtual-metrics server object
        """

        pass

    def on_shutdown(self, server):
        """
        Gets called on server shutdown.

        server (prometheus_virtual_metrics.PrometheusVirtualMetricsServer): prometheus-virtual-metrics server object
        """

        pass
```

::: prometheus_virtual_metrics.PrometheusVirtualMetricsServer
    handler: python
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false

::: prometheus_virtual_metrics.PrometheusRequest
    handler: python
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false

::: prometheus_virtual_metrics.PromqlQuery
    handler: python
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false

::: prometheus_virtual_metrics.PrometheusResponse
    handler: python
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false
