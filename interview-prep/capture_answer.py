#!/usr/bin/env python3
"""Push-to-talk mic recording + local Whisper transcription for one interview answer.

Usage:
    python tools/capture_answer.py                  # press Enter to start, Enter to stop
    python tools/capture_answer.py --seconds 30      # auto-stop after 30s (no keypress), for testing
    python tools/capture_answer.py --signal-file PATH --max-seconds 300
                                                      # starts recording immediately, stops as
                                                      # soon as PATH exists (deletes it after) or
                                                      # --max-seconds elapses, whichever first.
                                                      # For driving recording from another process
                                                      # (e.g. an agent) that has no keyboard access
                                                      # to this one -- create PATH to signal "stop".
    python tools/capture_answer.py --list-devices    # show available input devices and exit
    python tools/capture_answer.py --model small.en  # override Whisper model size

Prints the transcript to stdout prefixed with "TRANSCRIPT:" on its own line.
Saves the raw recording to .tmp/interview_prep/ (disposable, gitignored).
"""

import argparse
import queue
import sys
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000
CHANNELS = 1
TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp" / "interview_prep"


def list_devices():
    print(sd.query_devices())


def record_push_to_talk() -> np.ndarray:
    input("Press Enter to start recording your answer...")
    print("Recording... press Enter to stop.")

    frames = []
    q: "queue.Queue" = queue.Queue()

    def callback(indata, _frame_count, _time_info, status):
        if status:
            print(f"[mic warning] {status}", file=sys.stderr)
        q.put(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32", callback=callback
    ):
        input()  # blocks until Enter; callback keeps buffering in the background

    while not q.empty():
        frames.append(q.get())

    if not frames:
        return np.zeros((0,), dtype="float32")
    return np.concatenate(frames, axis=0).flatten()


def record_fixed_duration(seconds: float) -> np.ndarray:
    print(f"Recording for {seconds}s...")
    audio = sd.rec(
        int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32"
    )
    sd.wait()
    return audio.flatten()


def record_until_signal(signal_path: Path, max_seconds: float) -> np.ndarray:
    print("RECORDING_STARTED", flush=True)
    frames = []
    q: "queue.Queue" = queue.Queue()

    def callback(indata, _frame_count, _time_info, status):
        if status:
            print(f"[mic warning] {status}", file=sys.stderr)
        q.put(indata.copy())

    start = time.monotonic()
    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32", callback=callback
    ):
        while True:
            if signal_path.exists():
                break
            if time.monotonic() - start > max_seconds:
                print(f"Max duration ({max_seconds}s) reached, stopping.", file=sys.stderr)
                break
            time.sleep(0.1)

    try:
        signal_path.unlink(missing_ok=True)
    except OSError:
        pass

    while not q.empty():
        frames.append(q.get())

    if not frames:
        return np.zeros((0,), dtype="float32")
    return np.concatenate(frames, axis=0).flatten()


def save_wav(audio: np.ndarray, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(audio, -1.0, 1.0)
    sf.write(str(path), clipped, SAMPLE_RATE, subtype="PCM_16")


def transcribe(audio: np.ndarray, model_size: str) -> str:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(audio, language="en", vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-devices", action="store_true", help="list audio input devices and exit")
    parser.add_argument("--seconds", type=float, default=None, help="auto-stop after N seconds instead of push-to-talk")
    parser.add_argument("--signal-file", type=str, default=None, help="start recording immediately, stop when this path exists")
    parser.add_argument("--max-seconds", type=float, default=300, help="safety cap for --signal-file mode (default: 300)")
    parser.add_argument("--model", default="base.en", help="faster-whisper model size (default: base.en)")
    args = parser.parse_args()

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    if args.list_devices:
        list_devices()
        return

    if args.signal_file:
        audio = record_until_signal(Path(args.signal_file), args.max_seconds)
    elif args.seconds:
        audio = record_fixed_duration(args.seconds)
    else:
        audio = record_push_to_talk()

    if audio.size == 0:
        print("No audio captured.", file=sys.stderr)
        print("TRANSCRIPT:")
        return

    duration = audio.size / SAMPLE_RATE
    if duration < 0.3:
        print(f"Recording too short ({duration:.2f}s) — likely no answer captured.", file=sys.stderr)
        print("TRANSCRIPT:")
        return

    wav_path = TMP_DIR / f"answer_{int(time.time())}.wav"
    save_wav(audio, wav_path)
    print(f"Saved recording: {wav_path} ({duration:.1f}s)")

    print("Transcribing locally...")
    text = transcribe(audio, args.model)
    print("TRANSCRIPT:")
    print(text)


if __name__ == "__main__":
    main()
