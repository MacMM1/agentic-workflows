# Job Application Assistant

Given a job posting, this assesses fit, tailors a CV and cover letter to it, walks you through a one-pass review, drafts a follow-up message, sends it once you approve, and logs the application.

Full SOP: [`job_application_assistant.md`](job_application_assistant.md). Run it via the `/apply` skill, or read the workflow doc directly.

## What's here

- `job_application_assistant.md` — the workflow SOP (objective, steps, error handling, verification)
- `scaffold_application.py` — creates an application folder and working copies of the CV/cover letter (`start`), then converts the edited copies into final `.docx` files (`finish`)
- `docx_convert.py` — the underlying `.docx` ⇄ indexed-text converter `scaffold_application.py` wraps; can also be run standalone for one-off conversions
- `tracker_log.py` — appends a row to `saved-applications/tracker.csv` for every status change
- `send_email.py` — sends the approved follow-up email via Gmail (reuses the OAuth connection set up for the newsletter workflow, see [`shared/gmail_auth.py`](../shared/gmail_auth.py))

## Output lives in `saved-applications/`

- `saved-applications/cv-source-materials/` — your master CV, cover letter template, LinkedIn profile text, and `metrics.md` (quantified achievements) — the raw material every application is tailored from
- `saved-applications/<role-category>-<yyyy-mm-dd>/` — one folder per application: tailored `.docx` files plus `changes-summary.md`
- `saved-applications/tracker.csv` — full history of every application and its status

## Setup

```
pip install -r requirements.txt
```

Needs `python-docx` for the `.docx` conversion tool (already in `requirements.txt`). Sending the follow-up needs the same Gmail OAuth setup as the newsletter workflow — see `newsletter/newsletter.md` for that one-time walkthrough.
