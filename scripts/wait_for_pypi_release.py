#!/usr/bin/env python3
# ruff: noqa: S310, T201
"""Wait for a package version to appear on PyPI or TestPyPI."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

from http import HTTPStatus
from typing import Any, cast


REPOSITORY_URLS = {
    "pypi": "https://pypi.org/pypi",
    "testpypi": "https://test.pypi.org/pypi",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Poll PyPI/TestPyPI until a package version is available."
    )
    parser.add_argument("--repository", choices=sorted(REPOSITORY_URLS), required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--interval", type=int, default=15)
    return parser.parse_args()


def fetch_package_json(repository: str, package: str) -> dict[str, Any]:
    url = f"{REPOSITORY_URLS[repository]}/{package}/json"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "claude-builder-release-check",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return cast("dict[str, Any]", json.load(response))


def main() -> int:
    args = parse_args()
    deadline = time.monotonic() + args.timeout
    attempt = 0

    while time.monotonic() < deadline:
        attempt += 1
        try:
            payload = fetch_package_json(args.repository, args.package)
        except urllib.error.HTTPError as exc:
            if exc.code == HTTPStatus.NOT_FOUND:
                print(
                    f"[{attempt}] {args.package} not yet visible on {args.repository}; retrying in {args.interval}s..."
                )
            else:
                print(
                    f"[{attempt}] HTTP error querying {args.repository}: {exc.code} {exc.reason}",
                    file=sys.stderr,
                )
        except urllib.error.URLError as exc:
            print(
                f"[{attempt}] Network error querying {args.repository}: {exc.reason}; retrying in {args.interval}s...",
                file=sys.stderr,
            )
        else:
            files = payload.get("releases", {}).get(args.version, [])
            filenames = [
                file_info.get("filename")
                for file_info in files
                if file_info.get("filename")
            ]
            if filenames:
                print(
                    f"Found {args.package}=={args.version} on {args.repository} with files: {', '.join(filenames)}"
                )
                return 0
            print(
                f"[{attempt}] {args.package}=={args.version} not yet available on {args.repository}; retrying in {args.interval}s..."
            )

        time.sleep(args.interval)

    print(
        f"Timed out after {args.timeout}s waiting for {args.package}=={args.version} on {args.repository}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
