from http_wrap.security import sanitize_headers


def test_headers_returns_raw_values_by_default(monkeypatch):
    monkeypatch.setattr(
        "http_wrap.security.get_settings",
        lambda: type("S", (), {"redact_headers": []})(),
    )

    h = sanitize_headers({"X-Test": "abc", "Authorization": "token123"})
    assert h["x-test"] == "abc"
    assert h["authorization"] == "token123"


def test_headers_str_redacts_configured_fields(monkeypatch):
    # Redact Authorization and X-Api-Key
    monkeypatch.setattr(
        "http_wrap.security.get_settings",
        lambda: type("S", (), {"redact_headers": ["authorization", "x-api-key"]})(),
    )
    h = sanitize_headers(
        {
            "Authorization": "secret-token",
            "X-Api-Key": "123456",
            "X-Test": "visible",
        }
    )

    output = str(h)
    assert "secret-token" not in output
    assert "123456" not in output
    assert "<redacted>" in output
    assert "x-test" in output
    assert "visible" in output


def test_headers_repr_behaves_like_str(monkeypatch):
    monkeypatch.setattr(
        "http_wrap.security.get_settings",
        lambda: type("S", (), {"redact_headers": ["x-secret"]})(),
    )
    h = sanitize_headers({"X-Secret": "topsecret", "User-Agent": "pytest"})

    output = repr(h)
    assert "topsecret" not in output
    assert "<redacted>" in output
    assert "user-agent" in output


# def test_headers_allows_raw_access():
# h = sanitize_headers({"Authorization": "raw-token"})
# assert h.raw["authorization"] == "<redacted>"


def test_headers_redacts_fields_that_start_with_prefix(monkeypatch):
    monkeypatch.setattr(
        "http_wrap.security.get_settings",
        lambda: type(
            "S",
            (),
            {
                "redact_headers": [],
                "redact_headers_startswith": ["x-private-"],
                "redact_headers_endswith": [],
            },
        )(),
    )

    h = sanitize_headers(
        {
            "X-Private-Token": "secret123",
            "X-Private-Info": "classified",
            "X-Public": "open",
        }
    )

    output = h
    assert output["x-private-token"] == "<redacted>"
    assert output["x-private-info"] == "<redacted>"
    assert output["x-public"] == "open"


def test_headers_redacts_fields_that_end_with_suffix(monkeypatch):
    monkeypatch.setattr(
        "http_wrap.security.get_settings",
        lambda: type(
            "S",
            (),
            {
                "redact_headers": [],
                "redact_headers_startswith": [],
                "redact_headers_endswith": ["-secret", "-private"],
            },
        )(),
    )

    h = sanitize_headers(
        {
            "X-Token-Secret": "hidden",
            "Authorization-Private": "sensitive",
            "X-Api-Key": "visible",
        }
    )

    output = h
    assert output["x-token-secret"] == "<redacted>"
    assert output["authorization-private"] == "<redacted>"
    assert output["x-api-key"] == "visible"
