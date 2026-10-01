# Third-party software and model notices

**English** · [Türkçe](THIRD_PARTY_NOTICES.tr.md) · [Documentation](docs/INDEX.md)

Preparation inventory, checked 26 September 2026; not a complete distribution audit
or legal opinion. Nexus-authored source remains under [MIT](LICENSE). This does not
change any dependency, model, voice, dataset, icon, or screenshot license.

## Release-sensitive components

| Component | Upstream information | Required before a bundled distribution |
| --- | --- | --- |
| PyQt6 | Riverbank offers GPL v3 or a commercial license, not LGPL. Qt bundled in wheels has separate terms. [Official licensing information](https://www.riverbankcomputing.com/software/pyqt/intro) | Decide and document a compliant distribution approach; preserve notices and review the complete combination. Do not label the entire bundle “MIT-only” |
| Supertonic | Example code MIT; model OpenRAIL-M; upstream archived. [Official repository](https://github.com/supertone-oss-archive/supertonic) | Verify the exact downloaded model/revision, restrictions and notices; record checksums |
| sherpa-onnx model package | Nexus downloads a quantized model from [upstream releases](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models) | Check converted artifact notices against the original model; runtime and weights are separate |
| Whisper / faster-whisper | Runtime and downloaded weights are separate artifacts. [Runtime source](https://github.com/SYSTRAN/faster-whisper) | Inventory actual versions, model origin and their license files |
| Edge speech | Network-backed service accessed through a client library | Check service availability/terms separately from client code licensing; do not redistribute service voices |
| User-selected LLM / embedding models | Chosen outside this repository | User must check each model's requirements and license; Nexus grants no rights to those weights |

The dependency inputs are [requirements.txt](requirements.txt),
[requirements-tts.txt](requirements-tts.txt), and [requirements-dev.txt](requirements-dev.txt).
Version ranges are not a locked software bill of materials. Qt multimedia codecs,
native wheels and transitive packages also need inventory for an actual release.

## Assets

The README uses only the current application preview under `docs/assets/voice-memory/`,
generated with synthetic text. Windows fonts visible in screenshots are not bundled
as font files. Older root-level personal screenshots are excluded from Git by default,
not deleted. Review every new screenshot for private content before committing it.

## Open gates

- [ ] Decide the PyQt/Qt distribution approach with the project owner; do not silently relicense.
- [ ] Inventory exact runtime/transitive versions and collect required license texts.
- [ ] Inventory and checksum downloaded model artifacts separately from application code.
- [ ] Confirm rights/consent for any future demo voice or reference recording.
- [ ] Complete a distribution review before any executable/installer release.

Nexus now supports a [local installer preview](docs/WINDOWS_PREVIEW.md), with source,
available dependency license texts and a build-environment inventory. It is not a
public release or a completed distribution audit. No source license change or
model redistribution is made; the gates above remain open.
