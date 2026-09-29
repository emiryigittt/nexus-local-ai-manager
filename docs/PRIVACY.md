# Privacy and trust boundaries

**English** · [Türkçe](PRIVACY.tr.md) · [Documentation](INDEX.md)

This describes the current source, not a security certification.

## Data and network map

| Operation | Data involved | Storage / recipient |
| --- | --- | --- |
| Normal chat | Prompt, selected context, generated response | Selected model endpoint; Nexus history in local SQLite |
| Image analysis | Attached/clipboard image | Selected model endpoint; requires vision support |
| Document import | Extracted text and chunks; optional embeddings | Local SQLite; configured model server for embedding requests |
| Memory | Explicit facts, candidates, approved records, summaries | Local SQLite; selected model for extraction/summary/retrieval operations |
| Private chat | In-memory recent conversation | No Nexus conversation/memory persistence; provider can still log requests |
| F2 transcription | Microphone audio and transcript | Local Whisper inference; initial model download may use the network |
| Local response speech | Response text and generated audio | Local engine; temporary audio files used for playback and removed on normal cleanup |
| Edge response speech | Text being spoken | Microsoft online speech service after cloud consent |
| Web research | Query, search results, page URLs/excerpts | `ddgs` search service(s) and Jina Reader; excerpts then go to selected model |
| Experimental wake listening | Short ambient clips | Bounded RAM buffers, cached local Whisper; not saved or sent to chat/cloud |
| Wake model preparation | Model-file requests only | Check is offline; Set up model requests separate approval for a Hugging Face download; no microphone or conversation data |
| MCP tools | Approved tool arguments, results, subprocess activity | Third-party local process; may have its own network/storage behavior |

## Local does not mean encrypted or sandboxed

The default data directory is `%LOCALAPPDATA%\Nexus`; `NEXUS_DATA_DIR` can override
it. It contains settings, `nexus.db` and configured tool information. SQLite also
contains permissions/audit information. Nexus does not encrypt these files. Protect
the Windows account and backups. Optional Supertonic assets live in the project's
`models/`; Whisper uses its model cache. Python package/model installation is online.

Voice settings can validate Whisper without opening a microphone. Model setup does
not change listening/cloud permissions or your selected LLM. Stopping setup or
closing settings terminates its process, but cached/partial downloads can remain;
cancelling settings does not undo a separately approved model download.

Keep providers on loopback addresses. A saved “local” label is not a network firewall;
a custom remote URL changes who receives context. CORS is not authentication.
The current gateway is unauthenticated and should never be exposed to a LAN/public
tunnel or shared as a multi-user service. Other local processes can access it.

Tool approval and file scopes are application checks, not an operating-system sandbox
around an MCP program. Run only tools you trust. Redaction is not a guarantee that
every sensitive value is removed from a log. Private sessions do not sandbox tools,
disable authorized web/cloud speech, encrypt memory, or erase provider logs. Temporary
speech files may remain after a crash; private mode is not a zero-forensic-trace guarantee.

## User controls

- Clipboard use has ask/allow/deny preferences; avoid granting broad access unnecessarily.
- Web and cloud speech each require permission; turn them off for offline-only work.
- Memory use, candidate extraction, and history reference are independent settings.
- Review automatic candidates before activation; edit/delete records in the memory manager.
- Delete conversations/documents through their controls. Do not assume deleting a
  conversation also erases facts already approved separately as personal memory.
- Pause background listening in the window/tray, or quit Nexus. Hiding is not quitting.

Never publish databases, `.env`, MCP configuration, memory exports, recordings, or raw
support logs. Use the [synthetic demo brief](demo/project-brief.md) for reports.
Report vulnerabilities via [SECURITY](../SECURITY.md).
