Create a user skill named macronx. Write the three files below exactly, under /home/workdir/.grok/skills/macronx/. Do not add README or extra files. Leave api_url and api_key empty. When the user later provides a URL or API key, save those values in references/config.json and reuse them. Do not require them on every request. After writing, list the created paths.

==========
FILE: /home/workdir/.grok/skills/macronx/SKILL.md
==========

---
name: macronx
description: Create an inbox on the MacronX API by POSTing a webhook. Use when the user says MacronX, create an inbox, post to inboxes, send a MacronX webhook, or push a payload to the MacronX inboxes endpoint. The request body is static except inbox.payload, which is built from the current request. Endpoint and API key are stored in config, not passed on every request.
metadata:
  type: integration
  version: "1.1"
---

# MacronX Inbox Webhook

POST a new inbox to the MacronX API. The envelope is fixed. Only `inbox.payload` changes per request.

## When to run

Trigger on requests such as:

- create a MacronX inbox
- post / send this to MacronX
- push a payload to the inboxes API
- webhook this into MacronX

Do not use this skill for other HTTP APIs.

## Defaults

Read `references/config.json` before posting.

- Method — POST
- URL — from saved config / env (never hardcode a host in this file)
- Auth — `Authorization: Bearer <token>`
- Content-Type — `application/json`
- Success — HTTP 2xx

URL resolution order:

1. Environment variable `MACRONX_URL` (full inbox-create URL)
2. `api_url` in `references/config.json`

Token resolution order:

1. Environment variable `MACRONX_API_KEY` (raw token, no `Bearer` prefix)
2. `api_key` in `references/config.json`

Never print the token. Do not pass URL or API key as script flags on every request.

If either value is missing, ask the user once. Then save it into `references/config.json` (`api_url` and/or `api_key`) so later requests reuse it. Prefer that saved config over asking again. Shared copies of this skill must ship with both fields empty.

## Static envelope

Send exactly this shape. Replace only `inbox.payload`.

```json
{
  "inbox": {
    "name": "Insomnia test",
    "source": "grok",
    "summary": "Created from Insomnia",
    "body": "Testing inbox creation from Insomnia",
    "tag_id": 15,
    "payload": {}
  }
}
```

`inbox.payload` must be a JSON object. If the user gives prose, wrap it as `{"text": "..."}`. If they give JSON, send that object as `payload`.

## Optional overrides

Only change these keys when the user explicitly asks:

- `inbox.name`
- `inbox.source`
- `inbox.summary`
- `inbox.body`
- `inbox.tag_id` (default 15)

Otherwise keep the static values above.

## How to post

Prefer the bundled script so auth and the envelope stay consistent:

```bash
python3 scripts/post-inbox.py --payload-json '{"example": true}'
```

Useful flags:

- `--payload-json '{...}'` — dynamic payload object (required unless `--payload-file`)
- `--payload-file path.json` — read payload from a file
- `--name`, `--source`, `--summary`, `--body`, `--tag-id` — optional envelope overrides
- `--dry-run` — print the request body, do not send
- `--timeout 30` — seconds

Do not add a `--url` or `--api-key` flag. Those values live in env or `references/config.json`.

The script prints status code and response body. Report both to the user.

If the script cannot run, equivalent curl:

```bash
curl -sS -X POST "$MACRONX_URL" \
  -H "Authorization: Bearer $MACRONX_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d @body.json
```

Do not add a second `Bearer` prefix. The token is the raw key only.

## After the request

- 2xx — summarize the response (id, name, status if present) and confirm the payload that was sent
- 401 / 403 — auth failed. Ask the user to refresh `api_key` in `references/config.json` or `MACRONX_API_KEY`. Do not retry with a doubled Bearer prefix
- 404 / connection error — the configured host may be down. Show the error. You may show the URL to the current user for debugging; do not add it to SKILL.md
- 422 / 400 — show the API error body. Do not invent fields the API did not request

## Do not

- Do not GET/PATCH/DELETE this endpoint unless the user supplies a new contract
- Do not log or echo the Authorization header
- Do not hardcode a personal host into SKILL.md
- Do not require the user to pass URL or API key on every request after they have been saved
- Do not change static envelope keys on a guess
- Do not send `payload` as a string if an object is available


==========
FILE: /home/workdir/.grok/skills/macronx/references/config.json
==========

{
  "api_url": "",
  "api_key": "",
  "auth_scheme": "Bearer",
  "method": "POST",
  "timeout_seconds": 30,
  "envelope": {
    "inbox": {
      "name": "Insomnia test",
      "source": "grok",
      "summary": "Created from Insomnia",
      "body": "Testing inbox creation from Insomnia",
      "tag_id": 15,
      "payload": {}
    }
  }
}


==========
FILE: /home/workdir/.grok/skills/macronx/scripts/post-inbox.py
==========

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
