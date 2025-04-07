import pytest

from http_wrap import HTTPRequestConfig, HTTPRequestOptions, settings


@pytest.fixture
def default_options():
    return HTTPRequestOptions(params={"q": "test"})


@pytest.mark.parametrize("method", ["GET", "get"])
def test_valid_get_with_params(method, default_options):
    config = HTTPRequestConfig(
        method=method,
        url="https://example.com",
        options=default_options,
    )
    assert config.method == "get"
    assert config.options.params["q"] == "test"


def test_valid_post_with_body():
    config = HTTPRequestConfig(
        method="POST",
        url="https://example.com",
        options=HTTPRequestOptions(json={"key": "value"}),
    )
    assert config.options.json["key"] == "value"


@pytest.mark.parametrize("method", ["GET", "DELETE", "HEAD"])
def test_invalid_body_with_get_delete_head(method):
    with pytest.raises(ValueError, match=f"{method} request does not support a body"):
        HTTPRequestConfig(
            method=method,
            url="https://example.com",
            options=HTTPRequestOptions(json={"invalid": "data"}),
        )


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
def test_post_put_patch_without_body_should_fail(method):
    with pytest.raises(ValueError, match=f"{method} request requires a body"):
        HTTPRequestConfig(
            method=method,
            url="https://example.com",
            options=HTTPRequestOptions(),
        )


@pytest.mark.parametrize("url", ["", None, "ftp://invalid.com", "invalid-url"])
def test_invalid_url_inputs(url):
    with pytest.raises((ValueError, TypeError)):
        HTTPRequestConfig(
            method="GET", url=url, options=HTTPRequestOptions(params={"ok": "yep"})
        )


def test_invalid_options_type():
    with pytest.raises(TypeError, match="options must be of type HTTPRequestOptions"):
        HTTPRequestConfig(
            method="GET", url="https://example.com", options="not-an-option"
        )


def test_invalid_params_type():
    with pytest.raises(TypeError):
        HTTPRequestConfig(
            method="GET",
            url="https://example.com",
            options=HTTPRequestOptions(params="wrong-type"),  # should be dict
        )


@pytest.mark.parametrize(
    "url", ["http://127.0.0.1", "http://localhost", "http://192.168.1.1"]
)
def test_block_internal_ip_by_default(url):
    settings.configure(allow_internal_access=False)
    with pytest.raises(ValueError, match="Internal address '.*' is not allowed"):
        HTTPRequestConfig(
            method="GET", url=url, options=HTTPRequestOptions(params={"x": "1"})
        )


@pytest.mark.parametrize(
    "url", ["http://127.0.0.1", "http://localhost", "http://192.168.1.1"]
)
def test_allow_internal_ip_if_flag_set(url):
    settings.configure(allow_internal_access=True)
    config = HTTPRequestConfig(
        method="GET",
        url=url,
        options=HTTPRequestOptions(params={"x": "1"}),
        allow_internal=True,
    )
    assert config.url == url


def test_allow_internal_flag_without_class_call_should_fail():
    settings.configure(allow_internal_access=False)

    with pytest.raises(
        ValueError,
        match="Internal IP access is disabled. Use settings.configure",
    ):
        HTTPRequestConfig(
            method="GET",
            url="http://localhost",
            options=HTTPRequestOptions(params={"x": "1"}),
            allow_internal=True,
        )


def test_allow_internal_access_then_disable():
    settings.configure(allow_internal_access=True)
    config = HTTPRequestConfig(
        method="GET",
        url="http://localhost",
        options=HTTPRequestOptions(params={"x": "1"}),
        allow_internal=True,
    )
    assert config.url.startswith("http://localhost")

    # Desativa depois
    settings.configure(allow_internal_access=False)
    with pytest.raises(ValueError):
        HTTPRequestConfig(
            method="GET",
            url="http://localhost",
            options=HTTPRequestOptions(params={"x": "1"}),
            allow_internal=True,
        )
