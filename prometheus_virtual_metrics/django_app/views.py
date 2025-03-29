from django.http import JsonResponse
from multidict import CIMultiDict

from prometheus_virtual_metrics import (
    PrometheusRequest,
)

from .state import get_context


def _get_remote(django_request):
    remote = django_request.META.get('HTTP_X_FORWARDED_FOR')

    if remote:
        return remote.split(',')[0]

    return django_request.META.get('REMOTE_ADDR')


def handle_prometheus_request(django_request):
    context = get_context()

    prometheus_request = PrometheusRequest(
        context=context,
        http_remote=_get_remote(django_request),
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
