# Nexus user guide

**English** · [Türkçe](USER_GUIDE.tr.md) · [Documentation](INDEX.md)

For installation: [English](../README.md#get-started) · [Türkçe](../README.tr.md#başlangıç).
Turkish labels below also help locate controls in the untranslated dialogs. Normal app settings are preferred
over environment overrides. This guide describes a development preview.

## Interface language

Open settings with `Ctrl + ,`, then **General → Language → English → Save**.
From Turkish, use **Genel → Dil → English → Kaydet**. The main window updates
without restarting or clearing your conversation, draft or attached image. General
and Privacy settings use the saved language the next time you open them. Cancel
discards unsaved changes, including permissions. Model answers and your text are
not translated by this UI setting. Voice, history, memory dialogs and some
status/error messages are not fully translated yet.

## Everyday controls

| Action | Shortcut / control |
| --- | --- |
| Show / hide | `Alt + Space` |
| Send | `Enter` or send button |
| Navigate controls | `Tab` / `Shift + Tab` |
| Clipboard context | `Ctrl + Shift + V` or `/clip [instruction]` |
| Selected text from another app | `Ctrl + Shift + Space` |
| Start / finish voice input | `F2` while Nexus has focus |
| New conversation / history | `Ctrl + N` / `Ctrl + H` |
| Browse prompt history | `↑` / `↓` in the prompt field |
| Cancel current work / hide when idle | `Esc` |
| Quit | `Ctrl + Q` |
| Web research | `/web <question>` |
| Explicit memory | `/remember <fact>` or `/hatırla <bilgi>` |
| Show memory / correct a source | `/memory` / `/correct <source number or id>` |
| Prompt actions | `/summarize`, `/rewrite`, `/translate`, `/fix`, `/explain` |

The composer contains **Attach** (Ekle), **Research** (Araştır), and
**Tools** (Araçlar). Tools includes private session, document-grounded answers,
response speech, and memory management. The response header has a copy button.

## Documents and memory

Use **Ekle** to import readable text, then enable **Belgelerimden yanıtla**.
PDF extraction uses embedded text, not OCR; DOCX extraction currently reads paragraphs,
not every table or embedded object. A text-only model can summarize extracted text.
To understand an attached image, choose a model with image capability.

Memory has separate controls under **Ayarlar → Gizlilik**:

1. Use saved memory in future answers.
2. Extract candidate memories automatically from normal conversations.
3. Reference conversation/project summaries in future answers.

Candidates are not automatically active. Open **Araçlar → Hafızayı yönet**, review
the content, then choose **Adayı etkinleştir**. Check the last-job status and use
**Yenile** for an extraction still in progress. A conversation can produce no durable
facts; that is different from a reported extraction error. Model output is not
guaranteed to be accurate. Review sensitive information before approving it.

## Voice

Under **Settings → Voice** (Ayarlar → Ses), use **Input** for the microphone and
F2 mode, **Hey Nexus** for wake permission/model preparation, and **Response voice**
for the speaker and speech engine. Switching these sections preserves unsaved choices;
Save applies them and Cancel discards them. Input modes include toggle,
hold-to-talk, or silence-ended capture. Normal capture is bounded to 60 seconds;
silence detection depends on the microphone and room. F2 requires window focus.
Starting a new recording interrupts the answer and its speech.

For output, automatic mode prefers installed Supertonic with its runtime packages;
otherwise it uses Windows speech. Explicit Supertonic selection reports an error
instead of silently selecting cloud speech. Edge requires separate cloud consent.
Choose a voice, speed, and local 4/6/8-step quality preset; fewer steps can reduce
generation time at a possible quality cost. Captions show the playback segment,
not word-level timing. [Measured results and caveats](VOICE_AND_MEMORY_RELIABILITY.en.md).

**Hey Nexus is experimental and off by default.** Background listening and starting
it with Nexus have separate settings. It uses cached local Whisper, never downloads
weights automatically, and keeps short ambient clips in RAM. The window/tray shows
its state; pause or snooze it there. Hiding Nexus does not stop explicitly enabled
background listening while its tray indicator is available. Quit to stop Nexus.
Use F2 if wake recognition is unreliable. No physical microphone accuracy claim is made.

To enable it, open **Settings → Voice**, select your microphone under **Input**,
then open **Hey Nexus** and use **Check model**.
The check loads cached Whisper base offline, without opening the microphone. If the
model is missing, choose **Set up model…** and approve the separate Hugging Face
download. This does not grant listening permission, change your LLM, or send audio.
The device status shows a missing/disconnected microphone without opening it; it
does not verify Windows permission or recording quality. Then grant **Allow
Hey Nexus listening** and save. Wake listening itself never downloads models.
Say **Hey Nexus** on its own,
pause, then wait for **You can start speaking now** before giving your command.
That indication appears only after the command microphone has opened successfully.
Saying the wake phrase and command in one breath is not supported.

Saving settings preserves an existing pause or snooze; use the window/tray resume
control to listen again. Slow recognition results (over two seconds of inference)
and expired UI notifications are discarded, not acted on later. If this frequently
happens on your CPU, use F2. Model-not-ready, microphone and recognition failures
have separate messages; failures do not start an automatic retry loop.

Use **Stop task** to cancel model preparation. Closing settings also stops the
preparation process; there is a five-minute timeout. Downloaded or partial files
can remain in the model cache even if you cancel settings. **Cancel** discards
unsaved settings, not an explicitly approved download. No recording is made by
model preparation. First-time F2 input remains an alternative model setup path.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Provider unavailable | Start the local server, load its model, scan again in General; confirm the selected model identifier |
| Model ignores images | Select a vision-capable model; text capability alone is insufficient |
| No speech | Enable Tools → response speech; check selected output device, backend installation, and cloud permission if using Edge |
| Speech starts late | Try local 4-step mode and a short response; separate LLM delay from synthesis time. See the voice report |
| No automatic memory | Enable candidate extraction, exit private mode, inspect last-job status, then approve candidates and enable memory use |
| Empty document content | Check PDF text selection or export a plain-text copy; scanned pages are not OCR'd |
| Microphone/wake problems | Reconnect or reselect device; tune threshold; test focused F2 before experimental wake mode |
| Port 8000 is in use | Stop the old Nexus instance or choose another `NEXUS_BACKEND_PORT`; do not kill unrelated applications |
| Windows asyncio cleanup warning | Known intermittent Python 3.14 issue; record version and synthetic reproduction, do not post private logs |

Do not delete the data directory to troubleshoot. Back up local data privately first.

## Diagnostics for contributors

Run from the project folder with the application environment:

```powershell
.\.venv\Scripts\python.exe scripts\check_voice.py
.\.venv\Scripts\python.exe scripts\benchmark_tts.py
.\.venv\Scripts\python.exe scripts\check_memory.py
```

The first command **plays a synthetic voice sample**. The benchmark writes temporary
synthetic audio without playback. The memory check sends a synthetic preference to
the selected local model and uses a temporary database. None opens the microphone.
Optional local speech packages/model are required for the voice diagnostics; the
memory check requires a running local model. Exit success is not a listening-quality
or full live-conversation certification.

## Advanced configuration

Copy [.env.example](../.env.example) to `.env` only if developer overrides are needed.
Do not publish `.env`. Saved preferences normally live under `%LOCALAPPDATA%\Nexus`;
`NEXUS_DATA_DIR` changes that location. [Data boundaries](PRIVACY.md).

Important overrides include `NEXUS_API_BASE_URL`, `NEXUS_API_KEY`, `NEXUS_MODEL`,
`NEXUS_BACKEND_PORT`, `NEXUS_TTS_ENABLED`, `NEXUS_TTS_BACKEND`, and
`NEXUS_SUPERTONIC_SPEED` / `SPEAKER` / `STEPS` (the latter two also use the full
`NEXUS_SUPERTONIC_` prefix). Voice environment settings override the saved controls.
The example file contains explicit example values, not a promise that the named
model is installed. Keep model and gateway addresses local.
