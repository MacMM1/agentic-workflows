# Newsletter Automation Workflow

## Objective
Given a topic, research it, produce a styled HTML newsletter with data-driven infographics, and email it via Gmail — then archive the result so past issues aren't lost.

## One-Time Setup (before this workflow can run at all)
1. In [Google Cloud Console](https://console.cloud.google.com/): create or select a project → enable the **Gmail API** → configure the OAuth consent screen (External, testing mode is fine for personal use) → create an **OAuth 2.0 Client ID** of type **Desktop app** → download the JSON as `credentials.json` in the project root.
2. Run `python tools/gmail_auth.py`. This opens a browser for consent and saves `token.json` (already gitignored). Confirm the printed authenticated email address is correct, and that `token.json` contains a `refresh_token` key.
   - If `refresh_token` is missing (Google sometimes omits it on repeat consent), revoke prior access at `myaccount.google.com/permissions` and re-run.
3. Install dependencies once: `pip install -r requirements.txt`.
4. Optionally set `NEWSLETTER_SENDER_EMAIL` and `NEWSLETTER_DEFAULT_RECIPIENT` in `.env` (copy from `.env.example`).

## Inputs
- topic (string) — what the newsletter is about
- recipient email address (interactive runs: confirm with the user; unattended/scheduled runs: use `NEWSLETTER_DEFAULT_RECIPIENT`)

## Steps
1. **Agent researches the topic directly** using WebSearch/WebFetch — gather facts, any numeric data worth charting, and source URLs. This step is agent judgment, not a tool script.
2. **Check the minimum-content bar**: at least 2 credible sources and enough material for at least 2 real sections. If unmet, stop and ask the user how to proceed (broaden the topic, go shorter, or abandon) — never pad or fabricate content to hit the bar.
3. **Write the content JSON** to `.tmp/newsletter_<slug>-<YYYYMMDD-HHMMSS>.json` (timestamped so a retry after a downstream failure never clobbers completed research). Schema:
   ```json
   {
     "topic": "coffee prices 2026",
     "generated_at": "2026-08-01T14:32:00Z",
     "subject": "Coffee prices are about to spike — here's why",
     "preheader": "Frost in Brazil, a weak harvest, and what it means for your morning cup.",
     "headline": "Why your coffee is about to get more expensive",
     "sections": [
       {"id": "section-1", "heading": "The short version", "body": "Plain paragraph text.", "chart_ref": null},
       {"id": "section-2", "heading": "Prices by quarter", "body": "Explanatory text for the chart.", "chart_ref": "chart-1"}
     ],
     "charts": [
       {
         "id": "chart-1",
         "title": "Arabica futures price by quarter (2025-2026)",
         "type": "bar",
         "x_label": "Quarter", "y_label": "USD / lb",
         "data": {"categories": ["Q1 2025", "Q2 2025"], "series": [{"name": "Arabica", "values": [1.8, 2.1]}]},
         "note": "Source: ICE Futures U.S."
       }
     ],
     "sources": [
       {"title": "USDA Coffee: World Markets and Trade", "url": "https://example.gov/coffee-report", "accessed_at": "2026-08-01"}
     ]
   }
   ```
   - `charts` may be an empty array — not every topic has chartable numeric data, and that's valid, not an error.
   - `type` is restricted to `bar` or `line` (no pie).
   - `sources` must always be populated (enforced by step 2's minimum bar).
   - Delivery config (recipient/sender) is never part of this file — it's passed as a CLI arg when sending, keeping content generation decoupled from delivery targeting.
4. **Render charts**: `python tools/render_charts.py --content <path> --output-dir .tmp/charts_<slug>` → PNGs + `manifest.json` in that directory. No-op success if `charts` is empty.
5. **Build the HTML**: `python tools/build_newsletter_html.py --content <path> --charts-manifest .tmp/charts_<slug>/manifest.json --template tools/templates/newsletter_email.html.jinja2 --output .tmp/newsletter_<slug>.html`
6. **Confirm the recipient**: ask the user directly on interactive runs; use `NEWSLETTER_DEFAULT_RECIPIENT` on unattended/scheduled runs (the only branch point between the two modes — everything else is identical).
7. **Send it**: `python tools/send_newsletter.py --content <path> --html <path> --charts-manifest .tmp/charts_<slug>/manifest.json --to <email>`. Only proceed to step 8 if this exits 0.
8. **Archive it**: `python tools/archive_newsletter.py --html <path> --content <path> --message-id <id from step 7> --sent-at <ISO timestamp>` — copies the HTML into `newsletters/<year>/` and appends an entry to `newsletters/index.json`.
9. **Report back** to the user: subject line, recipient, archived file path, and the sources used.

## Error Handling
- **OAuth expired/revoked**: `send_newsletter.py` attempts a silent token refresh; if that fails, it prints an instruction to run `python tools/gmail_auth.py` and exits non-zero. It never tries to launch a browser flow itself mid-send — that needs interactive human access.
- **Gmail send failures**: recipient format is validated before calling the API. `HttpError` responses are caught and reported with the status code (401 = bad/expired creds, 403 = quota/permission, 400 = malformed request) instead of a raw traceback. Failed sends are never auto-retried, to avoid risking a duplicate send with no way to detect it already went out.
- **Archive/send consistency**: `archive_newsletter.py` must only run after a successful send. Never archive a newsletter that wasn't sent; if archiving fails after a successful send, report that mismatch clearly rather than dropping it silently.
- **Malformed chart data**: `render_charts.py` validates each chart spec independently (type is `bar`/`line`, category/value lengths match, values numeric). A bad chart is logged as a warning and skipped, not a run-aborting error. The template omits the image slot entirely for any chart missing from the manifest, so there's never a broken-image icon.
- **Thin research**: an agent-level judgment call at step 2, not a tool failure — stop and ask rather than pad or fabricate.

## Outputs
- A sent email (Gmail message ID)
- An archived copy at `newsletters/<year>/<date>-<slug>.html`
- An updated `newsletters/index.json` entry

## Verification
- **OAuth bootstrap**: `token.json` exists with a `refresh_token`, and `tools/gmail_auth.py` printed the correct authenticated address.
- **Fixture dry run** (repeatable without re-running research, using `tools/fixtures/sample_newsletter_content.json`):
  1. Render charts → open the PNG, check labels/colors/legend look right.
  2. Build HTML → open in a browser; confirm no leftover `<style>` block, images have explicit width/height, layout holds at 600px.
  3. Send to your own address — a real but cheap/quota-only Gmail call, safe to repeat while iterating.
  4. Archive → confirm the dated file lands under `newsletters/<year>/` and `index.json` gets a correct new entry.
- **One real end-to-end run**: an actual small topic, real research, sent to your own address, full chain start to finish.
- **Regression habit**: re-run the fixture dry run after any change to `tools/*.py`, before trusting it against a real research cycle again.

## Future: Recurring Schedule
Nothing here is specific to an interactive session — a scheduled agent run via Claude Code's `schedule` skill has its own WebSearch/WebFetch access and can follow this exact SOP unchanged with a preset topic on a cadence. No separate tooling is needed until that's actually set up.
