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
        options=HTTPRequestOptions(body={"name": "async"})
    )

    response = await client.request(config)
    print(response.status_code, response.text)

    await client.close_session()

asyncio.run(main())
```

## License

MIT
