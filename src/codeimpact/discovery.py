"""Shared filename policy; this does not collect, import or execute tests."""

from pathlib import PurePosixPath
from typing import Literal

DiscoveryPolicy = Literal["test-files-v1", "test-files-v2"]
LEGACY_POLICY: DiscoveryPolicy = "test-files-v1"
CURRENT_POLICY: DiscoveryPolicy = "test-files-v2"


def is_test_file(path: str, *, policy: DiscoveryPolicy = CURRENT_POLICY) -> bool:
    if policy not in (LEGACY_POLICY, CURRENT_POLICY):
        raise ValueError(f"Unknown discovery policy: {policy}")
    name = PurePosixPath(path).name
    return name.endswith(".py") and (
        name.startswith("test_")
        or name.endswith("_test.py")
        or (policy == CURRENT_POLICY and name == "test.py")
    )
