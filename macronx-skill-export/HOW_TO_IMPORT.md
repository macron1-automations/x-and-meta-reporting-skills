# Import the MacronX skill

This folder is a standard Agent Skill package (`SKILL.md` + optional `scripts/` and `references/`). It works in Grok and in other agents that read the Agent Skills layout.

Do **not** put a live API key or personal host in `references/config.json` before sharing. Recipients save their own values once after import.

---

## Option A — Grok on grok.com / iOS / Android (easiest)

1. Send the recipient this zip **or** paste the contents of `IMPORT_PROMPT.md`.
2. They start a new Grok conversation and say:

   > Create a user skill named `macronx` from the attached files. Put it at `/home/workdir/.grok/skills/macronx/` with `SKILL.md`, `scripts/post-inbox.py`, and `references/config.json`. Leave `api_url` and `api_key` empty. When I give my URL and key, save them in `references/config.json` and reuse them on later requests.

3. Attach `macronx/` (or the zip).
4. After Grok writes the files, they should say: **Create a MacronX inbox** and supply URL + API key once if asked.

Grok user skills live in `/home/workdir/.grok/skills/<skill-name>/` and persist across sessions. The skill name in frontmatter must match the folder name (`macronx`).

---

## Option B — Drop the folder into a skills directory

Unzip, then copy the inner `macronx/` directory (the one that contains `SKILL.md`) into the host’s skills path.

| Host | Destination |
|---|---|
| Grok (this environment / persisted user skills) | `/home/workdir/.grok/skills/macronx/` |
| Grok Build (project) | `<repo>/.grok/skills/macronx/` |
| Grok Build (global) | `~/.grok/skills/macronx/` |
| Claude Code | `~/.claude/skills/macronx/` or `<repo>/.claude/skills/macronx/` |
| Codex / other Agent Skills hosts | `~/.agents/skills/macronx/` or the host’s documented skills dir |

Example:

```bash
unzip macronx-skill.zip
mkdir -p ~/.grok/skills
cp -a macronx ~/.grok/skills/
```

Restart or start a new session so the host rediscovers skills.

---

## Option C — Recreate from text only

If they cannot attach files, they paste `IMPORT_PROMPT.md` into Grok. That prompt contains the full `SKILL.md`, script, and sanitized config.

---

## After import — save URL and key once

Both are required. They are stored the same way, not passed on every request.

Resolution order:

1. `MACRONX_URL` / `MACRONX_API_KEY` environment variables
2. `api_url` / `api_key` in `references/config.json`

First time the user provides a URL or key, write it into `references/config.json` and reuse it. Do not print the token. Do not write a personal host into `SKILL.md`. Shared packages leave both config fields as empty strings.

---

## Smoke test

After saving URL and key into `references/config.json`:

```bash
python3 /path/to/macronx/scripts/post-inbox.py \
  --payload-json '{"text":"hello from imported skill"}' \
  --dry-run
```

Then, in Grok:

> Create a MacronX inbox with payload `{"text":"hello"}`

Expected: first use may ask for URL and key, save them to config, then POST with the static envelope and only `inbox.payload` changed. Later uses should not ask again.

---

## Package layout

```
macronx/
├── SKILL.md
├── scripts/
│   └── post-inbox.py
└── references/
    └── config.json    # api_url and api_key left blank on purpose
```
