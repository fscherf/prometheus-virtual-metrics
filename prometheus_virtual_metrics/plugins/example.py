import math


class ExamplePlugin:
    METRIC_NAME = 'prometheus_virtual_metrics_example_metric'

    def on_metric_names_request(self, request, response):
        if not request.query.name_matches(self.METRIC_NAME):
            return

        response.add_value(
            self.METRIC_NAME,
        )

    def on_label_names_request(self, request, response):
        if not request.query.name_matches(self.METRIC_NAME):
            return

        response.add_value([
            'type',
            'amplitude',
        ])

    def on_label_values_request(self, request, response):
        if not request.query.name_matches(self.METRIC_NAME):
            return

        if request.label_name == 'type':
            response.add_value([
                'sine',
                'cosine',
                'square',
                'sawtooth',
            ])

        elif request.label_name == 'amplitude':
            response.add_value([
                '1',
                '5',
                '10',
            ])

    def on_range_query_request(self, request, response):
        if not request.query.name_matches(self.METRIC_NAME):
            return

        for timestamp in request.timestamps:
            t = timestamp.timestamp() % 60

            for amplitude in (1, 5, 10):
                response.add_sample(
                    self.METRIC_NAME,
                    metric_value=lambda: (
                        math.sin(t * 2 * math.pi / 60) * amplitude
                    ),
                    metric_labels={
                        'type': 'sine',
                        'amplitude': str(amplitude),
                    },
                    timestamp=timestamp,
                )

                response.add_sample(
                    self.METRIC_NAME,
                    metric_value=lambda: (
                        math.cos(t * 2 * math.pi / 60) * amplitude
                    ),
                    metric_labels={
                        'type': 'cosine',
                        'amplitude': str(amplitude),
                    },
                    timestamp=timestamp,
                )

                response.add_sample(
                    self.METRIC_NAME,
                    metric_value=lambda: (
                        1 * amplitude if t % 60 < 30 else -1 * amplitude
                    ),
                    metric_labels={
                        'type': 'square',
                        'amplitude': str(amplitude),
                    },
                    timestamp=timestamp,
                )

                response.add_sample(
                    self.METRIC_NAME,
                    metric_value=lambda: t / 60 * amplitude,
                    metric_labels={
                        'type': 'sawtooth',
                        'amplitude': str(amplitude),
                    },
                    timestamp=timestamp,
                )

        return response
