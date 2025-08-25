#!/usr/bin/env python3
"""
copy_url_to_onedrive.py

Small CLI to upload a file from a public URL directly to OneDrive using rclone's
"copyurl" command. This avoids manual downloading to local storage.

Usage examples:
  python copy_url_to_onedrive.py \
    "https://example.com/file.zip" \
    --remote onedrive \
    --dest-path "Backups/2025" \
    --filename "file.zip"

  # When URL contains a filename, --filename is optional
  python copy_url_to_onedrive.py "https://example.com/path/report.pdf" --remote onedrive --dest-path Reports

Prerequisites:
  - rclone installed and on PATH
  - rclone remote configured (e.g., `onedrive`) via `rclone config`
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from urllib.parse import urlparse


def ensure_rclone_available(rclone_path: str) -> None:
    """Raise SystemExit if rclone is not available on this system."""
    resolved = shutil.which(rclone_path)
    if resolved is None:
        sys.exit(
            f"Error: rclone not found at '{rclone_path}'. Install rclone and ensure it is on PATH, "
            f"or pass --rclone-path with the full path to the rclone binary."
        )


def infer_filename_from_url(url: str) -> str | None:
    """Best-effort filename inference from the URL path component."""
    parsed = urlparse(url)
    candidate = os.path.basename(parsed.path)
    if candidate:
        return candidate
    return None


def build_remote_target(remote: str, dest_path: str, filename: str) -> str:
    """Construct rclone remote target like 'onedrive:Folder/Sub/file.ext'."""
    # Normalize remote name (strip trailing colon if provided by user)
    normalized_remote = remote[:-1] if remote.endswith(":") else remote

    # Normalize destination path (strip leading slashes)
    normalized_dest = dest_path.lstrip("/") if dest_path else ""

    # Join path parts using forward slashes (OneDrive uses POSIX style)
    if normalized_dest:
        return f"{normalized_remote}:{normalized_dest}/{filename}"
    return f"{normalized_remote}:{filename}"


def run_rclone_copyurl(
    rclone_path: str,
    url: str,
    target: str,
    extra_args: list[str] | None = None,
) -> int:
    """Run `rclone copyurl <url> <target>` and return the exit code."""
    cmd = [rclone_path, "copyurl", url, target, "--retries", "3", "--low-level-retries", "10", "--stats", "5s"]
    if extra_args:
        cmd.extend(extra_args)

    print("Running:", shlex.join(cmd))
    completed = subprocess.run(cmd)
    return completed.returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy a URL directly to OneDrive using rclone copyurl")
    parser.add_argument("url", help="Publicly accessible URL to copy to OneDrive")
    parser.add_argument("--remote", default="onedrive", help="rclone remote name for OneDrive (default: onedrive)")
    parser.add_argument("--dest-path", default="", help="Destination folder path in the remote (e.g., 'Backups/2025')")
    parser.add_argument("--filename", default=None, help="Destination filename (if omitted, inferred from URL if possible)")
    parser.add_argument("--rclone-path", default="rclone", help="Path to rclone binary (default: rclone)")
    parser.add_argument("--no-progress", action="store_true", help="Hide rclone progress output")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    ensure_rclone_available(args.rclone_path)

    filename: str | None = args.filename or infer_filename_from_url(args.url)
    if not filename:
        print(
            "Error: Could not infer filename from URL. Please provide --filename.",
            file=sys.stderr,
        )
        return 2

    target = build_remote_target(args.remote, args.dest_path, filename)

    extra_args: list[str] = []
    if not args.no_progress:
        extra_args.extend(["--progress", "--stats-one-line"])

    code = run_rclone_copyurl(args.rclone_path, args.url, target, extra_args=extra_args)
    if code == 0:
        print(f"Success: Uploaded to {target}")
    else:
        print(f"Failed with exit code {code}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

