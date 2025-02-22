import base64

from prometheus_virtual_metrics.exceptions import ForbiddenError


def get_credentials(request):
    auth_header = request.http_headers.get('Authorization', '')

    if not auth_header or not auth_header.startswith('Basic '):
        return '', ''

    encoded_credentials = auth_header.split(' ', 1)[1]
    decoded_credentials_bytes = base64.b64decode(encoded_credentials)
    decoded_credentials_str = decoded_credentials_bytes.decode('utf-8')
    username, password = decoded_credentials_str.split(':', 1)

    return username, password


class BasicAuthPlugin:
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
