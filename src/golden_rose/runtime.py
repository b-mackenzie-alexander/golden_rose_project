import os
from collections.abc import Callable

import uvicorn

from golden_rose.config import Settings

EX_CONFIG = 78
RunServer = Callable[..., int | None]


def _read_port() -> int:
    raw_port = os.environ.get("PORT", "")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("PORT must be an integer") from exc
    if port < 1 or port > 65535:
        raise ValueError("PORT must be between 1 and 65535")
    return port


def main(run_server: RunServer = uvicorn.run) -> int:
    try:
        port = _read_port()
        Settings()  # type: ignore[call-arg]
    except ValueError:
        return EX_CONFIG

    # Container runtime must bind all interfaces; platform/network policy controls access.
    result = run_server(
        "golden_rose.main:app",
        host="0.0.0.0",  # nosec B104
        port=port,
        factory=False,
    )
    return 0 if result is None else result


if __name__ == "__main__":
    raise SystemExit(main())
