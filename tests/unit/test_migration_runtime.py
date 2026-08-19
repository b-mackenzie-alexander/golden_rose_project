from types import SimpleNamespace

from golden_rose.migration_runtime import EX_TEMPFAIL, main


class _FakeResult:
    def __init__(self, value: bool) -> None:
        self._value = value

    def scalar_one(self) -> bool:
        return self._value


class _FakeConnection:
    def __init__(self, lock_acquired: bool = True) -> None:
        self.lock_acquired = lock_acquired
        self.executed: list[str] = []

    def execute(self, statement, params=None):  # noqa: ANN001
        self.executed.append(str(statement))
        return _FakeResult(self.lock_acquired)


class _ConnectionContext:
    def __init__(self, connection: _FakeConnection) -> None:
        self.connection = connection

    def __enter__(self) -> _FakeConnection:
        return self.connection

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None


class _FakeEngine:
    def __init__(self, connection: _FakeConnection) -> None:
        self.connection = connection
        self.disposed = False

    def begin(self) -> _ConnectionContext:
        return _ConnectionContext(self.connection)

    def dispose(self) -> None:
        self.disposed = True


def _set_minimal_migration_env(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "develop")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DEPLOYMENT_TARGET",
        "gcp-develop-private-synthetic",
    )
    monkeypatch.setenv(
        "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL",
        "Non-production fictional synthetic develop environment",
    )
    monkeypatch.setenv("GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST", "sha256:" + "a" * 64)
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")


def test_migration_runtime_holds_advisory_lock_for_alembic_upgrade(monkeypatch) -> None:  # noqa: ANN001
    _set_minimal_migration_env(monkeypatch)
    connection = _FakeConnection(lock_acquired=True)
    engine = _FakeEngine(connection)
    observed: dict[str, object] = {}

    monkeypatch.setattr("golden_rose.migration_runtime.create_database_engine", lambda: engine)

    def fake_upgrade(config, revision):  # noqa: ANN001
        observed["revision"] = revision
        observed["connection"] = config.attributes["connection"]

    monkeypatch.setattr("golden_rose.migration_runtime.command.upgrade", fake_upgrade)
    monkeypatch.setattr(
        "golden_rose.migration_runtime.Config",
        lambda path: SimpleNamespace(path=path, attributes={}),
    )

    assert main() == 0
    assert observed == {"revision": "head", "connection": connection}
    assert any("pg_try_advisory_lock" in statement for statement in connection.executed)
    bootstrap_index = next(
        index
        for index, statement in enumerate(connection.executed)
        if "CREATE ROLE golden_rose_schema_owner NOLOGIN" in statement
    )
    assume_role_index = next(
        index
        for index, statement in enumerate(connection.executed)
        if "SET ROLE golden_rose_schema_owner" in statement
    )
    assert bootstrap_index < assume_role_index
    assert any(
        "ALTER SCHEMA public OWNER TO golden_rose_schema_owner" in statement
        for statement in connection.executed
    )
    assert any(
        "GRANT golden_rose_migrator TO CURRENT_USER" in statement
        for statement in connection.executed
    )
    assert any("pg_advisory_unlock" in statement for statement in connection.executed)
    assert engine.disposed is True


def test_migration_runtime_fails_closed_when_advisory_lock_is_held(monkeypatch) -> None:  # noqa: ANN001
    _set_minimal_migration_env(monkeypatch)
    connection = _FakeConnection(lock_acquired=False)
    engine = _FakeEngine(connection)
    called = False

    monkeypatch.setattr("golden_rose.migration_runtime.create_database_engine", lambda: engine)

    def fake_upgrade(config, revision):  # noqa: ANN001
        nonlocal called
        called = True

    monkeypatch.setattr("golden_rose.migration_runtime.command.upgrade", fake_upgrade)
    monkeypatch.setattr(
        "golden_rose.migration_runtime.Config",
        lambda path: SimpleNamespace(path=path, attributes={}),
    )

    assert main() == EX_TEMPFAIL
    assert called is False
    assert any("pg_try_advisory_lock" in statement for statement in connection.executed)
    assert any("pg_advisory_unlock" not in statement for statement in connection.executed)
    assert engine.disposed is True
