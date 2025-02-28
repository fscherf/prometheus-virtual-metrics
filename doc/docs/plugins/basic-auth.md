# BasicAuthPlugin

Implements [Basic Auth](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication).


## Usage

```python
# settings.py
from prometheus_virtual_metrics.plugins import BasicAuthPlugin

PLUGINS = [
    BasicAuthPlugin(
        credentials={
            'user-1': 'password-1',
            'user-2': 'password-2',
        },
    ),
]
```

::: prometheus_virtual_metrics.plugins.BasicAuthPlugin
    handler: python
    options:
      heading_level: 2
      show_root_heading: true
      show_source: false


## Custom Authentication

By default, the authentication backend is a simple Python dict that holds all
usernames and passwords. You can override `BasicAuthPlugin.check_credentials`
to check against other backends, like files or databases:

```python
from prometheus_virtual_metrics.plugins import BasicAuthPlugin


class CustomBasicAuth(BasicAuthPlugin):
    def check_credentials(self, username, password):
        if username == 'hacker':
            return False

        return True
```

You can also use `prometheus_virtual_metrics.plugins.get_credentials` in your
plugins without using `BasicAuthPlugin`:

```python
from prometheus_virtual_metrics.plugins.basic_auth import get_credentials
from prometheus_virtual_metrics import ForbiddenError


class SecurePlugin:
    def on_range_query_request(self, request, response):
        username, password = get_credentials(request)

        if username == 'hacker':
            raise ForbiddenError('nope!')
```
