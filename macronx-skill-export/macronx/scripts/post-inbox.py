#!/usr/bin/env python3
"""POST a MacronX inbox. Only inbox.payload is required per call."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "references" / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"Missing config: {CONFIG_PATH}")
    with CONFIG_PATH.open() as f:
        return json.load(f)


def resolve_token(config: dict) -> str:
    raw = os.environ.get("MACRONX_API_KEY") or config.get("api_key") or ""
    raw = raw.strip()
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    if not raw:
        sys.exit("No API key. Set api_key in references/config.json or MACRONX_API_KEY")
    return raw


def resolve_url(config: dict) -> str:
    raw = os.environ.get("MACRONX_URL") or config.get("api_url") or ""
    raw = raw.strip()
    if not raw:
        sys.exit("No API URL. Set api_url in references/config.json or MACRONX_URL")
    return raw


def load_payload(args: argparse.Namespace) -> dict:
    if args.payload_json and args.payload_file:
        sys.exit("Use only one of --payload-json or --payload-file")
    if args.payload_file:
        path = Path(args.payload_file)
        with path.open() as f:
            data = json.load(f)
    elif args.payload_json:
        data = json.loads(args.payload_json)
    else:
        sys.exit("Provide --payload-json or --payload-file")
    if not isinstance(data, dict):
        sys.exit("payload must be a JSON object")
    return data


def build_body(config: dict, payload: dict, args: argparse.Namespace) -> dict:
    body = deepcopy(config["envelope"])
    inbox = body["inbox"]
    inbox["payload"] = payload
    if args.name:
        inbox["name"] = args.name
    if args.source:
        inbox["source"] = args.source
    if args.summary:
        inbox["summary"] = args.summary
    if args.body:
        inbox["body"] = args.body
    if args.tag_id is not None:
        inbox["tag_id"] = args.tag_id
    return body


def post(url: str, token: str, body: dict, timeout: int) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        sys.exit(f"Request failed: {exc.reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a MacronX inbox")
    parser.add_argument("--payload-json", help="Dynamic inbox.payload as JSON object")
    parser.add_argument("--payload-file", help="Path to JSON file for inbox.payload")
    parser.add_argument("--name", help="Override inbox.name")
    parser.add_argument("--source", help="Override inbox.source")
    parser.add_argument("--summary", help="Override inbox.summary")
    parser.add_argument("--body", help="Override inbox.body")
    parser.add_argument("--tag-id", type=int, help="Override inbox.tag_id (default 15)")
    parser.add_argument("--dry-run", action="store_true", help="Print body and exit")
    parser.add_argument("--timeout", type=int, default=0, help="Timeout seconds")
    args = parser.parse_args()

    config = load_config()
    url = resolve_url(config)
    timeout = args.timeout or int(config.get("timeout_seconds") or 30)
    payload = load_payload(args)
    body = build_body(config, payload, args)

    if args.dry_run:
        print(json.dumps(body, indent=2))
        return

    token = resolve_token(config)
    status, text = post(url, token, body, timeout)
    print(f"HTTP {status}")
    print(text)
    if status < 200 or status >= 300:
        sys.exit(1)


if __name__ == "__main__":
    main()
