# Voice and memory reliability

**English** · [Türkçe](VOICE_AND_MEMORY_RELIABILITY.md) · [Documentation](INDEX.md)

Updated 27 September 2026. The LLM remains the user's chosen local provider.
This report separates implemented changes, measured results and outstanding checks.

## Hey Nexus follow-up — 27 September

- Saving settings no longer overrides a session pause, snooze or error stop. Only a
  new permission grant starts listening; startup remains a separate preference.
- Two-second inference expiry, queued-signal expiry, cancellation and device-release
  checks prevent stale wake handoffs. Invalid confidence values are rejected.
- Wake controls, tray states and actionable model/device/recognition errors support
  EN/TR. Command capture shows “ready” only after the microphone opens successfully.
- `scripts/check_wake_word.py --repetitions 3`, using installed Supertonic and cached
  Whisper base, recognized 6/6 synthetic calls and triggered on 0/9 negative phrases.
  Processing each buffered fixture took 0.49–0.56 seconds. This is not end-to-end wake
  latency: live silence detection, UI scheduling and microphone opening add time.
- These fixed synthetic phrases do not establish real-world accuracy or improvement
  over earlier random synthesis runs. No physical microphone was opened, no ambient
  audio recorded, and no cloud model called. Recognition remains experimental.
- 232 automated tests and Ruff passed. Physical microphone/noise validation remains
  open; the previously intermittent Windows cleanup warning is not declared fixed.

## Implemented in this reliability pass

- Speech synthesis starts while text is arriving. Long text is split into pieces of
  at most 180 characters, favoring sentence, punctuation and word boundaries.
- Without punctuation, completed words can be submitted after at least 50 characters
  and 1.2 seconds. This is not an audio-start guarantee: model/player delay comes on top.
- The local engine preloads while the LLM responds; synthesis of the next segment
  can overlap playback of the previous one.
- A lower caption shows the segment handed to the player; the main response is not
  delayed. This is neither word-timed alignment nor true PCM streaming.
- Voice settings offer 10 Supertonic voices, cloud voice choice, speed and 4/6/8
  generation steps. The default remains 8; faster presets need listening comparison.
- Cloud-speech consent is preserved. These tests did not call cloud speech services.

## Measurements on the development machine

`scripts/benchmark_tts.py` uses temporary settings/data and fixed synthetic Turkish
text with the installed Supertonic 3 int8 model. It generates files without playback.

| Trial | Generation | Audio duration | Generation / duration |
| --- | ---: | ---: | ---: |
| 8 steps, includes initial load | 1.686 s | 4.012 s | 0.420 |
| 8 steps, warm engine | 0.819 s | 4.012 s | 0.204 |
| 4 steps, warm engine | 0.436 s | 4.012 s | 0.109 |
| 4 steps, repeat | 0.435 s | 4.012 s | 0.108 |

In this short sample, 4-step generation was about 47% faster than warm 8-step
generation. This is not a general speed guarantee, an old-version comparison,
quality rating or end-to-end conversational latency. Text, load and hardware matter.

`scripts/check_voice.py` generated two synthetic sentences and completed both
segments on the real Qt/Realtek output with two text notifications and no reported
errors. The first audio file was ready in about 0.997 seconds. This excludes LLM
waiting time and does not prove that a person heard or found the output natural.

## Local voice options researched

The judgments below are inferences from upstream capabilities. Apart from
Supertonic, these models were not installed or measured on this machine.

| Option | Turkish / upstream information | Nexus assessment |
| --- | --- | --- |
| [Supertonic 3](https://github.com/supertone-oss-archive/supertonic) | 31 languages including Turkish, 99M, ONNX. Archived 9 September 2026; support ended. Code MIT, weights separately OpenRAIL-M | Retain the installed lightweight engine and disclose maintenance risk; pin versions/licenses before distribution |
| [Chatterbox Multilingual](https://www.resemble.ai/learn/models/chatterbox-multilingual) | Publisher lists Turkish, expression control, local operation and MIT V3 | Next candidate for Turkish listening comparisons; do not assume low CPU latency. Test an optional isolated runtime; do not conflate Turbo's languages |
| [Pocket TTS](https://github.com/kyutai-labs/pocket-tts) | 100M, CPU-oriented, audio streaming; no Turkish in the official language list | Not the Turkish default; potential optional supported-language backend. Publisher speeds are not Nexus measurements |
| [Qwen3-TTS 0.6B](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base) | Turkish absent from the official ten languages | Not a verified fit for the current Turkish requirement |

First compare existing voices and 4/6/8-step settings on identical Turkish text.
Then record Chatterbox's exact model version, license, download size and hardware
needs before deciding on optional integration. No voice upload or cloning a real
person without consent.

## Memory: saving, approval and use are different stages

1. If automatic extraction is enabled, the local model extracts durable information
   after a normal conversation turn. Private sessions do not schedule this work.
2. Information is stored in SQLite as a **candidate**, not automatically activated.
3. Review under **Araçlar → Hafızayı yönet → Adayı etkinleştir**.
4. With memory use enabled, relevant active entries can be selected for later answers.

The memory dialog shows the latest extraction outcome: candidate count, connection
failure, timeout or invalid output. **Yenile** refreshes it. The status table holds
only the latest job state, count, identifier and time; no conversation, extracted
fact, credential or server error body.

For local servers reporting unsupported JSON schemas, extraction retries once
with a plain JSON instruction. Output is still validated; invalid output is not
silently treated as “no facts”. Automatic-learning permission is rechecked before
writing after an in-flight request. The sensitive-information filter remains, but
cannot guarantee detecting all sensitive information.

Tests cover schema fallback, invalid versus empty output, candidate → approval →
reopen persistence, consent revocation, private sessions and content-free errors.
At this reliability checkpoint, 170 tests and Ruff passed; the known Windows
Python 3.14 closed-pipe cleanup warning recurred and remained open. Live user data
was not changed. `scripts/check_memory.py` failed to connect to the real local model;
rerun with that server running. The reason older sessions were absent is not established.

## Outstanding acceptance checks

- Twenty repetitions per text: cold/warm first playback, gaps, p50/p95 latency,
  CPU/RAM and simultaneous LLM load; report hardware/versions.
- Turkish numbers, abbreviations, technical terms, long answers and interruption/restart.
- Blind user listening comparison: naturalness, intelligibility and character.
- Consented cloud end-to-end tests, real network delay and disconnection.
- Live local extraction and sourced recall of approved memory after an application restart.
- True PCM streaming, word timing and playback-backlog backpressure remain separate,
  unfinished work; do not describe them as shipped.
