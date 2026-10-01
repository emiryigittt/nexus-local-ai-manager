# Changelog

All notable changes to Nexus are documented here. The project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.0-beta.1] - 2026-10-01

First public source beta. Windows installer distribution remains pending the
PyQt/Qt licensing decision and dependency distribution review.

### Added

- Compact top-edge strip with hover tools, expandable chat, preserved drafts,
  RGB accents, optional rainbow motion, bot/cat companions and original interface sounds.
- Card-based memory review and an optional first-run introduction with an explicit
  review/save step for personal preferences. Nexus has a defined assistant identity;
  it does not claim consciousness or invent personal knowledge.
- Three-step connection wizard and a source launcher that prepares dependencies.
  A reproducible, unsigned installer is available locally for development checks.
- Speech-end detection using local Silero, bounded input amplification, default
  automatic finish after a configurable pause, optional transcript review, and
  separately prepared balanced/stronger offline transcription profiles.
- Playback-following captions; cloud speech uses supplied word timings, while
  local speech uses approximate alignment. This is not true PCM streaming.
- Original 50-second, 1080×1920, 60 fps Turkish/English promo preparation tools.
  The films show fictional sample content rather than live inference.

### Reliability updates

- Batch streamed UI updates, start speech from smaller completed text pieces,
  bound optional memory lookups, and cancel background memory work before foreground replies.
- Accept common Turkish wake-phrase transcriptions and reject stale detections.
  Hey Nexus remains experimental; F2 is the reliable manual fallback.
- Keep model preparation outside microphone capture and erase captured audio
  buffers on completion, cancellation and error.

### Earlier work included in this beta

- Shared two-ribbon Nexus vector logo, livelier emerald accents, multi-resolution
  window icon and clearly distinct paused/listening tray variants. Added transparent
  artwork, app-tile exports, a brand board and rendering regression tests.
- Refined graphite/mint desktop: left-aligned welcome, descriptive keyboard action
  cards, send beside the input, a composer focus ring and a compact-height layout.
- Card-based General/Privacy settings and Input / Hey Nexus / Response voice sections
  with EN/TR voice controls. Switching sections preserves unsaved choices; permissions
  and backend values remain unchanged. Updated isolated previews and UI regression tests.
- Offline Whisper validation and separately confirmed model download from Voice
  settings, without opening the microphone or changing listening/LLM preferences.
  Preparation is cancellable, stops on settings dismissal, has a five-minute timeout,
  and reports content-free EN/TR status; partial downloads may remain in the cache.
- Missing/disconnected microphone guidance that does not claim Windows permission
  or real audio capture has been tested.
- Safer Hey Nexus lifecycle: preserve paused/snoozed/error-stop sessions on settings
  save, expire slow/queued detections, reject invalid scores and failed microphone
  release, and invalidate stopped handoffs. Wake/tray guidance supports EN/TR.
- Command recording now displays readiness only after microphone startup succeeds;
  cancelled readiness events are ignored and startup failures replace the waiting screen.
- English/Turkish main-window controls, accessible names, General/Privacy settings
  and basic chat connection statuses; apply saved language without rebuilding the
  window or discarding conversations, drafts, images or session modes. Voice,
  history, memory dialogs and remaining statuses are not fully localized yet.
- Localization regression tests and isolated bilingual UI previews.
- Non-owning translation bindings that skip deleted Qt widgets, and one shared
  test QApplication to avoid repeated application teardown between UI tests.
- Thirteen paired English/Turkish public documents, a language index, bilingual
  issue/PR templates, and unposted launch/pilot copy in both languages.
- Translation-manifest checks for paired files and reciprocal language links;
  this checks navigation, not semantic translation accuracy or full UI localization.
- English/Turkish repository introduction, synthetic document demo, user/privacy guides,
  contribution briefs, and a first-time GitHub setup checklist.
- Read-only publication preflight for Git-visible runtime files, common credential patterns,
  large files and local Markdown links; regression tests and CI integration.
- Third-party licensing notes distinguishing Nexus source from PyQt/Qt and model terms;
  explicit unauthenticated-gateway and unfinished publication-channel disclosures.
- Voice character, speed and local quality presets; playback-segment captions and
  isolated local synthesis/memory diagnostic scripts.
- Content-free last memory-job status, actionable extraction errors, and a direct
  Tools entry for reviewing candidates before activation.
- Current voice-provider research and a gated community launch plan under `docs/`.
- Redesigned desktop window: graphite surfaces, mint accents, a full-width composer,
  visible send action, readable responses, copy action, and font-independent line icons.
- General/Privacy/Voice settings tabs and a compact Tools menu for conversation modes.
- Isolated UI preview renderer and interaction tests for focus, sending, copying, settings,
  and long status labels. Tab now navigates controls; clipboard inspection is Ctrl+Shift+V.
- Durable product roadmap for the Windows-first, local-first assistant.
- Foundation for local settings, provider discovery, and SQLite conversations.
- Permission-aware clipboard and selected-text workflows with explicit privacy state.
- Local document ingestion with provider-hosted embeddings, semantic retrieval, and FTS fallback.
- MCP stdio discovery with a namespaced tool registry, explicit consent, filesystem scopes,
  and redacted local audit logs.
- Memory 2.0 foundations: typed and scoped records, provenance, ranking metadata, lifecycle
  states, version history, and opt-in local-model candidate extraction.
- Memory deduplication and conflict replacement, rolling conversation/project summaries,
  semantic budgeted retrieval, and visible source attribution.
- Complete local Memory 2.0 management UI, explicit correction/forget flows, sensitive-data
  and prompt-injection guards, private-session isolation, and behavioral evaluation fixtures.
- Verified lazy local Faster Whisper transcription and automatic Supertonic-first speech.
- Voice settings with microphone/output selection, F2 toggle, hold-to-talk, and
  silence-ended capture; configurable silence duration and sensitivity.
- Adaptive capture energy gate and local Silero VAD before Whisper transcription,
  bounded in-memory recording, and interruption of the current response on voice input.
- Planned an opt-in, local-only “Hey Nexus” wake-word mode with visible microphone state,
  ephemeral audio buffering, calibration, snooze, and false-trigger protections.
- Experimental cached-Whisper “Hey Nexus” listener, off by default with separate startup
  consent, window/tray status, pause/resume, 15-minute snooze, and F2 microphone handoff.
- Ambient capture stays in bounded RAM-only clips; no ambient transcript reaches chat,
  history, memory, or logs. Missing tokenizer/model files fail closed without downloading.
- Wake lifecycle/privacy tests and `scripts/check_wake_word.py` for synthetic offline
  recognition checks. Recognition remains experimental: positive cases can be missed,
  and physical microphone/noise calibration remains pending.

### Fixed

- Exclude personal document-generation outputs without deleting them; detect those
  paths even if force-added, and reject documentation links to unpublished files.
- Split long streaming speech into bounded text pieces and flush waiting text without
  dropping the unfinished word; preload local synthesis while the LLM prepares its response.
- Validate automatic memory output strictly, retry once when a local server rejects JSON
  schemas, and recheck automatic-learning consent before saving extracted candidates.
- Removed periodic wake-capture restarts and inference-time capture gaps with a bounded
  ring buffer, overlapping long-speech windows, and a latest-only inference queue.
- Release the microphone on cancellation independently of native inference; erase pending
  clips and reject stale work. Wake decoding now follows the selected Turkish/English language.
- Extended synthetic wake diagnostics to exercise live buffering and repeat fixtures;
  recognition quality remains experimental rather than loosening phrase matching.
- Close and await MCP subprocess stdin writers, including after an already-exited child.
  A separate Windows asyncio cleanup warning still occurs in the full test suite.
- Cancel voice capture on Escape/window hide, ignore repeated push-to-talk key presses,
  and surface capture/device failures without silently changing the selected device.
- Fixed silent responses when Supertonic assets exist but optional runtime packages are absent.
  Automatic mode checks both and can fall back to local Windows speech.
- Persist the response-speech toggle, read the current answer when speech is enabled after
  completion, and retain short sentences such as greetings in the speech queue.
- Preserve audio that is still loading, release completed audio before deletion, and show
  playback errors. Initialize Windows COM for speech workers and serialize native synthesis.
- Added `scripts/check_voice.py` to verify synthetic local speech and real Qt playback
  using temporary preferences, without changing user history/settings.
- Restored multi-turn model context and user-message persistence independently of summary settings.
- Added bounded, RAM-only private-session context and reset conversation state at privacy boundaries.
- Validate provider streams, reject premature EOF and reasoning-only output, filter split `<think>`
  blocks, and warn when an answer reaches the generation limit.
- Cancel chat HTTP requests asynchronously and ignore cancelled workers' late UI signals.
- Keep active workers alive until they finish, including when speech is disabled or a new chat starts;
  shutdown waits without blocking Qt's event loop.
- Preserve model selections in settings and reject missing or disabled provider profiles.
- Reuse memory embeddings until edits or model changes invalidate them; retain lexical fallback.
- Remove stored conversation summaries when their parent conversation is deleted.
- Require saved cloud-speech consent before Edge synthesis and release microphone buffers after use.
- Fixed Markdown rendering through `QTextDocument.setMarkdown()` with HTML disabled.
- Escape conversation search input so punctuation and incomplete quotes cannot trigger an FTS error.
- Routed voice-capture failures to the visible UI instead of leaving a failed worker silent.

## [0.2.0]

### Added

- Spotlight-inspired PyQt interface and global keyboard shortcut.
- Streaming local-model responses, image understanding, clipboard analysis, and research.
- Faster Whisper transcription with local and optional cloud speech backends.
