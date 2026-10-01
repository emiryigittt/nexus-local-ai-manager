# Windows installer and source build

**English** · [Türkçe](WINDOWS_PREVIEW.tr.md) · [Documentation](INDEX.md)

Nexus Beta 2 provides a Windows x64 installer under the
[GPL distribution terms](../DISTRIBUTION_LICENSE.md). It is unsigned and remains a beta.
Download the installer and corresponding sources from the
[release page](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.2).

## For users

1. Open the release `NexusSetup.exe` and install for your Windows account.
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

Use a clean Windows x64 **Python 3.12.10** environment and the exact
[build lock](../packaging/windows-build.lock.txt). Install the official Inno Setup 6
compiler separately. From the repository root:

```powershell
python -m pip install -r packaging/windows-build.lock.txt
python -m scripts.prepare_distribution
python -m scripts.build_windows --compiler "C:\path\to\Inno Setup 6\ISCC.exe"
python -m scripts.check_windows_package --installer dist/installer/NexusSetup.exe
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

## Sources, notices and limits

The release publishes `Nexus-source.zip`, `Nexus-dependency-sources.zip`,
`dependency-sources.json`, `windows-package-check.json`, `release-manifest.json`
and `SHA256SUMS.txt` alongside the installer. The source catalog records exact
upstream archive hashes. The dependency archive includes original Python sources,
Qt modules, FFmpeg and codecs, PyAV build recipes, and matching MSYS2 runtime sources
with patches and packaging recipes. Nothing is encrypted or locked to a signing key.

To modify the app, extract its source, install the pinned build environment, edit
and run the build steps above. Original upstream source archives retain their build
files. Qt modules use their bundled CMake/configure instructions; PyQt uses the SIP
build instructions in its source archive. For native PyAV libraries, the archived
`pyav-ffmpeg-build` contains build scripts, patches and configuration. MSYS2 source
packages contain PKGBUILD recipes, patches and original GCC/libiconv/winpthreads sources.
Use the media configuration recorded in `dependency-sources.json` when rebuilding.
Prebuilt compatible DLLs can be replaced in `_internal` without authorization keys.

The frozen inventory is generated from files actually present in the desktop bundle;
`build-environment.json` is a separate build inventory, not a certified SBOM.
Publishing requires successful unit checks and isolated installation, repeated
installation and uninstall checks. Microphone hardware, real model quality, cancelled
interactive installation and all Windows configurations are not covered by these
automated checks. Wake detection remains experimental; F2 is the reliable manual path.
Cloud speech and external tools retain their explicit consent/permission controls.
