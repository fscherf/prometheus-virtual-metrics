# prometheus-virtual-metrics

[![PyPI - Version](https://img.shields.io/pypi/v/prometheus-virtual-metrics)](https://pypi.org/project/prometheus-virtual-metrics)
[![PyPI - License](https://img.shields.io/pypi/l/prometheus-virtual-metrics)](https://github.com/fscherf/prometheus-virtual-metrics/blob/master/LICENSE.txt)

prometheus-virtual-metrics is a [Prometheus HTTP API](https://prometheus.io/docs/prometheus/latest/querying/api/)
compatible server [Python](https://python.org) server designed to statelessly
connect [Grafana](https://grafana.com/) to almost anything by implementing
simple plugins.

```python
import math


class ExamplePlugin:
    """
    Generates a sine curve with amplitudes of 1, 5, and 10.
    """

    def on_range_query_request(self, request, response):
        # gets called when Grafana asks for all data in a time range

        # if `sine` is not queried, we don't need to generate any data
        if not request.query.name_matches('sine'):
            return

        # `request.timestamps` is a generator that yields all timestamps
        # between `request.start` and `request.end` with an interval
        # of `request.step`
        for timestamp in request.timestamps:
            t = timestamp.timestamp() % 60

            for amplitude in (1, 5, 10):
                response.add_sample(
                    self.METRIC_NAME,
                    metric_value=math.sin(t * 2 * math.pi / 60) * amplitude,
                    metric_labels={
                        'type': 'sine',
                        'amplitude': str(amplitude),
                    },
                    timestamp=timestamp,
                )
```

prometheus-virtual-metrics is not meant to be a Prometheus replacement! It is
meant to connect Grafana to data sources like databases or REST APIs
that are not supported by Grafana itself. 

Similar projects:

 - [Grafana Infinity](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/)
 - [Grafana JSON API](https://grafana.com/grafana/plugins/marcusolsson-json-datasource/)


# Why the integration into the Prometheus HTTP API?

prometheus-virtual-metrics is just about getting data into Grafana. Prometheus
is part of the Grafana suite, so by implementing a compatible server, we get
perfect integration into Grafana UI. Additionally, Prometheus defines simple
yet powerful API and query language we can take advantage of.
