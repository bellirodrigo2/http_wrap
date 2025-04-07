# http-wrap

[![Python Tox Tests](https://github.com/bellirodrigo2/http_wrap/actions/workflows/tox.yml/badge.svg)](https://github.com/bellirodrigo2/http_wrap/actions/workflows/tox.yml)

`http-wrap` is a decoupled and testable HTTP client wrapper for both synchronous and asynchronous requests. It provides a unified interface for configuring and sending HTTP requests using popular libraries like `requests` and `aiohttp`.

The goal is to enable clean and flexible usage across projects, while supporting:
- Full HTTP method support: GET, POST, PUT, PATCH, DELETE, HEAD
- Unified interface via `HTTPRequestConfig` and `HTTPRequestOptions`
- Response abstraction via `ResponseInterface`
- Batch support for async requests
- Decoupling and testability via dependency injection
- Compatibility with Clean Architecture and DDD

## Features

- ✅ Sync support via `SyncRequest` (using `requests`)
- ✅ Async support via `AioHttpAdapter` (using `aiohttp`)
- ✅ Custom configuration for headers, query params, body, timeouts, redirects, SSL, and cookies
- ✅ Batch execution of async requests
- ✅ Easy mocking for testing using `responses` and `aioresponses`
- ✅ Built-in protection against requests to internal/private IPs (optional)
- ✅ Global timeout configuration via factory method
- ✅ Configurable redirect policy via `RedirectPolicy`
- ✅ Redação automática de headers sensíveis como `Authorization` e `Proxy-Authorization`

## Installation

```bash
pip install http-wrap
```

Or if using [Poetry](https://python-poetry.org/):

```bash
poetry add http-wrap
```

## Example Usage

### Synchronous

```python
from http_wrap.sync_adapters import RequestsAdapter
from http_wrap.request import configure

client = RequestsAdapter()
config = configure(
    method="GET",
    url="https://httpbin.org/get",
    params={"q": "test"},
)

response = client.request(config)
print(response.status_code, response.text)
```

### Asynchronous

```python
import asyncio
from http_wrap.async_adapters import AioHttpAdapter
from http_wrap.request import configure

async def main():
    client = AioHttpAdapter()
    await client.init_session()

    config = configure(
        method="POST",
        url="https://httpbin.org/post",
        json={"name": "async"},
    )

    response = await client.request(config)
    print(response.status_code, response.text)

    await client.close_session()

asyncio.run(main())
```

## Advanced Configuration

### Enforcing a Default Timeout

You can set a global default timeout using the factory method `force_default_timeout` in `HTTPRequestOptions`:

```python
from http_wrap.request import HTTPRequestOptions

HTTPRequestOptions.force_default_timeout(5.0)  # All requests default to 5 seconds unless explicitly set
```

Each request can still override the timeout by passing a specific value.

---

### Blocking Requests to Internal IPs

To prevent accidental requests to internal or private IP addresses (e.g. `127.0.0.1`, `192.168.x.x`), this behavior is enabled by default:

```python
from http_wrap.request import configure, HTTPRequestConfig

# Enable internal access globally
HTTPRequestConfig.allow_internal_access()

config = configure(
    method="GET",
    url="http://localhost",
    allow_internal=True,
)
```

If `HTTPRequestConfig.allow_internal_access()` is **not** called, any attempt to access internal addresses—even with `allow_internal=True`—will raise an error. This ensures security out of the box.

---

### Configurable Redirect Policy

You can configure global redirect behavior using `RedirectPolicy`:

```python
from http_wrap.security import RedirectPolicy

RedirectPolicy.set_redirect_policy(
    enabled=True,  # Enable redirect filtering
    allow_cross_domain=False,  # Disallow redirects to a different domain
    trusted_domains=["example.com"]  # Allow redirects only to these domains
)
```
If not configured, the redirect policy is disabled by default (enabled=False), meaning all redirects are allowed normally.

The `HTTPRequestOptions.allow_redirects` option controls redirect behavior per request (i.e., whether to follow redirects or not).

This policy applies globally to all clients that support RedirectPolicy.

---

### ✅ Redação de Headers Sensíveis

Por padrão, headers sensíveis como `Authorization` e `Proxy-Authorization` são ocultados quando impressos ou logados para evitar vazamento de credenciais:

```python
from http_wrap.request import configure

config = configure(
    method="GET",
    url="https://httpbin.org/anything",
    headers={"Authorization": "Bearer super-secret-token"}
)

print(config)  # Authorization será exibido como "****"
```

Você pode adicionar headers personalizados à lista de sanitização:

```python
from http_wrap.security import SensitiveHeaders

SensitiveHeaders.add("X-Api-Key")
```

---

## License

MIT

