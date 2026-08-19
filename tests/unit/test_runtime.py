import pytest

from golden_rose.runtime import main


def _set_minimal_runtime_env(monkeypatch, port: str = "8080") -> None:
    monkeypatch.setenv("PORT", port)
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


def test_runtime_entrypoint_binds_all_interfaces_to_cloud_run_port(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(*args: object, **kwargs: object) -> int:
        calls.append({"args": args, "kwargs": kwargs})
        return 17

    _set_minimal_runtime_env(monkeypatch, port="8080")

    exit_status = main(run_server=fake_run)

    assert exit_status == 17
    assert calls == [
        {
            "args": ("golden_rose.main:app",),
            "kwargs": {
                "host": "0.0.0.0",
                "port": 8080,
                "factory": False,
            },
        }
    ]


@pytest.mark.parametrize("port", ["", "0", "65536", "not-a-number"])
def test_runtime_entrypoint_rejects_invalid_port_without_starting(monkeypatch, port: str) -> None:
    def fail_if_started(*args: object, **kwargs: object) -> None:
        raise AssertionError("server must not start with invalid PORT")

    _set_minimal_runtime_env(monkeypatch, port=port)

    assert main(run_server=fail_if_started) == 78
