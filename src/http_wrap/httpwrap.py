import inspect
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
    ExitStack,
    asynccontextmanager,
    contextmanager,
)
from functools import partial
from typing import Any, AsyncGenerator, Callable, Generator, Union

from http_wrap.configs import HTTPWrapConfig, run_check_config
from http_wrap.hooks import validate_client
from http_wrap.interfaces import (
    HTTPWrapClient,
    HTTPWrapResponse,
    HTTPWrapSession,
    RunCheck,
    WrapResponse,
)
from http_wrap.proxies import ClientProxy, ResponseProxy


def is_async_callable(fn: Any) -> bool:
    if inspect.iscoroutinefunction(fn):
        return True
    if hasattr(fn, "__call__"):
        return inspect.iscoroutinefunction(fn.__call__)
    return False


@contextmanager
def http_wrap_session_factory(
    *,
    sessionmaker: Callable[..., Any],
    configs: HTTPWrapConfig,
    run_check: RunCheck[HTTPWrapConfig],
    validate_client: Callable[[HTTPWrapSession], None],
    response_proxy: Callable[[Any], WrapResponse],
    **kwargs: Any,
) -> Generator[HTTPWrapClient, None, None]:
    with ExitStack() as stack:
        client = sessionmaker(**kwargs)
        validate_client(client)

        prebound_run_check = partial(run_check, config=configs)

        proxy = ClientProxy(client, prebound_run_check, response_proxy)
        if hasattr(client, "__exit__"):
            stack.enter_context(client)
        yield proxy


@asynccontextmanager
async def async_http_wrap_session_factory(
    *,
    sessionmaker: Callable[..., Any],
    configs: HTTPWrapConfig,
    run_check: RunCheck[HTTPWrapConfig],
    validate_client: Callable[[HTTPWrapSession], None],
    response_proxy: Callable[[Any], WrapResponse],
    **kwargs: Any,
) -> AsyncGenerator[HTTPWrapClient, None]:
    async with AsyncExitStack() as stack:
        client = await sessionmaker(**kwargs)
        validate_client(client)

        prebound_run_check = partial(run_check, config=configs)

        proxy = ClientProxy(client, prebound_run_check, response_proxy)
        if hasattr(client, "__aexit__"):
            await stack.enter_async_context(client)
        yield proxy


def make_client_session(
    sessionmaker: Callable[..., Any],
    configs: HTTPWrapConfig,
) -> Union[
    AbstractContextManager[HTTPWrapClient],
    AbstractAsyncContextManager[HTTPWrapClient],
]:
    def make_resp_proxy(resp: Any) -> HTTPWrapResponse:
        match, startswith, endswith, contain = configs.sanitize_resp_header
        return ResponseProxy(resp, redact=(match, startswith, endswith, contain))

    prebound_run_check = partial(run_check_config, config=configs)

    factory = (
        async_http_wrap_session_factory
        if is_async_callable(sessionmaker)
        else http_wrap_session_factory
    )

    return factory(
        sessionmaker=sessionmaker,
        configs=configs,
        run_check=prebound_run_check,
        validate_client=validate_client,
        response_proxy=make_resp_proxy,
    )
