# Interview Prep Workflow

## Objective
Run a voice mock interview tailored to a specific job posting: generate role-specific questions one at a time, capture and transcribe the user's spoken answer, give honest per-answer feedback (what was strong, what was missing), and end with an honest grade out of 10 on whether the user would have gotten the job — plus a saved record of the full session.

## Required inputs
- **Job description** — pasted text or a link (fetch with WebFetch). If a link won't load or looks incomplete, ask the user to paste the text instead. Never invent requirements that can't be seen.
- **Resume/CV text** (optional but strongly preferred) — pasted text, a path to a file, or reuse `saved-applications/cv-source-materials/` if the user points at it. Without this, JD-fit grading is generic ("this JD asks for X, your answers didn't demonstrate it") rather than grounded in the user's actual background.
- **Number of questions** — ask if not specified. Default to 6: roughly 2 behavioral, 3-4 role/technical drawn from the JD's stated requirements, and optionally 1 curveball. Adjust the mix for the role (e.g. more technical for an engineering role, more case/situational for consulting).

## Tool used
`interview-prep/capture_answer.py` — mic recording + local Whisper transcription (`faster-whisper`, runs fully offline after the model's first download). Prints the transcript to stdout after `TRANSCRIPT:`. Saves the raw `.wav` to `.tmp/interview_prep/` (disposable).

One-time setup: `pip install -r requirements.txt`. First run downloads the `base.en` model (~150MB, needs internet once); every run after that is offline. Sanity-check the mic before a real session: `python interview-prep/capture_answer.py --list-devices`.

**Important constraint discovered running this live: an agent's Bash tool calls have no live keyboard connection to the user.** `input()` (used for true push-to-talk) fails immediately with EOF when the agent runs it — it only works if the *user* runs the script themselves, in their own terminal. This gives two supported recording modes:

- **Agent-driven (default, stays in chat)** — the agent runs the recording in the background with `--signal-file <path>`, which starts capturing immediately (no keypress needed) and stops as soon as that file exists. The agent tells the user "reply 'start' when ready," launches the background recording on that reply, tells the user to answer, and on the user's "stop" reply touches the signal file, then reads the transcript from the completed background task. See step 3 below for the exact sequence.
- **User-run standalone** — the user runs `python interview-prep/capture_answer.py` directly in their own terminal (true Enter-to-start/Enter-to-stop), then pastes the printed transcript back into chat. Use this if the user prefers manual control over exact start/stop timing, or if the agent-driven mode is unavailable for some reason.

## Steps

### 1. Gather context
Collect the job description (and resume, if available). Note the JD's explicit requirements and priorities — these drive both question generation (step 2) and grading (step 5).

### 2. Generate the question set
This is agent judgment, not a script. Write N questions (see "Number of questions" above) tailored to the JD: behavioral questions should target situations the JD's requirements imply (e.g. "tell me about a time you..." mapped to a specific listed responsibility), technical/role questions should probe the JD's specific stack or domain, not generic filler.

Do **not** show the full question list upfront — reveal one question at a time, immediately before the user answers it. Showing the whole list in advance lets the user script answers instead of practicing real recall, which defeats the point.

### 3. Ask → capture → transcribe → feedback, one question at a time
For each question, in order (agent-driven mode — see "Tool used" above for the user-run alternative):
1. Post the question in chat and ask the user to reply "start" when ready.
2. On "start": run `python interview-prep/capture_answer.py --signal-file .tmp/interview_prep/stop.signal --max-seconds 300` via Bash with `run_in_background: true`. Recording begins almost immediately — tell the user it's recording and to answer now, and to reply "stop" when done.
3. On "stop": touch the signal file (`.tmp/interview_prep/stop.signal`) to end the recording, then retrieve the background task's output (block until it completes — transcription takes a few seconds after the signal).
4. Read the `TRANSCRIPT:` line from that output. If it's empty or clearly garbled (e.g. one or two words for a question that needs a real answer), show the user what was captured and ask if they want to redo it — never grade an empty or obviously-mistranscribed answer.
5. Show the transcript back to the user briefly (so they can catch a bad transcription) alongside feedback, in three parts:
   - **What worked** — specific, structured, on-target moments.
   - **What's missing** — an unaddressed part of the question, a JD requirement the answer could have tied to, no concrete example or quantified result, weak structure (e.g. no STAR shape for a behavioral question), or rambling/unclear delivery.
   - **What you should've said** — a tightened model version of their actual answer (same story, same real facts/numbers — never invent new ones), rewritten to fix the structure/clarity issues and close the gaps just named. This is a rewrite of their answer, not a generic template.
6. Move to the next question.

Keep feedback honest and specific — tied to the actual JD and the actual transcript, not generic encouragement. The point is to surface real gaps before the real interview.

### 4. Final grade
After the last question, give an honest combined grade out of 10:
- **Generic interview quality** — structure, clarity, specificity, confidence, across all answers.
- **JD-fit** — how well the answers collectively demonstrate the JD's stated requirements, grounded in the resume if one was provided.
- **Combined verdict** — the single 1-10 score plus a short, honest paragraph on whether this performance would likely have gotten the job, and the top 1-3 things that would have made the biggest difference. Do not soften this to spare feelings — an honest low score is more useful than a flattering one.

### 5. Save the session
Write the full session — every question, its transcript, its feedback, and the final grade breakdown — to `interview-prep-sessions/<role-slug>-<company>-<yyyy-mm-dd>.md`. Create the folder if it doesn't exist.

## Expected outputs
- `interview-prep-sessions/<role-slug>-<company>-<yyyy-mm-dd>.md` — full record of the session (questions, transcripts, feedback, final grade).

## Error handling
- **No mic detected / `sounddevice` error** — run `python interview-prep/capture_answer.py --list-devices` and confirm a real input device is listed; check Windows mic privacy permissions if the list is empty.
- **First-run model download fails** — needs internet for the one-time `faster-whisper` model download; retry once connected. All runs after that are offline.
- **Empty or near-silent transcript** — treat as "no answer captured," not a bad answer. Offer to redo.
- **Transcript looks wrong (background noise, mumbling)** — show it to the user before scoring and offer a redo rather than grading a mistranscription.

## Verification
Before a real session, run `python interview-prep/capture_answer.py` standalone once (answer any test question aloud) and confirm a sane transcript comes back.
