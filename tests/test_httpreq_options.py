import pytest

from src.http_wrap.request import HTTPRequestOptions


def test_valid_options_creation():
    opts = HTTPRequestOptions(
        headers={"X-Test": "1"},
        params={"q": "search"},
        body={"key": "value"},
        timeout=10,
        allow_redirects=True,
        verify_ssl=True,
        cookies={"session": "abc123"},
    )

    assert opts.headers["X-Test"] == "1"
    assert opts.params["q"] == "search"
    assert opts.body["key"] == "value"
    assert opts.timeout == 10
    assert opts.allow_redirects is True
    assert opts.verify_ssl is True
    assert opts.cookies["session"] == "abc123"


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("headers", [("X-Test", "1")]),
        ("params", [("q", "1")]),
        ("cookies", [("c", "v")]),
    ],
)
def test_invalid_mapping_types(field_name, value):
    with pytest.raises(TypeError, match=f"{field_name} must be a mapping"):
        HTTPRequestOptions(**{field_name: value})


def test_invalid_body_type():
    with pytest.raises(TypeError, match="body must be a mapping"):
        HTTPRequestOptions(body=[("key", "value")])


def test_invalid_timeout():
    with pytest.raises(ValueError, match="timeout must be a positive number"):
        HTTPRequestOptions(timeout=0)


def test_from_dict_success():
    opts = HTTPRequestOptions.from_dict(
        {"headers": {"X-Test": "1"}, "timeout": 3.0, "verify_ssl": False}
    )

    assert opts.headers["X-Test"] == "1"
    assert opts.timeout == 3.0
    assert opts.verify_ssl is False


def test_from_dict_with_unknown_key():
    with pytest.raises(ValueError, match="Unknown option keys"):
        HTTPRequestOptions.from_dict(
            {"unknown_field": 123, "headers": {"X-Test": "ok"}}
        )
