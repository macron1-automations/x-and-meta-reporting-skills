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
