import pytest

from src.http_wrap import HTTPRequestConfig, HTTPRequestOptions


def test_valid_get_with_params():
    config = HTTPRequestConfig(
        method="GET",
        url="https://example.com",
        options=HTTPRequestOptions(params={"q": "test"}),
    )
    assert config.method == "get"
    assert config.options.params["q"] == "test"


def test_valid_post_with_body():
    config = HTTPRequestConfig(
        method="POST",
        url="https://example.com",
        options=HTTPRequestOptions(body={"key": "value"}),
    )
    assert config.options.body["key"] == "value"


@pytest.mark.parametrize("method", ["GET", "DELETE", "HEAD"])
def test_invalid_body_with_get_delete_head(method):
    with pytest.raises(ValueError, match=f"{method} request does not support a body"):
        HTTPRequestConfig(
            method=method,
            url="https://example.com",
            options=HTTPRequestOptions(body={"invalid": "data"}),
        )


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
def test_post_put_patch_without_body_should_fail(method):
    with pytest.raises(ValueError, match=f"{method} request requires a body"):
        HTTPRequestConfig(
            method=method, url="https://example.com", options=HTTPRequestOptions()
        )


def test_invalid_url_type():
    with pytest.raises(ValueError, match="url must be a non-empty string"):
        HTTPRequestConfig(
            method="GET", url="", options=HTTPRequestOptions(params={"ok": "yep"})
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
