import logging

logger = logging.getLogger('TestPlugin')


class TestPlugin:
    def on_startup(self, server):
        logger.info('running on_startup')

    def on_shutdown(self, server):
        logger.info('running on_shutdown')

    def on_metric_names_request(self, request, response):
        logger.info('running on_metric_names_request')

    def on_label_names_request(self, request, response):
        logger.info('running on_label_names_request')

    def on_label_values_request(self, request, response):
        logger.info('running on_label_names_request')

    def on_query_request(self, request, response):
        logger.info('running on_query_request')

    def on_query_range_request(self, request, response):
        logger.info('running on_query_range_request')
