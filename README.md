# http-wrap

[![Python Tox Tests](https://github.com/bellirodrigo2/http_wrap/actions/workflows/tox.yml/badge.svg)](https://github.com/bellirodrigo2/http_wrap/actions/workflows/tox.yml)

`http-wrap` is a decoupled and testable HTTP client wrapper for both synchronous and asynchronous requests. It provides a unified interface for configuring and sending HTTP requests using popular libraries like `requests` and `aiohttp`.

The goal is to enable clean and flexible usage across projects, while supporting:
- Full HTTP method support: GET, POST, PUT, PATCH, DELETE, HEAD
- Unified interface via `HTTPRequestConfig` and `HTTPRequestOptions`
- Response abstraction via `ResponseInterface` and `ResponseProxy`
- Batch support for async requests
- Decoupling and testability via dependency injection
- Compatibility with Clean Architecture and DDD

## Features

- ✅ Sync support via `SyncRequest` (using `requests`)
- ✅ Async support via `AioHttpAdapter` (using `aiohttp`)
- ✅ Custom configuration for headers, query params, body, timeouts, redirects, SSL, and cookies
- ✅ Batch execution of async requests
- ✅ Easy mocking for testing using `responses`, `aioresponses`, and `pytest-httpx`
- ✅ Built-in protection against requests to internal/private IPs (optional)
- ✅ Global timeout configuration via `configure()`
- ✅ Redaction of sensitive headers (e.g. Authorization)
- ✅ Configurable redirect policy via `configure()`
- ✅ Unified response wrapper via `ResponseProxy`

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

## Global Configuration

You can configure global behavior using the `configure()` function:

```python
from http_wrap.config import configure

configure(
    default_timeout=5.0,  # Set default timeout for all requests
    allow_internal_access=True,  # Allow requests to localhost / private IPs
    redact_headers=["Authorization", "X-API-KEY"],  # Mask headers in logs/debug
    redirect_policy={
        "enabled": True,
        "allow_cross_domain": False,
        "trusted_domains": ["example.com"]
    }
)
```

All options are optional, and individual requests can still override them.

---

### Blocking Requests to Internal IPs (Default Behavior)

By default, requests to internal or private IPs (e.g. `127.0.0.1`, `192.168.x.x`) are **blocked** unless allowed via configuration:

```python
from http_wrap.config import configure

configure(allow_internal_access=True)

# You must still mark each request as safe
from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions

config = HTTPRequestConfig(
    method="GET",
    url="http://localhost",
    options=HTTPRequestOptions(),
    allow_internal=True
)
```

If `configure(allow_internal_access=True)` is **not** called, requests to internal IPs will raise an error regardless of the `allow_internal` flag.

---

### Default Timeout

Set a global timeout for all requests unless explicitly overridden:

```python
from http_wrap.config import configure

configure(default_timeout=3.0)

# You can still override per-request:
config = HTTPRequestConfig(
    method="GET",
    url="https://httpbin.org/delay/2",
    options=HTTPRequestOptions(timeout=5.0)
)
```

---

### Configurable Redirect Policy

To control redirect behavior globally:

```python
from http_wrap.config import configure

configure(
    redirect_policy={
        "enabled": True,
        "allow_cross_domain": False,
        "trusted_domains": ["example.com"]
    }
)
```

This prevents redirects to untrusted domains. You can also control per-request behavior using:

```python
HTTPRequestOptions(allow_redirects=False)
```

---

## License

MIT