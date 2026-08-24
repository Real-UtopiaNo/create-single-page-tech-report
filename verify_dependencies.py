#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys


MINIMUM_PYTHON = (3, 10)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check command-line dependencies for create-single-page-tech-report."
    )
    parser.parse_args()

    version = sys.version_info
    if version < MINIMUM_PYTHON:
        required = ".".join(str(part) for part in MINIMUM_PYTHON)
        current = f"{version.major}.{version.minor}.{version.micro}"
        print(f"FAIL Python {required}+ is required; found {current}.")
        return 1

    print(f"PASS Python {version.major}.{version.minor}.{version.micro}")
    print("PASS Required Python packages: none (standard library only).")
    print(
        "INFO A PowerPoint-capable artifact runtime is required when creating the report; "
        "this script cannot inspect Agent tool availability."
    )
    print(
        "INFO Image generation is optional. When unavailable, use editable native shapes "
        "and disclose the fallback."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
