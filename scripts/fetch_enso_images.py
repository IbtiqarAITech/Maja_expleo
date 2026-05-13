#!/usr/bin/env python3
"""
fetch_enso_images.py — Download ENSO satellite images from CNES/UMR server.

Source:  https://ddp.csum.umontpellier.fr/rob1e/photos
Dest:    docs/assets/enso/

Usage:
  python scripts/fetch_enso_images.py
  python scripts/fetch_enso_images.py --url https://ddp.csum.umontpellier.fr/rob1e/photos
  python scripts/fetch_enso_images.py --dry-run
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin
from urllib.request import urlopen, Request

DEFAULT_SOURCE = "https://ddp.csum.umontpellier.fr/rob1e/photos"
DEST_DIR = Path("docs/assets/enso")
USER_AGENT = "Maja_ENSO_Fetcher/1.0"


def list_remote_images(base_url: str) -> List[str]:
    """Parse directory listing for image links (jpg, png, gif, svg)."""
    req = Request(base_url, headers={"User-Agent": USER_AGENT})
    images: List[str] = []
    try:
        with urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"Warning: could not fetch directory listing: {exc}")
        return images
    import re
    for match in re.finditer(r'href=[\'"]?([^\'">]+\.(?:jpg|jpeg|png|gif|svg))[\'">]', html, re.I):
        images.append(match.group(1))
    return sorted(set(images))


def download_image(url: str, dest: Path) -> bool:
    """Download a single image. Returns True on success."""
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=60) as resp:
            data = resp.read()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception as exc:
        print(f"  FAILED: {url} — {exc}")
        return False


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download ENSO satellite images")
    parser.add_argument("--url", default=DEFAULT_SOURCE, help=f"Source URL (default: {DEFAULT_SOURCE})")
    parser.add_argument("--dest", default=str(DEST_DIR), help=f"Destination directory (default: {DEST_DIR})")
    parser.add_argument("--dry-run", action="store_true", help="List images without downloading")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    dest = Path(args.dest)
    print(f"Source: {args.url}")
    print(f"Dest:   {dest.resolve()}")
    images = list_remote_images(args.url)
    if not images:
        print("No images found (or directory listing unavailable).")
        print(f"Check manually: {args.url}")
        return 0
    print(f"Found {len(images)} image(s):")
    for img in images:
        print(f"  {img}")
    if args.dry_run:
        print("\nDry run: no images downloaded.")
        return 0
    success = 0
    for img in images:
        img_url = urljoin(args.url.rstrip("/") + "/", img)
        dest_file = dest / img
        if dest_file.exists():
            print(f"  EXISTS: {img}")
            continue
        print(f"  DOWNLOAD: {img}", end=" ... ")
        if download_image(img_url, dest_file):
            print("OK")
            success += 1
        else:
            print("FAILED")
    print(f"\nDownloaded {success}/{len(images)} images to {dest.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
