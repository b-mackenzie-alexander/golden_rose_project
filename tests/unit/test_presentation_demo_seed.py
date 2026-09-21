from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from pydantic import SecretStr
from sqlalchemy.engine import Engine

from golden_rose.application import presentation_demo_seed
from golden_rose.application.presentation_demo_seed import (
    DEMO_INTAKE_PERMISSIONS,
    presentation_seed_records,
    seed_presentation_demo_data,
)
from golden_rose.config import Settings


def _model_input(value: object) -> Any:
    return value


class FakeSession:
    instances: list["FakeSession"] = []

    def __init__(self, engine) -> None:
        self.engine = engine
        FakeSession.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        pass


def _develop_settings(*, enabled: bool) -> Settings:
    return Settings(
        environment="develop",
        auth_mode="synthetic",
        database_url="postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
        synthetic_staff_id=uuid4(),
        deployment_target="gcp-develop-private-synthetic",
        public_environment_label="Non-production develop fictional synthetic data only",
        deployed_image_digest="sha256:" + "a" * 64,
        demo_access_enabled=True,
        demo_access_password=SecretStr("ZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmY"),
        demo_access_expires_at=_model_input(
            (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        presentation_demo_seed_enabled=enabled,
    )


def test_presentation_seed_inventory_is_backend_sized_and_human_named() -> None:
    records = presentation_seed_records()
    worker_records = [record for record in records if record.kind == "worker"]
    employer_records = [record for record in records if record.kind == "employer"]

    assert len(worker_records) == 50
    assert len(employer_records) == 30
    visible_names = [
        str(record.content.get("full_name") or record.content.get("display_name"))
        for record in records
    ]
    assert all("Fictional" not in name for name in visible_names)
    assert all("Preview" not in name for name in visible_names)
    assert all("Meme" not in name for name in visible_names)


def test_disabled_presentation_seed_does_not_open_session(monkeypatch) -> None:
    FakeSession.instances.clear()
    monkeypatch.setattr(presentation_demo_seed, "Session", FakeSession)

    seed_presentation_demo_data(cast(Engine, object()), _develop_settings(enabled=False))

    assert FakeSession.instances == []


def test_enabled_presentation_seed_replays_all_records_with_demo_permissions(monkeypatch) -> None:
    calls = []
    FakeSession.instances.clear()

    def execute_intake(**kwargs):
        calls.append(kwargs)
        return {"current": {}}, False

    monkeypatch.setattr(presentation_demo_seed, "Session", FakeSession)
    monkeypatch.setattr(presentation_demo_seed, "execute_intake", execute_intake)

    engine = cast(Engine, object())
    seed_presentation_demo_data(engine, _develop_settings(enabled=True))

    assert len(FakeSession.instances) == 1
    assert FakeSession.instances[0].engine is engine
    assert len(calls) == 80
    assert len({call["command_id"] for call in calls}) == 80
    assert all(call["principal"].permissions == DEMO_INTAKE_PERMISSIONS for call in calls)
