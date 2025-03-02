import base64

from prometheus_virtual_metrics.exceptions import ForbiddenError


def get_credentials(request):
    """
    Returns username and password as a tuple of strings. If no credentials
    can be found `('', '')` is returned.

    Args:
        request (prometheus_virtual_metrics.PrometheusRequest): Prometheus request

    Returns:
        credentials (tuple[str, str]): credentials
    """

    auth_header = request.http_headers.get('Authorization', '')

    if not auth_header or not auth_header.startswith('Basic '):
        return '', ''

    encoded_credentials = auth_header.split(' ', 1)[1]
    decoded_credentials_bytes = base64.b64decode(encoded_credentials)
    decoded_credentials_str = decoded_credentials_bytes.decode('utf-8')
    username, password = decoded_credentials_str.split(':', 1)

    return username, password


class BasicAuthPlugin:
    """
    Args:
        credentials (dict[str, str]): Login credentials as dict. Keys are usernames, values passwords.
    """

    def __init__(self, credentials=None):
        self.credentials = credentials or {}

    def _run_checks(self, request):
        try:
            username, password = get_credentials(request)

            if not username:
                raise ForbiddenError()

            if not self.check_credentials(
                username=username,
                password=password,
            ):

                raise ForbiddenError()

        except Exception as exception:
            if isinstance(exception, ForbiddenError):
                raise

            raise ForbiddenError() from exception

    def check_credentials(self, username, password):
        """
        Gets called for every incoming Grafana request.
        `username` and `password` are optained from the
        `prometheus_virtual_metrics.PrometheusRequest`, using
        `prometheus_virtual_metrics.plugins.basic_auth.get_credentials`.

        If this method returns `False`, a
        `prometheus_virtual_metrics.ForbiddenError` is raised.

        Args:
            username (str): Username as string
            password (str): password as string

        Returns:
            credentials_valid (bool): credentials are valid
        """

        if (username in self.credentials and
                self.credentials[username] == password):

            return True

        return False

    def on_metric_names_request(self, request, response):
        self._run_checks(request)

    def on_label_names_request(self, request, response):
        self._run_checks(request)

    def on_label_values_request(self, request, response):
        self._run_checks(request)

    def on_instant_query_request(self, request, response):
        self._run_checks(request)

    def on_range_query_request(self, request, response):
        self._run_checks(request)
