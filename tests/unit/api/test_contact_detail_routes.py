from collections.abc import Iterator
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_db_session, get_settings
from golden_rose.api.staff import contact_details
from golden_rose.main import create_app


@pytest.fixture
def http(monkeypatch) -> Iterator[Any]:
    app = create_app(engine_factory=lambda: Mock())
    app.dependency_overrides[get_db_session] = lambda: object()
    reader, sink = Mock(), Mock()
    monkeypatch.setattr(contact_details, "read_contact_details", reader)
    app.state.contact_address_access_sink = sink
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, reader, sink


def path() -> str:
    return f"/api/staff/v1/employers/{uuid4()}/contacts/{uuid4()}/details"


def address() -> dict[str, Any]:
    return {
        "contact_details_id": uuid4(),
        "version": 1,
        "address": {"line1": "10 Fictional Road", "locality": "Fictional City", "country": "US"},
    }


@pytest.mark.parametrize("suffix", ["", "/address"])
def test_sections_have_safe_headers_and_separate_values(http, suffix):
    client, reader, sink = http
    reader.return_value = (
        address()
        if suffix
        else {
            "contact_details_id": uuid4(),
            "employer_id": uuid4(),
            "employer_contact_id": uuid4(),
            "version": 1,
            "phone": "202-555-0151",
            "email": None,
            "representative_name": "Fictional Representative",
        }
    )
    response = client.get(path() + suffix)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    if suffix:
        assert "phone" not in response.json()
        assert set(sink.call_args.kwargs) == {"actor_id", "employer_id", "contact_id"}
    else:
        assert "address" not in response.json()
        sink.assert_not_called()


@pytest.mark.parametrize("suffix", ["", "/address"])
def test_develop_blocks_before_read(http, suffix):
    client, reader, sink = http
    client.app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"environment": "develop"}
    )
    assert client.get(path() + suffix).status_code == 403
    reader.assert_not_called()
    sink.assert_not_called()


@pytest.mark.parametrize("failure", ["sink", "projection", "reader", "uuid"])
def test_failures_do_not_disclose_values(http, failure):
    client, reader, sink = http
    reader.return_value = address()
    target = path() + "/address"
    if failure == "sink":
        sink.side_effect = OSError("private")
    elif failure == "projection":
        reader.return_value["private"] = "private"
    elif failure == "reader":
        reader.side_effect = RuntimeError("private")
    else:
        target = "/api/staff/v1/employers/private/contacts/private/details/address"
    response = client.get(target)
    assert response.status_code == (422 if failure == "uuid" else 503)
    assert response.headers["cache-control"] == "no-store"
    assert "private" not in response.text
    assert "Fictional" not in response.text
