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
- ✅ Redaction of sensitive headers (e.g. Authorization)
- ✅ Configurable redirect policy via `RedirectPolicy`

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
from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions

client = RequestsAdapter()
config = HTTPRequestConfig(
    method="GET",
    url="https://httpbin.org/get",
    options=HTTPRequestOptions(params={"q": "test"})
)

response = client.request(config)
print(response.status_code, response.text)
```

### Asynchronous

```python
import asyncio
from http_wrap.async_adapters import AioHttpAdapter
from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions

async def main():
    client = AioHttpAdapter()
    await client.init_session()

    config = HTTPRequestConfig(
        method="POST",
        url="https://httpbin.org/post",
        options=HTTPRequestOptions(json={"name": "async"})
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
from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions

# This will raise an error unless internal access is explicitly allowed
HTTPRequestConfig.allow_internal_access()  # Enable internal access globally

config = HTTPRequestConfig(
    method="GET",
    url="http://localhost",
    options=HTTPRequestOptions(),
    allow_internal=True  # Must still be set per-request
)
```

### Keeping Internal Access Disabled by Default

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

This applies to all clients that respect `RedirectPolicy`. Note that `HTTPRequestOptions.allow_redirects` controls redirect behavior per request (e.g., enable or disable following redirects entirely).

---

## License

MIT
