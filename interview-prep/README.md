# Interview Prep

Given a job posting, runs a voice mock interview: generates tailored questions one at a time, records and locally transcribes your spoken answers, gives honest per-answer feedback (what worked, what's missing, what you should've said), and ends with an honest 1-10 grade on whether you'd have gotten the job.

Full SOP: [`interview_prep.md`](interview_prep.md). Read the workflow doc directly to run it (no dedicated skill yet).

## What's here

- `interview_prep.md` — the workflow SOP (objective, steps, error handling, verification)
- `capture_answer.py` — mic recording + local Whisper transcription (`faster-whisper`). Supports agent-driven recording (`--signal-file`, background + chat-controlled start/stop) and standalone push-to-talk (run directly by you, Enter to start/stop)

## Output lives in `interview-prep-sessions/`

One markdown file per session: `interview-prep-sessions/<role-slug>-<company>-<yyyy-mm-dd>.md`, with every question, transcript, feedback, and the final grade breakdown.

## Setup

```
pip install -r requirements.txt
```

Needs `sounddevice`, `soundfile`, and `faster-whisper` (already in `requirements.txt`). First run downloads the local Whisper model (~150MB, one-time, needs internet); every run after that is fully offline — no API key, nothing leaves your machine.

Sanity-check your mic before a real session:

```
python interview-prep/capture_answer.py --list-devices
```
