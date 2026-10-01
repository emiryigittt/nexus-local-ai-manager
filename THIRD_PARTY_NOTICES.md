# Third-party software and model notices

**English** · [Türkçe](THIRD_PARTY_NOTICES.tr.md) · [Documentation](docs/INDEX.md)

The combined Windows Beta 2 distribution uses [GNU GPL version 3](DISTRIBUTION_LICENSE.md).
Nexus-authored source retains [MIT](LICENSE). Third-party copyright and license
notices are preserved; dependencies and separately downloaded models are not relicensed.

## Distribution inputs

The [pinned Windows build](packaging/windows-build.lock.txt) records exact Python
package versions. The [source catalog](packaging/dependency-sources.json) records
immutable source archive URLs, SHA-256 hashes, native media configuration and runtime
matches. The release serves these archives inside `Nexus-dependency-sources.zip`
alongside the installer, rather than relying on upstream links alone.
Original license/copyright texts from installed wheels and source archives are
included in `distribution-notices/licenses`. Nexus source is included in
`distribution-notices/nexus-source.zip` and the release's `Nexus-source.zip`.
**Tools → About Nexus and licenses** opens these notices and source access.

| Distributed component | Terms and corresponding source |
| --- | --- |
| PyQt6 6.11.0 / SIP 13.12.0 | GPLv3 PyQt route; exact PyPI sources and full GPL text supplied. [Riverbank](https://www.riverbankcomputing.com/software/pyqt/intro) |
| Qt runtime 6.11.2 | Qt base, multimedia, SVG, image formats and translations sources and their original LGPLv3/GPLv3/permissive notices supplied. DLL replacement and rebuilding are permitted. [Qt obligations](https://www.qt.io/development/open-source-lgpl-obligations) |
| PyAV 19.0.0 and FFmpeg 9.0.2 | PyAV BSD-3-Clause; FFmpeg includes GPL x264/x265 and other codec libraries. Sources, headers, build recipes and patches supplied. The combined application uses GPLv3 even though a runtime FFmpeg license string reports LGPL. [PyAV build recipes](https://github.com/PyAV-Org/pyav-ffmpeg/tree/bac889417e26be29615cb6a3f38318151fed55cd), [FFmpeg](https://ffmpeg.org/legal.html) |
| Qt FFmpeg 7.1.5 / zlib 1.3.1 | LGPL-2.1-or-later FFmpeg, dynamic DLLs; exact source and recorded configuration supplied. zlib notice retained |
| GCC / libstdc++ runtime 16.1.0-5 | GNU licenses with GCC Runtime Library Exception; MSYS2 corresponding sources, patches, recipes and exception text supplied |
| libiconv 1.19 / winpthreads | Original GNU/permissive terms; native code matched to MSYS2 packages; source packages and notices supplied |
| edge-tts 7.2.8 | LGPLv3 client, exact source supplied. Online speech service terms are separate; service voices are not redistributed |
| pyttsx3 2.99 / certifi / tqdm | Original MPL/permissive terms preserved; exact source archives supplied |
| Python 3.12.10 / PyInstaller | PSF Python license and original runtime notices; PyInstaller GPL bootloader exception. Sources and notices supplied |
| NumPy, OpenBLAS, ONNX Runtime, CTranslate2, sherpa-onnx, lxml, tokenizers and other libraries | Original wheel/source notices, including native third-party notices, supplied. Python inputs and actual frozen-file hashes are recorded separately |
| Microsoft runtime DLLs | Unchanged redistributable files carried by original Python/Qt/native wheels; original Microsoft terms apply. Windows system libraries are external |

Unused QtPdf/qpdf/software OpenGL, SoundFile/libsndfile and nonstandard PortAudio
backends are excluded. Standard x64 PortAudio retains its original license.
The actual bundle's `frozen-files.json` lists shipped resources and DLL/PYD hashes;
`build-environment.json` describes installed build inputs, not a certified SBOM.
This inventory and source delivery are technical distribution preparation, not an
independent legal certification.

## Models and assets

- faster-whisper includes a small **MIT-licensed Silero VAD** asset. Its upstream
  source archive and copyright notice are supplied; it is recorded in the frozen inventory.
- LLM, Whisper and Supertonic weights are not bundled. Model preparation is an explicit
  user action. Supertonic model terms are OpenRAIL-M, separately from sherpa-onnx's
  Apache runtime. [Original Supertonic](https://github.com/supertone-oss-archive/supertonic),
  [converted model distribution](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models).
- User-selected language/embedding models retain their own terms. Nexus grants no rights
  to those weights. Online providers and tools have separate service/privacy boundaries.
- UI sounds and artwork generated for Nexus are supplied with its authored source.
  Screenshots use synthetic text. Windows fonts are not shipped as font files.

The installer is unsigned and the app is provided without warranty. Release assets
include checksums and the clean Windows check report. Review new dependency versions,
native components and model assets before future redistributions; the pinned catalog
is specific to Beta 2. See the [build and verification guide](docs/WINDOWS_PREVIEW.md).
