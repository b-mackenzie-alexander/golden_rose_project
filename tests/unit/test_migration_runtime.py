from types import SimpleNamespace

from golden_rose.migration_runtime import EX_TEMPFAIL, main


class _FakeResult:
    def __init__(self, value: bool | int) -> None:
        self._value = value

    def scalar_one(self) -> bool | int:
        return self._value


class _FakeConnection:
    def __init__(
        self,
        lock_acquired: bool = True,
        role_count: int = 0,
        authority_valid: bool = True,
    ) -> None:
        self.lock_acquired = lock_acquired
        self.role_count = role_count
        self.authority_valid = authority_valid
        self.executed: list[str] = []

    def execute(self, statement, params=None):  # noqa: ANN001
        rendered = str(statement)
        self.executed.append(rendered)
        if "golden_rose_database_authority_role_count" in rendered:
            return _FakeResult(self.role_count)
        if "golden_rose_database_authority_initialized" in rendered:
            return _FakeResult(self.authority_valid)
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
        "GRANT golden_rose_migrator TO SESSION_USER" in statement
        for statement in connection.executed
    )
    assert any("pg_advisory_unlock" in statement for statement in connection.executed)
    assert engine.disposed is True


def test_migration_runtime_skips_privileged_bootstrap_for_initialized_database(
    monkeypatch,
) -> None:  # noqa: ANN001
    _set_minimal_migration_env(monkeypatch)

    connection = _FakeConnection(lock_acquired=True, role_count=3)
    engine = _FakeEngine(connection)
    observed: dict[str, object] = {}
    monkeypatch.setattr("golden_rose.migration_runtime.create_database_engine", lambda: engine)
    monkeypatch.setattr(
        "golden_rose.migration_runtime.Config",
        lambda path: SimpleNamespace(path=path, attributes={}),
    )

    def fake_upgrade(config, revision):  # noqa: ANN001
        observed["revision"] = revision

    monkeypatch.setattr("golden_rose.migration_runtime.command.upgrade", fake_upgrade)

    assert main() == 0
    assert observed == {"revision": "head"}
    assert any("golden_rose_database_authority_role_count" in item for item in connection.executed)
    assert not any(
        "GRANT golden_rose_migrator TO SESSION_USER" in item for item in connection.executed
    )
    assert any("SET ROLE golden_rose_schema_owner" in item for item in connection.executed)


def test_migration_runtime_rejects_malformed_initialized_database_authority(
    monkeypatch,
) -> None:  # noqa: ANN001
    _set_minimal_migration_env(monkeypatch)
    connection = _FakeConnection(lock_acquired=True, role_count=3, authority_valid=False)
    engine = _FakeEngine(connection)
    called = False
    monkeypatch.setattr("golden_rose.migration_runtime.create_database_engine", lambda: engine)

    def fake_upgrade(config, revision):  # noqa: ANN001
        nonlocal called
        called = True

    monkeypatch.setattr("golden_rose.migration_runtime.command.upgrade", fake_upgrade)

    assert main() == 78
    assert called is False
    assert any("golden_rose_database_authority_initialized" in item for item in connection.executed)
    assert not any("SET ROLE golden_rose_schema_owner" in item for item in connection.executed)
    assert engine.disposed is True


def test_migration_runtime_fails_closed_on_partial_database_authority_roles(
    monkeypatch,
) -> None:  # noqa: ANN001
    _set_minimal_migration_env(monkeypatch)
    connection = _FakeConnection(lock_acquired=True, role_count=2)
    engine = _FakeEngine(connection)
    called = False
    monkeypatch.setattr("golden_rose.migration_runtime.create_database_engine", lambda: engine)

    def fake_upgrade(config, revision):  # noqa: ANN001
        nonlocal called
        called = True

    monkeypatch.setattr("golden_rose.migration_runtime.command.upgrade", fake_upgrade)

    assert main() == 78
    assert called is False
    assert not any("CREATE ROLE golden_rose_schema_owner" in item for item in connection.executed)
    assert not any("SET ROLE golden_rose_schema_owner" in item for item in connection.executed)
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


def test_local_bootstrap_never_assumes_managed_administrator(monkeypatch) -> None:  # noqa: ANN001
    _set_minimal_migration_env(monkeypatch)
    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "test")
    connection = _FakeConnection()
    monkeypatch.setattr(
        "golden_rose.migration_runtime.create_database_engine", lambda: _FakeEngine(connection)
    )
    monkeypatch.setattr("golden_rose.migration_runtime.command.upgrade", lambda *_: None)
    assert main() == 0
    assert not any("cloudsqlsuperuser" in item for item in connection.executed)
    assert any("GRANT golden_rose_migrator TO CURRENT_USER" in item for item in connection.executed)


def test_installed_migration_uses_application_working_directory(monkeypatch, tmp_path) -> None:  # noqa: ANN001
    """The image installs Python under site-packages but keeps Alembic in /app."""
    import importlib.util
    from pathlib import Path

    import golden_rose.migration_runtime as source

    _set_minimal_migration_env(monkeypatch)
    installed = tmp_path / "lib" / "python3.12" / "site-packages" / "golden_rose"
    installed.mkdir(parents=True)
    module_file = installed / "migration_runtime.py"
    module_file.write_text(Path(source.__file__).read_text())
    app = tmp_path / "app"
    app.mkdir()
    (app / "alembic.ini").write_text("[alembic]\nscript_location = migrations\n")
    (app / "migrations").mkdir()
    monkeypatch.chdir(app)
    spec = importlib.util.spec_from_file_location("installed_migration_runtime", module_file)
    assert spec is not None and spec.loader is not None
    installed_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installed_module)
    monkeypatch.setattr(
        installed_module, "create_database_engine", lambda: _FakeEngine(_FakeConnection())
    )
    observed = []

    def upgrade(config, revision):  # noqa: ANN001
        assert config.get_main_option("script_location") == "migrations"
        assert Path(config.config_file_name) == app / "alembic.ini"
        observed.append(revision)

    monkeypatch.setattr(installed_module.command, "upgrade", upgrade)
    assert installed_module.main() == 0
    assert observed == ["head"]
