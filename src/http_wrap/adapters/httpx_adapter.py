from http import HTTPStatus

import httpx
import wrapt

from http_wrap.adapters.utils import extract_host, normalize_response_headers

# from http_wrap.adapters.basesync import SyncAdapter, SyncHttpSession, std_make_args

# from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions


# @contextmanager
# def httpx_sync_session_factory(option: HTTPRequestOptions):
#     verify = option.verify
#     with httpx.Client(verify=verify) as session:
#         yield session


# def httpx_make_args(config: HTTPRequestConfig):
#     method, url, options = std_make_args(config)
#     options["follow_redirects"] = options.pop("allow_redirects", True)
#     options.pop("verify", True)
#     return method, url, options


def wrap_httpx_resp(response: httpx.Response):

    proxy = wrapt.ObjectProxy(response)

    proxy.is_permanent_redirect = (
        "location" in response.headers
        and response.status_code
        in (
            HTTPStatus.MOVED_PERMANENTLY,
            HTTPStatus.PERMANENT_REDIRECT,
        )
    )
    proxy.reason = response.reason_phrase.upper()

    status = HTTPStatus(response.status_code)
    proxy.ok = status.is_success or status.is_redirection

    proxy.original_url = response.history[0].url if response.history else response.url
    proxy.final_url = response.url

    proxy.host = extract_host(proxy.original_url)

    normalize_response_headers(proxy.headers, response.content)

    proxy.raw_headers = [
        (k.lower().encode("utf-8"), v.encode("utf-8"))
        for k, v in response.headers.items()
    ]
    return proxy


# @dataclass
# class HttpxAdapter(SyncAdapter):
#     make_session: Callable[..., ContextManager[SyncHttpSession]] = (
#         httpx_sync_session_factory
#     )
#     make_args: Callable[[HTTPRequestConfig], tuple[str, str, dict[str, Any]]] = (
#         httpx_make_args
#     )
#     wrap_response: Callable[[Any], ResponseInterface]
