# AI reliability

## Conversation behavior

The selected provider receives the current prompt and recent complete user/assistant
turns from the same conversation. Recent context is capped at 24 messages and 16,000
characters, keeping complete pairs. These are character limits, not tokenizer-specific
limits; very large current prompts can still exceed a particular model's context window.
Previous image bytes are not persisted or replayed; attach the image again for follow-up
questions that require inspecting it.

Saving ordinary conversation messages does not depend on memory learning or summary
settings. Failed requests may leave an unanswered user message; those incomplete turns
are excluded from subsequent model context. A completed stream saves the visible answer.

Private chat context lives in the desktop client's RAM. It is not loaded from SQLite,
does not use saved personal memories or summaries, and clears on a new chat or privacy
mode change. Explicit persistent-memory commands are blocked in private chat. Knowledge
search in private chat uses local text search without embedding requests.

## Output and cancellation

The stream reader accepts SSE data lines with or without a space after the colon.
Malformed output, premature disconnects, and reasoning-only responses produce visible
errors. Separate reasoning fields and inline `<think>` blocks are not presented as final
answers. Length-limited answers show a warning. Markdown rendering disables embedded HTML.

Stopping a response cancels its HTTP request and queued speech. New chats detach old
workers, ignore their late signals, and retain their objects until their threads finish.
Shutdown keeps Qt's event loop running until workers exit. Native speech synthesis or
Whisper inference already in progress must return before their threads can finish;
these native calls are not forcibly terminated.

## Memory and providers

Recent conversation context and long-term saved memory are separate. Saved-memory
embeddings are reused until a record is edited or the embedding model changes. Missing
embeddings are generated in batches. Embedding failures fall back to lexical retrieval.
Deleting a conversation also removes its stored conversation summary.

Opening settings preserves saved model selection. Switching providers uses the selected
provider's own model. Unknown or disabled profiles produce an error rather than switching
to another provider. Cloud speech requires saved consent even if Edge is selected by an
environment variable.

## Voice capture

Settings exposes microphone/output selection and three capture modes: F2 toggle,
hold F2 to talk, or F2 with automatic silence ending. Starting voice input interrupts
the current answer and queued speech. Escape or hiding the window cancels capture.
Recordings stay in RAM, are limited to 60 seconds, and stop after 10 seconds without
detected speech. Missing selected devices produce an error rather than silently
switching to another device.

An adaptive energy gate rejects silence and short clicks and controls silence ending;
Whisper also applies local Silero VAD before transcription. These are speech-detection
guards, not noise cancellation. Sensitivity and silence duration are adjustable.

## Verification on 2026-09-25

- 98 automated tests passed, including multi-turn persistence/context, malformed and
  truncated streams, private-session isolation, cancellation during a stalled request,
  late-worker signals, nonblocking shutdown, literal history search, Markdown rendering,
  embedding reuse/invalidation, missing voice dependencies, short spoken sentences,
  enabling speech after completion, persisted speech preference, playback queue order,
  silence/noise gates, recording limits, disconnected microphones, saved device choices,
  push-to-talk key repetition/release, focus-loss cancellation, and response interruption.
- Ruff checks passed. Test data is isolated from the user's live preferences and database.
- A real private-context stream through LM Studio using `google/gemma-4-e4b` returned
  the synthetic project code `ORION-742` supplied in the previous turn and ended with
  `finish_reason: stop`. No test conversation was saved.
- A real desktop speech check produced a non-silent 3.02-second PCM WAV using Supertonic
  in the application's `.venv` and Qt reported playback completion on Realtek speakers
  without errors. Run `scripts/check_voice.py` in the same environment to repeat it.
- Supertonic generated the synthetic phrase “Merhaba, bu bir sesli konuşma testidir.”;
  the cached local Whisper base model with Silero VAD transcribed it as
  “Merhaba bu bir sesli konuşma testidir.” No microphone was opened and no model
  download was required; generated files were temporary.

## Experimental wake listening — 2026-09-26

The latest full suite passed 135 tests and Ruff checks. The run also reported one Windows
Python 3.14 asyncio pipe-transport cleanup warning; it is not a failed test and remains
to be investigated. MCP stdin writers now explicitly close and await closure, including
already-exited children, but this did not eliminate the suite warning. Wake-specific coverage includes denied consent, separate startup
control, cancellation during capture/inference, stale signals after revocation, pause/
snooze, microphone handoff, playback exclusion, audio erasure, and incomplete offline
model caches. The application's `.venv` successfully loaded the real cached model and
tokenizer after the offline preflight; no microphone was opened for these checks.

Wake permission and startup listening are separately opt-in. Capture uses the chosen
microphone and a four-second ring, with silence-ended phrases and two-second overlap for
long speech. Capture runs independently of model inference instead of reopening the
microphone for each clip. The pipeline retains at most one pending clip and one in-flight
clip (each at most four seconds), in addition to the ring; decoder scratch memory is
separate. Replaced clips are erased, and pending clips older than two seconds are rejected.
Clips and transcripts
stay transient; only a detection boolean leaves the recognizer. No command is extracted
from ambient speech. After detection and microphone release, a fresh ordinary voice
session begins. Cancellation is polled every 50 ms on the device-owning thread, independently
of inference; the microphone closes while an already-running native inference finishes,
and its cancelled result is ignored. Synthetic stream tests verify this handoff.

The recognizer requires a complete cached Whisper base model, including tokenizer.json;
it rejects incomplete caches before Faster Whisper can attempt a tokenizer download.
There is no cloud fallback. Whisper's per-model logger is disabled for ambient inference.
Window/tray state, manual pause, snooze, cooldown, and exclusive microphone ownership
are implemented. A missing tray prevents hidden-window background capture.

`scripts/check_wake_word.py` uses fixed synthetic fixtures, no microphone, offline model
lookup, and temporary WAV files. It now exercises the actual ring-buffer path, including
phrases crossing the old four-second boundary, and follows the selected Turkish/English
language. The latest `--repetitions 3` run detected 4/6 wake phrases and rejected all nine
negatives. The missed positives were decoded as “Hey nex” and “Hey, next”. Synthesis varies between runs;
this is evidence of a quality limitation, not a recognition-rate benchmark. A nonzero
diagnostic exit is intentional when any expected detection is missed. Do not loosen
matching to accept “Hey next”; that would introduce an obvious false trigger.

Capture continues during inference, though slow decoding can cause pending clips to be
dropped intentionally rather than queued without bound. This is not a dedicated low-power
keyword model. Recognition quality,
physical microphones, noisy rooms, and human listening assessment remain open gates.

These checks do not establish microphone quality or compatibility with every runtime.
Registered tools can be called through the permissioned
API; this chat path does not yet implement autonomous model-driven tool execution.
