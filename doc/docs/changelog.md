# Changelog

## [v0.3.0 (2025-03-28)](https://github.com/fscherf/prometheus-virtual-metrics/releases/tag/v0.3.0)

### Breaking Changes

- The `PrometheusVirtualMetricsServer` object in hooks and requests was
  replaced with a `PrometheusVirtualMetricsContext` object

### Changes
- Integration for Django was added
- `Response.http_remote` was added
- `Response.http_status` was added
- `settings.API_URL_PREFIX` was added


## [v0.2.0 (2025-03-06)](https://github.com/fscherf/prometheus-virtual-metrics/releases/tag/v0.2.0)

### Changes

- `responses.PrometheusVectorResponse`,
  `responses.PrometheusMatrixResponse`,
  `responses.PrometheusDataResponse`, and
  `responses.PrometheusSeriesResponse`
  were merged into `response.PrometheusResponse`

- The import shortcuts
  `PrometheusVirtualMetricsError`,
  `ForbiddenError`,
  `PROMETHEUS_RESPONSE_TYPE`,
  `PrometheusResponse`,
  `PrometheusVirtualMetricsServer`,
  `PrometheusRequest`, and
  `PromqlQuery`
  were added


## [v0.1.0 (2025-02-24)](https://github.com/fscherf/prometheus-virtual-metrics/releases/tag/v0.1.0)

### Changes
- Initial release
