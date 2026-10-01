import io
import tarfile

import pytest

from scripts.prepare_distribution import archive_notices, is_notice


@pytest.mark.parametrize("name", ["../LICENSE", "/tmp/LICENSE", "C:/Users/test/LICENSE", "..\\LICENSE", "C:\\Users\\test\\LICENSE", "folder/LICENSE.dll"])
def test_upstream_notice_paths_cannot_escape_output(name):
    assert not is_notice(name)


def test_full_copyleft_texts_are_collected_and_symlinks_ignored(tmp_path):
    source = tmp_path / "sources.tar.gz"
    text = b"synthetic full license text"
    with tarfile.open(source, "w:gz") as archive:
        for name in ("package/COPYING.LIB", "package/COPYING.GPLv3", "package/LICENSES/LGPL-3.0-only.txt", "../LICENSE"):
            entry = tarfile.TarInfo(name)
            entry.size = len(text)
            archive.addfile(entry, io.BytesIO(text))
        entry = tarfile.TarInfo("package/LICENSE-link")
        entry.type = tarfile.SYMTYPE
        entry.linkname = "../../outside"
        archive.addfile(entry)
    output = tmp_path / "notices"
    assert archive_notices(source, output) == 3
    assert (output / "package/COPYING.LIB").read_bytes() == text
    assert not (tmp_path / "LICENSE").exists()
    assert not (output / "package/LICENSE-link").exists()
