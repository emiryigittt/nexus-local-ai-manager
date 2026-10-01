# Windows installer preview

**English** · [Türkçe](WINDOWS_PREVIEW.tr.md) · [Documentation](INDEX.md)

Nexus now has a reproducible Windows installer build and a three-step first-run
wizard. This is a local development preview, not a published or signed release.

## For users

1. Open the locally supplied `NexusSetup.exe` and install for your Windows account.
   Python and a terminal are not needed. Windows 10/11 x64 is the current target.
2. Open Nexus from the Start menu. Select Turkish or English.
3. Start LM Studio, Ollama or llama.cpp and load/download a model in that application.
   Nexus finds loopback servers automatically. If none is available, follow the
   on-screen instructions and use **Scan again**.
4. Select a model, click **Test connection**, then **Open Nexus** after a real reply.
   You can use **Later** without changing saved preferences and reopen
   **Connection setup** on the welcome screen.
5. Click **Try a sample document**, then send the prepared question. The fictional
   brief is added to the local document library; it is not an automatically generated answer.

Optional speech is under **Settings → Voice**. Whisper preparation is available in
the **Hey Nexus** tab; this also prepares normal speech transcription. Supertonic
preparation and download progress are under **Response voice**. Downloads require
an explicit action and confirmation, and do not enable listening or cloud speech.
Checks load a model offline; they do not test the physical microphone or speaker.
Stopping a preparation or closing settings stops its child process. Partial downloads
can remain in the model cache. Windows speech works without downloading Supertonic.

Data is stored under `%LOCALAPPDATA%\Nexus` (or `NEXUS_DATA_DIR`), separately from the
installation. Uninstall preserves conversations, settings and downloaded models.
Delete that data only if you deliberately want to reset Nexus. The installer does not
bundle an LLM, Whisper weights or Supertonic weights, or install a model server.

## Build and verification

Use a clean Windows Python 3.11–3.13 environment. Install `requirements-dev.txt`,
`requirements-tts.txt` and `pyinstaller>=6.22,<7`. Install the official Inno Setup 6
compiler separately. From the repository root:

```powershell
python -m scripts.build_windows --compiler "C:\path\to\Inno Setup 6\ISCC.exe"
```

The build produces `dist/Nexus/Nexus.exe`, `dist/installer/NexusSetup.exe` and a
SHA-256 manifest beside the installer. The desktop build uses a folder of bundled
libraries; copying only `Nexus.exe` is insufficient. The installer contains that folder.
User configuration, databases, recordings, `.env` and model directories are excluded.
Build dependencies and tools are kept outside the distributed application.

For an isolated packaged smoke test, set `NEXUS_DATA_DIR` to a disposable test directory
and `QT_QPA_PLATFORM=offscreen`, then run `Nexus.exe --self-test report.json`.
The report checks API imports, the three wizard pages, brand assets and sample brief.
It does not verify model answer quality, audio hardware or every packaged workflow.

`python -m scripts.check_windows_package --installer dist/installer/NexusSetup.exe`
performs isolated desktop, local API, synthetic model connection, document ingestion,
installation and uninstall checks. It keeps real user data out of the test and refuses
to run the installer test if Nexus is already registered as installed. The JSON report
in `build/windows-package-check.json` includes the tested installer hash. The model
server in this check is a deterministic fixture; use a real LLM for quality testing.

## Before public distribution

- Complete the [PyQt/Qt and dependency distribution review](../THIRD_PARTY_NOTICES.md).
  The build includes Nexus source, available dependency license files and an exact
  build-environment inventory; that inventory is not a final audited SBOM.
- Test install, upgrade, cancellation and uninstall on a clean Windows machine.
- Test real LM Studio/Ollama inference and optional model download, transcription and speech.
- Review every native dependency and model separately. No model redistribution is implied.
- Sign the installer or clearly document its unsigned status and provide independently
  verifiable checksums. Do not claim it is an official signed release.

The author-owned source remains MIT. The bundled dependency combination must not be
described as MIT-only. This local build does not resolve the public release gates.
