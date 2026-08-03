# Agentic Workflows

A workspace for building automations on top of Claude, split into three layers: markdown files describe *what* to do, the agent decides *how* and *when*, and Python scripts actually do it. The reasoning behind the split is simple — chaining several LLM steps together compounds error fast (90% accuracy per step is under 60% after five steps), so anything that touches an API, a file, or someone's inbox is a deterministic script, not a prompt.

`CLAUDE.md` has the full brief for how the agent is supposed to operate in here.

## Layout

- `workflows/` — plain-language SOPs. Each one says what the goal is, what it needs as input, and what order things happen in.
- `tools/` — the scripts that do the actual work: render a chart, build an email, send it, archive it.
- `.tmp/` — scratch space. Nothing in here is meant to survive between runs.
- `newsletters/` — the one output that *is* meant to survive: sent issues, archived by year, with an index.

## What's built so far

**Research-driven newsletter automation.** Give it a topic and it:

1. Researches it (this is the only step that's actually the agent — everything after is a script)
2. Writes the content out to a JSON file
3. Renders any numeric data as matplotlib charts
4. Builds an email-safe HTML newsletter — table layout, CSS inlined at build time, because Outlook still ignores `<style>` blocks and flexbox in 2026
5. Sends it through the Gmail API, with chart images attached as inline CID references instead of base64, since several major clients strip base64-inlined images
6. Archives the result

Full walkthrough, including the one-time Gmail OAuth setup, is in `workflows/newsletter.md`.

There's also a second template (`tools/build_beautydash_newsletter.py`) for a fixed-brand weekly update newsletter — no research or charts, just structured update content dropped into a matching design.

## Setup

```
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in a sender/default recipient. Gmail sending needs a one-time OAuth client set up in Google Cloud Console and a local auth pass — see `workflows/newsletter.md` for the exact steps.

## Testing changes

`tools/fixtures/sample_newsletter_content.json` is a small fixture with a toy topic, so the render → build → send → archive chain can be smoke-tested without re-running research every time.
