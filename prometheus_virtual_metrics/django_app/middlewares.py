from django.http import JsonResponse
from multidict import CIMultiDict

from prometheus_virtual_metrics import (
    PrometheusRequest,
)

from .state import get_context


class PrometheusVirtualMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _get_remote(self, django_request):
        remote = django_request.META.get('HTTP_X_FORWARDED_FOR')

        if remote:
            return remote.split(',')[0]

        return django_request.META.get('REMOTE_ADDR')

    def __call__(self, django_request):
        context = get_context()

        if not context.valid_prometheus_request_path(django_request.path):
            return self.get_response(django_request)

        prometheus_request = PrometheusRequest(
            context=context,
            http_remote=self._get_remote(django_request),
            http_headers=CIMultiDict(django_request.headers),
            http_query=CIMultiDict(django_request.GET),
            http_post_data=CIMultiDict(django_request.POST),
            http_path=django_request.path,
        )

        prometheus_response = context.handle_prometheus_request(
            prometheus_request=prometheus_request,
        )

        return JsonResponse(
            status=prometheus_response.http_status,
            data=prometheus_response.to_dict(),
        )
