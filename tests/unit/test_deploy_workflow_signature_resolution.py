"""Execute the deployed shell's tag-to-digest handoff without registry access."""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("fail_immutable", [False, True])
def test_deployment_admits_only_immutable_verification(
    tmp_path: Path, fail_immutable: bool
) -> None:
    workflow = (ROOT / ".github/workflows/deploy-develop.yml").read_text()
    step = workflow.split("      - name: Verify direct OCI image authority\n", 1)[1]
    body = textwrap.dedent(step.split("        run: |\n", 1)[1].split("\n      - name:", 1)[0])
    binaries = tmp_path / "bin"
    binaries.mkdir()
    stub = f"#!{sys.executable}\n" + textwrap.dedent("""
        import json, os, sys
        from pathlib import Path
        tool = Path(sys.argv[0]).name
        args = sys.argv[1:]
        with Path("calls.jsonl").open("a") as output:
            output.write(json.dumps([tool, *args]) + "\\n")
        if tool == "docker":
            sys.stdin.read()
        elif tool == "cosign":
            if args[0] == "verify":
                if "@sha256:" in args[-1] and os.environ["FAIL_IMMUTABLE"] == "1":
                    raise SystemExit(7)
                print(json.dumps([{"critical": {
                    "identity": {"docker-reference": args[-1]},
                    "image": {"docker-manifest-digest": "sha256:" + "a" * 64}
                }}]))
            else:
                print("{}")
        elif tool == "uv":
            image = args[args.index("--image") + 1]
            signature = json.loads(Path(args[args.index("--signature") + 1]).read_text())
            assert signature[0]["critical"]["identity"]["docker-reference"] == image
            Path("admitted").touch()
    """)
    for name in ("docker", "cosign", "uv"):
        path = binaries / name
        path.write_text(stub)
        path.chmod(0o755)
    (binaries / "python").symlink_to(sys.executable)
    repository = "registry.example.test/synthetic/image"
    digest = "sha256:" + "a" * 64
    source = "b" * 40
    env = {
        **os.environ,
        "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
        "ARTIFACT_VERIFIER_ACCESS_TOKEN": "fictional-test-token",
        "DOCKER_CONFIG": str(tmp_path / "docker"),
        "MANAGED_REPOSITORY": repository,
        "BUILD_CERTIFICATE_IDENTITY": "https://example.test/workflow",
        "GITHUB_SHA": source,
        "GITHUB_ENV": str(tmp_path / "github-env"),
        "FAIL_IMMUTABLE": "1" if fail_immutable else "0",
    }
    result = subprocess.run(["bash", "-c", body], cwd=tmp_path, env=env, capture_output=True)
    calls = [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()]
    verifies = [call for call in calls if call[:2] == ["cosign", "verify"]]
    assert [call[-1] for call in verifies] == [f"{repository}:{source}", f"{repository}@{digest}"]
    for call in verifies:
        assert call[call.index("--certificate-identity") + 1] == env["BUILD_CERTIFICATE_IDENTITY"]
        assert (
            call[call.index("--certificate-oidc-issuer") + 1]
            == "https://token.actions.githubusercontent.com"
        )
    if fail_immutable:
        assert result.returncode == 7
        assert not any(
            call[0] == "uv" or call[:2] == ["cosign", "verify-attestation"] for call in calls
        )
        assert not (tmp_path / "admitted").exists()
        assert not (tmp_path / "github-env").exists()
    else:
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "admitted").exists()
        assert f"MANAGED_IMAGE={repository}@{digest}" in (tmp_path / "github-env").read_text()
        assert len([call for call in calls if call[:2] == ["cosign", "verify-attestation"]]) == 3
