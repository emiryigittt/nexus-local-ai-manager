# Windows distribution license

**English** · [Türkçe](DISTRIBUTION_LICENSE.tr.md)

The combined Nexus Windows application is distributed under **GNU GPL version 3**
([full text](COPYING)). Nexus-authored source retains its [MIT license](LICENSE).
The MIT copyright and permission notice remains applicable to that source.
Third-party components retain their own licenses and copyright notices; this
document does not relicense them. See [third-party notices](THIRD_PARTY_NOTICES.md).

You may run, study, modify and redistribute the combined application under the GPL.
There is no additional EULA, activation key, signing requirement or restriction on
reverse engineering for debugging modifications. The application is supplied
without warranty, as described in the applicable licenses.

The installer includes `distribution-notices`, complete Nexus source and third-party
license texts. **Tools → About Nexus and licenses** opens these files. The release
also provides dependency source archives, exact version and SHA-256 manifests,
and the build instructions. Download the corresponding source alongside the binary
from the same [GitHub release](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.2).
Redistributors must preserve the notices and meet the source obligations of the
applicable licenses. An upstream URL alone is not the source delivery mechanism.

Qt and media libraries are dynamically linked. You can rebuild Nexus, replace
compatible DLLs in the unpacked application, and distribute a modified build under
the applicable licenses. No installation authorization information is required.
The build is unsigned. Windows system libraries are not part of the corresponding
source; Microsoft runtime redistributables retain their original terms.

LLM, Whisper and Supertonic model weights are downloaded separately or supplied
by the user, and retain their respective terms. The small MIT-licensed Silero VAD
asset shipped by faster-whisper is included in the dependency inventory.
