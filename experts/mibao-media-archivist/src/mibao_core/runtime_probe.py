"""Small, non-sensitive facts for one-shot MIBAO runtime checks."""

from __future__ import annotations

import platform
from typing import Any

from mibao_core.version import __version__


def one_shot_runtime_probe() -> dict[str, Any]:
    """Return a bounded probe without starting a server or inspecting user media."""

    return {
        "ok": True,
        "status": "completed",
        "probe": "runtime_check",
        "runtimeVersion": __version__,
        "executionMode": "packaged_one_shot_cli",
        "mcpConnected": False,
        "persistentProcessCreated": False,
        "mediaRead": False,
        "hostConfigModified": False,
        "separateConnectorRequired": False,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
    }
