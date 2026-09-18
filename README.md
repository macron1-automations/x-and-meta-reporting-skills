# X and Meta Reporting Skills

Agent Skill package for posting reports/inboxes into **MacronX** ([github.com/macron1-automations/macronx](https://github.com/macron1-automations/macronx)) from Grok.

## What's here

- `macronx-skill-export/` — the `macronx` skill (`SKILL.md` + `scripts/` + `references/`) and `HOW_TO_IMPORT.md` / `IMPORT_PROMPT.md`
- `macronx-skill.zip` — the same skill, zipped for sharing

## Getting started

Follow **`macronx-skill-export/HOW_TO_IMPORT.md`** to import the skill:

- **Option A** — paste `IMPORT_PROMPT.md` into a new Grok conversation and attach `macronx/` (or the zip)
- **Option B** — drop the `macronx/` folder into the host's skills directory
- **Option C** — recreate from text only

After import, save your MacronX `api_url` and `api_key` **once** in `references/config.json` (Grok will ask the first time and then reuse them).

## Before first use — set `tag_id`

This skill is designed to work specifically with MacronX's `prompts/x_trends.md` workflow — see [x_trends.md](https://github.com/macron1-automations/macronx/blob/main/prompts/x_trends.md).

The shipped config uses `tag_id: 15`, which may not match the tag setup in your MacronX instance. Fix it either way:

- **Manually** — edit `tag_id` in `macronx-skill-export/macronx/references/config.json` to match your MacronX tag.
- **Via Grok** — after import, prompt Grok to update the `tag_id` in `references/config.json` to match the tag setup in MacronX.

## Recurring automation on grok.com

One way to use the skill is to set up a recurring automation on **grok.com** that runs daily. Use a prompt like:

```
Look at what's trending on X right now and give me the five most interesting conversations: what happened, why it's taking off, and the sharpest take you can find on each side of the debate.

Then turn this into JSON and Post a webhook to MacronX with that payload and set the name to `X Trends Digest`.
```

Trigger it daily.

## Smoke test

After saving URL and key into `references/config.json`:

```bash
python3 /path/to/macronx/scripts/post-inbox.py \
  --payload-json '{"text":"hello from imported skill"}' \
  --dry-run
```

