# Job Application Assistant Workflow

## Objective
Given a job posting, assess fit, tailor the CV and cover letter to it if suitable, get one-pass review and approval, draft a follow-up message and send it directly once approved, and log the application — every time, in the same order, without skipping or merging steps.

## One-Time Setup (before this workflow can run at all)
1. Confirm `saved-applications/cv-source-materials/` exists with:
   - `cv-master.docx` — current CV
   - `cover-letter-template.docx` — current cover letter
   - `linkedin-profile.docx` or `linkedin-profile.md` — LinkedIn "About" and experience text
   If any are missing, stop and tell the user exactly what to add and where. Never guess at their experience to fill a gap.
   - `metrics.md` (optional but check for it) — quantified achievements per role (volumes, rankings, results). If present, prefer these numbers over generic verbs when tailoring bullets in step 3. Never state a number that isn't in this file — if a role has no entry, or the entry is marked unclear/incomplete, leave that bullet qualitative rather than guessing a figure.
2. Confirm `saved-applications/tracker.csv` exists with columns: `date_applied, company, role, source_link, status, materials_folder, follow_up_sent, follow_up_date, notes`. If missing, `job-application/tracker_log.py` creates it automatically on first use.
3. Install dependencies once: `pip install -r requirements.txt` (needs `python-docx` for the `.docx` conversion tool).
4. Sending the follow-up (step 6) reuses the same Gmail OAuth connection as the newsletter workflow (`credentials.json` / `token.json` in the project root). If either is missing, run `python shared/gmail_auth.py` once — see `newsletter/newsletter.md` for the full setup walkthrough. Never run the browser auth flow on the user's behalf without telling them first.

## Inputs
- The job posting: a link (fetch it with WebFetch) or pasted text. If a link won't load or looks incomplete, ask the user to paste the text instead — never guess at requirements that can't be seen.

## Steps

### 1. Read the posting
Fetch or read the posting. Note its language, priorities, and explicit requirements — these drive step 3's tailoring choices.

### 2. Suitability check
Before tailoring anything, compare the posting's requirements against `saved-applications/cv-source-materials/` (CV, LinkedIn profile, `metrics.md` if present) and assess fit. This is grounded strictly in what's actually in `saved-applications/cv-source-materials/` — never invent or stretch experience to make the fit look stronger than it is.

- Produce a short assessment (3-5 bullets) tied to specific requirements from the posting: what matches well, what's a stretch, what's missing.
- Classify as **Good fit** or **Weak fit**.
  - **Good fit** → show the assessment briefly, then continue straight to step 3.
  - **Weak fit** → show the assessment and STOP. Wait for the user's explicit go-ahead before tailoring anything. Never tailor materials for a posting flagged as a weak fit without that go-ahead.

### 3. Tailor the materials
Pull from `saved-applications/cv-source-materials/` and adapt the CV and cover letter to this specific posting. This is agent judgment (writing), not a tool script — but every edit must follow these fixed rules, no exceptions:

- **Own words, light edits only.** Clean up a phrase or swap a word or two. Never rewrite sentences from scratch.
- **UK spelling throughout** (organise, not organize; programme, not program; etc.).
- **Natural phrasing.** Don't over-formalise or lean corporate.
- **Real Estate Data Entry role (Fortified Occupiers Home Ltd) is always framed as an internship** — never drop that.
- **Never overstate the Blackmont Consulting work.** Don't inflate scope or claim more than was actually done. Don't name the client or project specifics if the posting is public-facing in any way.
- **Referees are Juan Yanes (Blackmont) and Ayo Oyewale (Sensory Everywhere) only.** Never the user's brother, anywhere, in any field. Only include a referee at all if the posting explicitly asks for references at this stage — and never contact either referee.

**Mechanics for editing `.docx` source files** (via `job-application/scaffold_application.py`, which wraps `docx_convert.py` so a full application takes two commands instead of six):
1. `python job-application/scaffold_application.py start --role-category "Quant Graduate Analyst" --company "<name>"` — creates `saved-applications/<role-category>-<yyyy-mm-dd>/`, writes indexed working copies (`<!-- p3 style=Normal -->...`) to `.tmp/<slug>-cv.md` and `.tmp/<slug>-cover-letter.md`, and prints both paths plus the `finish` command to run next.
2. Edit those two `.tmp/*.md` files directly — tags intact, only the text after each tag changes. Do not add or remove tagged lines; this maps edits back by paragraph index, so restructuring silently fails to apply.
3. `python job-application/scaffold_application.py finish --slug <role-category>-<yyyy-mm-dd>` — converts both working copies into the final `.docx` files in the application folder, named `cv-<role-category>.docx` and `cover-letter-<role-category>.docx`.
4. Each conversion prints a warning for any paragraph it couldn't map — check the output before treating a `.docx` as final; the run replaces the first run's text and clears the rest, so it can't reproduce a formatting change that spans mid-run (e.g. bolding half a sentence).

Use a role-category name ("Business Development", "Data Analyst", "Quant Graduate Analyst"), never the company name — folder structure stays reusable. If `docx_convert.py` needs to be run directly instead (one-off, not a full application — e.g. just checking what a paragraph maps to), its own `to-md` / `to-docx` subcommands still work standalone.

### 4. One-pass review
Before anything is finalised, produce `changes-summary.md` in the same folder with:
- If step 2 found a **Good fit**, open with a 2-3 bullet "Why this fits" summary before the per-document bullets.
- What changed and why — short bullets per document, plain language, tied to what the posting asked for.
- The full tailored CV text.
- The full tailored cover letter text.

Show this in one go. The user responds with one of:
- **"Keep as is"** → finalise and save.
- **Specific edits** → make them and show only the updated section, not the whole doc again.

Nothing further needed beyond that — don't ask for re-approval unless the user flagged changes.

### 5. Follow-up message
After the user has applied, draft a short follow-up message for use roughly a week later:
- Don't repeat what's already in the cover letter — add something (interest confirmation, a question, a relevant update).
- Keep it short and simple, same "own words" standard as step 3.
- Default to email unless told otherwise.
- Write this as the final, ready-to-send text, not a template — step 6 sends it as-is once approved.

### 6. Send the follow-up
When the user is ready to send (typically about a week after applying, but whenever they say go):
1. Ask the user for the employer's email address. Never infer one from the posting or any other source, even if a contact address is listed there — always ask.
2. Show the exact final To / Subject / Body one more time and get explicit confirmation to send. This is a real message to a real person and can't be unsent — never skip this confirmation, even if the text was already approved earlier in the conversation.
3. Write the approved body to `.tmp/<slug>-followup.txt`, then send it:
   `python job-application/send_email.py --to "<employer-email>" --subject "<subject>" --body-file ".tmp/<slug>-followup.txt"`
4. On success, update the tracker for this application: re-run `job-application/tracker_log.py` with `--status "follow-up sent"`, `--follow-up-sent yes`, `--follow-up-date <today>`.

### 7. Log it
`python job-application/tracker_log.py --company "<name>" --role "<title>" --source-link "<url>" --status applied --materials-folder "saved-applications/<role-category>-<yyyy-mm-dd>" --notes "<anything worth remembering, e.g. referee requested, unusual requirement, deadline>"`

Status values: `applied`, `follow-up sent`, `interview`, `rejected`, `offer`. Re-run with `--status` updated (and `--follow-up-sent`/`--follow-up-date` set) as the application progresses — this appends a new row rather than editing in place, so `saved-applications/tracker.csv` keeps a full history per application.

## Error Handling
- **Missing source materials**: stop at setup, tell the user exactly what file is missing and where it goes. Never guess at experience to fill the gap.
- **Posting won't load**: ask the user to paste the text rather than guessing at requirements.
- **Weak-fit posting**: stop after the suitability check, show the assessment, and wait for the user's explicit go-ahead — never tailor materials for a flagged weak fit without it.
- **`scaffold_application.py start` exits with "Missing saved-applications/cv-source-materials/..."**: a required source file is gone from `saved-applications/cv-source-materials/` after setup passed — stop and tell the user exactly which file, same as a setup failure.
- **`scaffold_application.py finish` exits with "No metadata ... run 'start' first"**: the `--slug` doesn't match a folder `start` created — check for a typo, or re-run `start` if it was never actually run for this slug.
- **`docx_convert.py to-docx` reports unmapped paragraphs**: treat the output `.docx` as a draft, not final — check the flagged paragraphs by eye in Word before moving to step 4.
- **Any of the fixed rules in step 3 would be violated by the "obvious" tailoring choice** (e.g. the posting's seniority language tempts inflating the Blackmont scope): follow the rule, not the posting's cue. Flag the tension to the user in the review doc instead of silently resolving it.
- **`send_email.py` reports a 401**: tell the user to run `python shared/gmail_auth.py` to re-authenticate, then retry. Don't attempt the browser auth flow yourself.
- **Any other `send_email.py` failure**: show the error to the user; don't retry silently or guess at a fix.

## Outputs
- A suitability assessment (Good fit / Weak fit) shown before tailoring begins
- Tailored `cv-<role-category>.docx` and `cover-letter-<role-category>.docx` in `saved-applications/<role-category>-<yyyy-mm-dd>/`
- `changes-summary.md` in the same folder
- A drafted follow-up message, sent via Gmail only after the user explicitly approves the final text and recipient (never auto-sent)
- A new row in `saved-applications/tracker.csv`, plus a follow-up-sent row once step 6 completes

## Verification
- Confirm the suitability assessment in step 2 is grounded only in `saved-applications/cv-source-materials/` content — no invented qualifications.
- Confirm `saved-applications/<role-category>-<yyyy-mm-dd>/` contains both tailored documents and `changes-summary.md`.
- Open the tailored `.docx` files and spot-check formatting held up, especially around any paragraph `docx_convert.py` flagged as unmapped.
- Confirm `saved-applications/tracker.csv` gained exactly one new row with the correct company, role, and folder path.
- Re-read the tailored text once against the six fixed rules in step 3 before showing the review doc — this is the check most likely to catch a rule violation before the user ever sees it.
- After step 6 sends, confirm `send_email.py` returned a message ID and that `saved-applications/tracker.csv` reflects the follow-up-sent update.
