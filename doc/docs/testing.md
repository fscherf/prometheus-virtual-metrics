# Testing

prometheus-virtual-metrics defines a [pytest](https://docs.pytest.org/) fixture
called `prometheus_virtual_metrics_context_factory` which lets you run and
query one or more prometheus-virtual-metrics servers inside a test.

```python
class ExamplePlugin:
    def on_range_query_request(self, request, response):
        for timestamp in request.timestamps:
            response.add_sample(
                'example_metric',
                metric_value=1,
                metric_labels={
                    'label1': 'value1',
                },
                timestamp=timestamp,
            )


def test_basic_auth(prometheus_virtual_metrics_context_factory):
    from types import SimpleNamespace

    # this starts a prometheus-virtual-metrics server on a random,
    # unprivileged port
    context = prometheus_virtual_metrics_context_factory(
        settings=SimpleNamespace(
            PLUGINS=[
                ExamplePlugin(),
            ],
        ),
    )

    # run checks
    response = context.request_range(
        'example_metric',
        start=datetime(1970, 1, 1, 0, 0, 0),
        end=datetime(1970, 1, 1, 0, 0, 30),
        step=30,
    )

    assert response['status'] == 'success'

    assert response['data']['result'] == [
        {
            'metric': {
                '__name__': 'example_metric',
                'label1': 'value1',
            },
            'values': [
                [0.0, '1'],
                [30.0, '1'],
            ]
        },
    ]
```

::: prometheus_virtual_metrics.pytest_plugin.PrometheusVirtualMetricsContext
    handler: python
    options:
      heading_level: 2
      show_root_heading: false
      show_source: false
