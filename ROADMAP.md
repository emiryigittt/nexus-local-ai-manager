# Nexus Product & Development Roadmap

> A Spotlight-style personal assistant for Windows that gives the local AI model
> chosen by the user eyes, ears, memory, and permission-aware desktop abilities.

Nexus is Windows-first and local-first. Language-model requests stay on a user-selected
LM Studio, Ollama, llama.cpp, or compatible local/LAN provider. Web research and cloud
speech are optional hybrid capabilities and must remain visible and consent-driven.
Nexus does not silently fall back to a cloud LLM and does not collect telemetry.

## Release sequence

### v0.3 — dependable core

- [x] First-run setup, durable settings, and provider/model discovery
- [x] Searchable SQLite conversation history and private sessions
- [x] Refined keyboard-first interface with explicit local/cloud state

### v0.4 — reusable actions

- [x] Built-in actions for summarizing, rewriting, translating, and explaining code
- [x] Permission-aware selected-text and clipboard workflows
- [x] Shareable YAML action packs with schema validation

### v0.5 — knowledge and tools

- [x] Fully local document ingestion, semantic embeddings, retrieval, and source citations
- [x] Permissioned tool registry and MCP stdio connections
- [x] Per-tool consent, scoped filesystem access, and a local audit log

### v0.6 — Memory 2.0

- [x] Explicit, editable, opt-in saved-memory API as the initial foundation
- [x] Add typed memories: preference, fact, goal, instruction, and project decision
- [x] Separate global memory, project-only memory, and temporary-chat isolation
- [x] Store provenance for every memory, including its source conversation and message
- [x] Add confidence, importance, recency, last-used, expiry, and pinned metadata
- [x] Add candidate, active, superseded, and disabled states with complete version history
- [x] Extract memory candidates after a conversation using the selected local model and a
  strict JSON schema; never let free-form model output write directly to memory
- [x] Deduplicate similar candidates and resolve contradictions by superseding old facts
  instead of silently keeping conflicting active entries
- [x] Create rolling conversation and project summaries without copying complete chats into
  every prompt
- [x] Retrieve only relevant memories using local embeddings, scope, importance, recency,
  confidence, and usage signals within a fixed context-token budget
- [x] Show which memories influenced an answer and link each item back to its local source
- [x] Build Settings > Personalization > Memory with summary, search, filters, edit, pin,
  disable, forget, export, and delete-all controls
- [x] Support “What do you remember about me?”, “forget this”, and corrections as explicit,
  reviewable operations
- [x] Keep automatic learning off by default; require separate controls for saved memories
  and reference-chat-history behavior
- [x] Never auto-save credentials, secrets, identity documents, or highly sensitive health
  and financial facts; require explicit confirmation for other sensitive categories
- [x] Ensure private sessions neither read nor update memory, summaries, or embeddings
- [x] Add evaluation fixtures for relevance, stale facts, contradictions, over-personalization,
  prompt injection, deletion, and private-session leakage

### Core reliability follow-up — 2026-09-25

Prioritized before new voice features after real-world crash reports.

- [x] Feed bounded recent user/assistant turns to the selected local model
- [x] Persist user messages independently of automatic summaries, in correct turn order
- [x] Keep private conversation context in RAM and reset it on session changes
- [x] Validate streamed output, report interrupted/empty/malformed responses, and filter
  inline reasoning across split tokens; surface response-length limits
- [x] Cancel pending chat network requests without blocking the UI and ignore stale signals
- [x] Retain speech/recording workers until completion; stop queued speech on cancel/new chat
- [x] Preserve provider-specific model selections when opening and saving settings
- [x] Render Markdown through QTextDocument with HTML disabled, without the Qt argument crash
- [x] Reuse saved-memory embeddings and invalidate them after edits; keep lexical fallback
- [x] Enforce saved cloud-speech consent before any Edge synthesis request
- [x] Treat conversation-search input as literal text instead of raw SQLite FTS syntax
- [x] Verify 79 automated tests and a real LM Studio private-context recall smoke test

See [AI reliability notes](docs/AI_RELIABILITY.md) for verification scope and remaining limits.

### Interface redesign — user-prioritized

- [x] Replace the crowded command header with a quiet navigation bar and full-width composer
- [x] Add a visible send button, response copying, clearer typography, and consistent drawn icons
- [x] Group secondary controls in a labelled Tools menu without removing existing capabilities
- [x] Split settings into General, Privacy, and Voice with a persistent Save/Cancel area
- [x] Restore Tab focus navigation; move clipboard inspection to Ctrl+Shift+V
- [x] Bound long provider/status text and only show wake status when permission is enabled
- [x] Verify welcome, response, and settings renders using isolated synthetic data; pass 140 tests
- [x] Refine the desktop visual system with left-aligned welcome typography, descriptive
  keyboard-operable action cards, a send button beside the input and a visible focus ring
- [x] Group General/Privacy settings into cards and separate Voice into Input / Hey Nexus /
  Response voice, preserving unsaved values, provider IDs, permission defaults and cancellation
- [x] Translate voice-setting controls in EN/TR and inspect both languages plus a compact
  640x560 main / 560x600 settings preview; prevent welcome cards clipping on short windows
- [x] Verify 254 tests and Ruff; add card keyboard, focus, compact-layout and unsaved-state tests
- [x] Replace the thin N with a shared two-ribbon vector mark and a livelier #55EF9D
  accent; integrate header, welcome, window icon and paused/listening tray states
- [x] Export transparent/app-tile artwork and a size/color review board; test transparency,
  diagonal-cut visibility, icon resolutions and tray state rendering; verify 262 tests and Ruff
- [ ] Investigate the intermittent native Qt access violation seen once after the new six-test
  UI subset; reruns and full 254-test suite passed after explicit test-window disposal, but
  the root cause is not established and the issue is not declared fixed
- [ ] Get user feedback on the new layout and verify real desktop DPI/keyboard/screen-reader behavior

### v0.7 — natural voice

- [x] Faster Whisper transcription and Supertonic local speech as preferred backends
- [x] Check optional runtime packages as well as model assets before choosing Supertonic;
  fall back to Windows speech in automatic mode if local neural synthesis fails
- [x] Persist the speech toggle, read an existing answer when enabled, retain short sentences,
  and preserve playback order while the next audio file is loading
- [x] Verify local Supertonic generation and Qt playback on the Realtek output;
  pass 85 automated regression tests
- [x] Add microphone/output selection, F2 push-to-talk, silence-ended capture, and
  response interruption; use an adaptive energy gate and local Whisper/Silero VAD
- [x] Bound recording to 60 seconds, cancel on hide/Escape, report device failures,
  and verify 98 automated tests plus synthetic local Turkish speech-to-text
- [ ] Validate physical microphones/headsets and noisy-room behavior; tune sensitivity
  from real recordings with explicit user consent (current checks use synthetic audio)
- [x] Implement an opt-in, experimental local “Hey Nexus” phrase listener that opens the
  assistant and starts a silence-ended session; use cached Whisper with no network fallback
- [x] Keep wake-word listening visibly indicated in the window and system tray; provide
  one-click pause, timed snooze, startup control, microphone selection, and push-to-talk fallback
- [x] Add cooldown, duplicate/stale-trigger suppression, exclusive microphone handoff,
  cancellation, and automatic suspension during assistant responses and playback
- [ ] Add sensitivity calibration and real false-positive/false-negative
  tests for different microphones, background noise, and Turkish/English pronunciation
- [x] Process bounded four-second ambient windows in RAM; never forward their transcripts to
  chat/history/memory/logs or save its audio to disk; release capture on pause/disable
- [x] Keep capture running during inference with a four-second ring and overlapping long-speech
  windows; bound pending audio to one clip, drop stale work, and release the device during cancellation
- [x] Use the selected Turkish/English language for wake decoding and test the real buffering
  path in repeated synthetic diagnostics (earlier run: 4/6 positives, 0/9 false positives)
- [x] Preserve pause/snooze/error-stop choices when saving settings; require a new
  permission grant or explicit resume to restart paused listening
- [x] Reject expired inference/UI signals, cancelled handoffs, missing indicators,
  invalid confidence scores and microphone-release errors
- [x] Explain model/device/recognition errors separately and localize wake controls,
  tray states and permission text in EN/TR
- [x] Show command-recording readiness only after microphone startup; discard late
  readiness events after cancellation and display startup errors instead
- [x] Verify 232 tests and Ruff; offline 2026-09-27 synthetic diagnostic: 6/6 calls,
  0/9 negative triggers, 0.49–0.56 s fixture processing (not end-to-end latency)
- [x] Add offline model validation and explicit, separately confirmed model preparation
  in Voice settings without opening a microphone or granting listening permission
- [x] Show missing/disconnected input devices without claiming OS permission or audio
  quality was tested; keep model setup feedback and controls bilingual
- [x] Run preparation in a cancellable child process; stop on settings dismissal and
  five-minute timeout, explain retained partial cache files, and sanitize status output
- [x] Verify 248 tests and Ruff, inspect EN/TR previews and load the existing cached
  model through both the CLI and settings-panel process without network or microphone
- [ ] Validate a fresh, user-approved model download on a clean machine, including
  interrupted-download recovery and Windows microphone permission behavior
- [ ] Improve phrase recognition before promoting wake listening out of experimental status;
  earlier synthetic positives failed; latest narrow results do not establish real-world
  accuracy, and physical microphone/noise validation is pending
- [x] Add automated wake lifecycle/privacy tests and a reproducible offline synthetic
  diagnostic; keep the recognition-quality gate open when the diagnostic fails
- [x] Verify 122 automated tests, Ruff checks, and real cached-only model/tokenizer loading
- [x] Verify 135 automated tests and Ruff after continuous-capture and language changes
- [x] Close and await MCP stdin writers even when child processes have already exited
- [ ] Investigate the Windows Python 3.14 asyncio pipe-transport cleanup warning in the full suite
- [ ] Clearly labelled, consent-driven cloud speech fallback

### Voice latency and memory reliability — current user priority

- [x] Bound spoken text chunks and flush long punctuation-free streams before completion
- [x] Preload local synthesis during response generation; show the queued playback segment
- [x] Add persistent voice, speed, and local generation-quality controls; preserve cloud consent
- [x] Distinguish invalid memory output from an empty result and support a single validated
  fallback for local servers rejecting structured output
- [x] Persist content-free memory job status; expose failures and pending approval in the UI
- [x] Verify candidate persistence, approval, consent revocation and private-session guards
- [x] Pass 170 automated tests and Ruff; retain the intermittent Windows asyncio cleanup
  warning as an open issue rather than treating it as resolved
- [x] Measure installed local synthesis and verify two generated chunks complete real Qt playback
- [x] Research current Turkish/local speech alternatives and record upstream maintenance risks
- [x] Prepare a gated GitHub/community launch plan without publishing externally
- [ ] Verify extraction and cross-session recall against the user's running local model
  (latest synthetic live check: connection unavailable)
- [ ] Compare Turkish voices/quality presets with user listening feedback
- [ ] Measure end-to-end local/cloud p50/p95 latency and gaps under simultaneous LLM load
- [ ] Evaluate optional Chatterbox Multilingual integration after hardware/license/quality checks
- [ ] Add true audio streaming, word-timed highlighting, and bounded playback backlog

See [voice/memory verification and research](docs/VOICE_AND_MEMORY_RELIABILITY.md) and
[GitHub launch plan](docs/GITHUB_LAUNCH_PLAN.md). Windows packaging remains deferred.

### v0.8 — optional embedded runtime

- [ ] Optional llama.cpp sidecar and managed GGUF downloads
- [ ] Hardware-aware recommendations, checksums, licenses, and disk management
- [ ] Keep LM Studio, Ollama, llama.cpp servers, and custom local providers first-class

### v0.9 — Windows packaging

- [ ] Python-free Windows installer after the feature set and dependencies stabilize
- [ ] Clean install, upgrade, uninstall, checksum, and optional signing workflows
- [ ] Tagged GitHub release automation and user-initiated update checks

### v1.0 — public launch

- [x] English/Turkish README, source quick start, privacy matrix and troubleshooting guide
- [x] Synthetic demo fixture, recording storyboard and scoped first-contribution briefs
- [x] Git-visible file/link/credential-pattern preflight, tests and CI integration
- [x] First-time GitHub setup guide; keep publication and account creation separate from preparation
- [x] Initial third-party notices and accurate preview/verification limitations
- [x] Verify 187 local tests, Ruff, four YAML files and preflight over 123 Git-visible files
- [x] Maintain 13 English/Turkish public-document pairs with a bilingual documentation index
- [x] Route each README to its language's guides; translate contribution, privacy,
  security, conduct, third-party, demo, setup and launch materials
- [x] Prepare equivalent English/Turkish announcement and pilot-invitation drafts without posting
- [x] Make issue/PR templates bilingual and test reciprocal language navigation in publication preflight
- [x] Verify bilingual preparation with 194 tests, Ruff, YAML parsing and 138-file preflight;
  retain the known intermittent Windows asyncio cleanup warning as open
- [x] Finish the 2026-09-27 publication check: preserve/exclude personal PDF/photo outputs,
  reject links to unpublished files, and pass 199 tests, Ruff and 138-file preflight
- [x] Implement the first UI localization phase: saved EN/TR preference, main-window
  controls/accessibility, General/Privacy settings and basic chat connection statuses
- [x] Apply language without rebuilding the window or losing drafts, conversations,
  images or session modes; test persistence, cancellation and deleted-widget bindings
- [x] Render and inspect synthetic EN/TR main/settings previews; pass 206 tests twice,
  Ruff and the 154-file publication preflight (2026-09-27)
  - The first full run hit a native Qt access violation; an unchanged verbose rerun
    passed 205 tests. Added a session-owned test QApplication and weak widget bindings;
    two subsequent 206-test runs passed. This is not proof that every native crash is fixed.
  - The known Windows asyncio closed-pipe cleanup warning remains open.
- [ ] Finish voice/history/memory dialogs, tray, remaining statuses/errors and consent
  prompts in both languages; do not translate user content or model output
- [ ] Complete English application UI localization and matching real demo recordings;
  the scoped UI pilot and translated documentation do not close this product task
- [ ] Record and review the real demo; complete clean-machine compatibility testing
- [ ] Resolve dependency/model distribution licensing and configure private reporting channels
- [ ] Harden unauthenticated local gateway and validate configured provider trust boundaries
- [ ] Reproducible benchmarks, signed builds when a certificate is available
- [ ] Healthy community profile, Discussions, good-first-issues, and release notes

## Product rules

These are target constraints, not a security certification. In particular, the
current gateway does not yet implement the session credential required by rule 5;
keep it on loopback. See [current trust boundaries](docs/PRIVACY.md).

1. The selected language model is local; remote web and speech helpers never change it.
2. Sensitive operations are previewed and require scoped permission.
3. Private sessions write no conversation, attachment, or memory data.
4. Users can inspect, export, and delete every durable piece of personal data.
5. The local API binds to loopback and mutation endpoints require a session credential.
6. Each release phase ships only after unit, integration, UI, and Windows package checks.
7. Always-listening voice features are opt-in, locally processed, visibly indicated, and can be
   stopped immediately without retaining ambient audio.

## Acceptance gates

- A new user can install Nexus without Python, discover a provider, select a model, and
  send a first message without editing `.env`.
- Conversations survive restarts and are searchable; private sessions do not survive.
- No cloud request is made without informed consent and a visible cloud indicator.
- Community actions and tools cannot exceed their declared permissions.
- Removing a conversation, memory, model, or indexed document removes its local data.
- Memory retrieval must prefer relevant, current, in-scope facts and expose the source of
  every injected memory; disabling or deleting a memory must prevent its future use.
