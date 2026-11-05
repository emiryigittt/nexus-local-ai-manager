<div align="center">

<img src="frontend/assets/nexus-mark.svg" alt="Nexus logo" width="72" height="72">

# Nexus — Local AI Assistant for Windows

### Your local model. One shortcut away.

**A desktop home for the AI models you run yourself.**

Nexus brings **Ollama, LM Studio and llama.cpp** into one Windows assistant — with chat, document search, voice and memory you can inspect and control.

**English** · [Türkçe](README.tr.md)

[![Windows CI](https://github.com/emiryigittt/nexus-local-ai-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/emiryigittt/nexus-local-ai-manager/actions/workflows/ci.yml)

[**⬇ Download for Windows**](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.3) · [▶ Watch the 50-second demo](#watch-nexus-in-50-seconds)

</div>

<p align="center">
<img src="docs/assets/promo/nexus-demo-en.webp" alt="Nexus Windows desktop assistant showing its compact panel and document chat" width="600">
</p>

*Real Nexus interface with synthetic example content and activity; not a recorded model response.*

### Why Nexus?

- **Use your models:** connect to an existing Ollama, LM Studio or llama.cpp server.
- **Ask your documents:** work with PDF, DOCX, Markdown, text and code files.
- **Keep control of memory:** inspect, edit and approve what Nexus remembers.
- **Work your way:** use voice, keyboard shortcuts, prompt actions and conversation history.

Nexus stays close at hand: reveal its compact top-edge panel, pin the mini panel, or press **Alt + Space** to open Chat. Choose your accent, companion and interface sounds in Settings.

**Get started in minutes:** download the Windows installer, launch Nexus, connect a running local model server and select a model. **Python and a terminal are not required.**

[Download the latest beta](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.3) · [Installation guide](docs/WINDOWS_PREVIEW.md) · [User guide](docs/USER_GUIDE.md) · [Privacy](docs/PRIVACY.md) · [Contribute](CONTRIBUTING.md)

<sub>**Current release: 0.3.0 Beta 3.** The installer is unsigned, so Windows may show a publisher warning. Verify the download using the SHA256 file on the release page. Nexus connects to your model server; it does not bundle an LLM. See the privacy and security boundaries below before enabling web or third-party tools.</sub>

## Watch Nexus in 50 seconds

Meet the compact desktop panel, your companion, RGB themes and memory. Choose a language below.

<table>
<tr>
<td align="center"><a href="https://github.com/user-attachments/assets/3bb373f0-6cb6-415b-8d06-8b5dfdbcdb64"><img src="docs/assets/promo/nexus-social-cover-en.webp" alt="Nexus — English · 50s" width="180"></a><br><a href="https://github.com/user-attachments/assets/3bb373f0-6cb6-415b-8d06-8b5dfdbcdb64"><strong>▶ English · 50s</strong></a></td>
<td align="center"><a href="https://github.com/user-attachments/assets/5f4b67f6-b371-467c-84b4-4c32fdb32fe2"><img src="docs/assets/promo/nexus-social-cover-tr.webp" alt="Nexus — Türkçe · 50s" width="180"></a><br><a href="https://github.com/user-attachments/assets/5f4b67f6-b371-467c-84b4-4c32fdb32fe2"><strong>▶ Türkçe · 50s</strong></a></td>
</tr>
</table>

<details>
<summary>Play here — English · 50s</summary>

https://github.com/user-attachments/assets/3bb373f0-6cb6-415b-8d06-8b5dfdbcdb64

</details>

<details>
<summary>Play here — Türkçe · 50s</summary>

https://github.com/user-attachments/assets/5f4b67f6-b371-467c-84b4-4c32fdb32fe2

</details>

*Real Nexus interface with synthetic example content and activity; not a recorded model response. Music and sound effects, no narration.*

Download original videos: [English](https://github.com/emiryigittt/nexus-local-ai-manager/releases/download/v0.3.0-beta.2/nexus-social-film-en-50s-v2.mp4) · [Türkçe](https://github.com/emiryigittt/nexus-local-ai-manager/releases/download/v0.3.0-beta.2/nexus-social-film-tr-50s-v2.mp4)

## What you can do

- **Meet Nexus:** a calm, consistent companion with a clear purpose. An optional
  introduction after setup asks your preferred name, interests, goal and response
  style. Review and save your answers; Nexus can ask occasional relevant questions
  to get to know you. [Identity and introduction guide](docs/IDENTITY.md).
- **Keep your chosen model:** discover LM Studio, Ollama, or llama.cpp servers and
  select a model already available locally.
- **Work from documents:** import PDF, DOCX, text, Markdown, or code and retrieve
  relevant passages. Scanned PDFs require text extraction/OCR elsewhere first.
- **Make memory explicit:** save a preference, inspect its source, review automatically
  proposed memories, and edit or forget them. Automatic candidates require approval.
- **Talk when useful:** local Whisper transcription, optional Supertonic speech,
  Windows speech fallback, or consent-driven Edge cloud speech.
- **Stay at the keyboard:** clipboard/selected-text context, searchable conversation
  history, reusable prompt actions, and streamed answers.
- **Reach outside deliberately:** `/web` supplies web sources; tools have permission
  controls. Their privacy boundaries differ from local chat.

## Get started

### 1. Start your local model

Use an installed [LM Studio](https://lmstudio.ai/), [Ollama](https://ollama.com/),
or [llama.cpp](https://github.com/ggml-org/llama.cpp) server with a loaded model.
Text chat does **not** require a vision model; image analysis does.

| Provider | Default API address Nexus scans |
| --- | --- |
| LM Studio | `http://127.0.0.1:1234/v1` |
| Ollama | `http://127.0.0.1:11434/v1` |
| llama.cpp | `http://127.0.0.1:8080/v1` |

Nexus does not install/start these servers. Hardware requirements depend on your
model. A matching API is necessary; model capabilities still vary.

### 2. Install from source

You need Windows and **64-bit Python 3.11–3.13**. Earlier Windows CI passed on
these versions; the current release is gated on fresh CI. Python 3.14 has known intermittent
native access violations during tests and subprocess-cleanup warnings. A clean-machine
compatibility check is pending. See the [latest local verification](docs/PREPUBLICATION_CHECK.md).

Download **Source code (zip)** from the
[beta release](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.1),
extract it completely, then double-click **Nexus Baslat.bat**. The launcher
prepares dependencies and opens the connection wizard. For manual installation,
open a terminal in the extracted folder and use the commands below.

With Git, you can instead clone the repository:

```powershell
git clone https://github.com/emiryigittt/nexus-local-ai-manager.git
cd nexus-local-ai-manager
```

Then install and start Nexus:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_nexus.py
```

No PowerShell activation-policy change is needed. Alternatively, double-click
`Nexus Baslat.bat` to create the environment, install dependencies, and start Nexus.
Initial dependency/model downloads need internet access.

### 3. Choose a model and try one useful task

In Settings (**Ayarlar → Genel**), scan local providers, select the loaded model,
and save. Try: “Help me plan three focused tasks for today.”

Next, add the [synthetic project brief](docs/demo/project-brief.md) using **Ekle**,
enable **Araçlar → Belgelerimden yanıtla**, and ask: “What are the three release
priorities in this document?” No personal document is needed for this first test.

Optional voice setup: run `Yerel Ses Kur.bat`, then choose a backend under
**Ayarlar → Ses** and enable **Araçlar → Yanıtları seslendir**. Supertonic is a
separate model download with separate license terms; its upstream repository is
archived. See [voice notes](docs/VOICE_AND_MEMORY_RELIABILITY.en.md).

For memory, start with `/remember I prefer concise answers`. Automatic learning
is separately opt-in; candidates appear under **Araçlar → Hafızayı yönet** and
must be activated. Turn on memory use under **Ayarlar → Gizlilik** for retrieval.

## Local by default, not “nothing ever leaves”

With loopback provider addresses, chat inference stays on your computer. Normal
history, imported document text, and memory are stored locally in SQLite, **not
encrypted by Nexus**. Private chat avoids Nexus conversation/memory persistence;
it does not disable logging by another program or permitted network features.

| Feature | Boundary |
| --- | --- |
| Chat / image analysis | Configured model endpoint; keep it local |
| Transcription / local speech | Local inference after model installation |
| `/web` | Search queries and page URLs go to external services with permission |
| Edge speech | Spoken text goes to an online service with speech consent |
| Third-party MCP tools | Separate processes; review their permissions and behavior |

The local API currently has **no authentication**. Keep it on `127.0.0.1`; do not
expose it to a LAN, proxy, or public tunnel. [Privacy and security boundaries](docs/PRIVACY.md).

## Current status

| Area | What is verified / what remains |
| --- | --- |
| Automated checks | 377 tests, Ruff and 13 packaged smoke checks passed locally on 1 October 2026. The source beta publishes only after fresh Windows CI on Python 3.11–3.13 passes. [Verification details](docs/PREPUBLICATION_CHECK.md) |
| Local speech | Two segments completed real Qt playback; naturalness needs listening tests |
| Memory | Candidate persistence/approval tested; current live-model recall check awaits a running server |
| Hey Nexus | Opt-in experiment; missed triggers and CPU use remain. Use `F2` as fallback |
| Compatibility | Windows 10/11 x64 target; automated clean-runner installation, repeated installation and uninstall checks. Physical microphone and model quality need user testing; no macOS/Linux support claim |

Speech uses text segments rather than true PCM streaming. Captions follow playback;
cloud word timings are supplied by the service and local word alignment is approximate.
Speech input now finishes after a configurable pause, balances quiet input and offers
optional transcript review. These changes have not established accuracy with your
physical microphone. Model answers can be wrong. See [verification scope](docs/VOICE_AND_MEMORY_RELIABILITY.en.md)
and [troubleshooting](docs/USER_GUIDE.md#troubleshooting).

## Help shape Nexus

Useful contributions include reproducible bugs with synthetic examples, English UI
localization, keyboard accessibility, and Turkish speech test cases. Start with
[CONTRIBUTING](CONTRIBUTING.md) and the [small-task briefs](docs/GOOD_FIRST_ISSUES.md).
Never attach your database, credentials, private documents, or unredacted logs.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts\check_public_repo.py
```

## License

Nexus-authored source is available under [MIT](LICENSE). The combined Windows
distribution is offered under [GNU GPL v3](DISTRIBUTION_LICENSE.md), with notices
and corresponding source archives. Dependencies, models and voices retain their
own terms. See [third-party notices](THIRD_PARTY_NOTICES.md).

If Nexus helps with your daily work, a star or concrete usage report helps others
discover it. Neither requires sharing personal data.
