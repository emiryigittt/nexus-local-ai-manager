import pytest

from backend.speech_chunks import take_speech_chunks


@pytest.mark.parametrize("text,expected,remainder", [
    ("Merhaba! Evet. kalan", ["Merhaba!", "Evet."], "kalan"),
    ("Değer 3.14 oldu. Tamam", ["Değer 3.14 oldu."], "Tamam"),
    ("1. Önce aç. Sonra", ["1. Önce aç."], "Sonra"),
    ("Bitti. 2026 yılı", ["Bitti."], "2026 yılı"),
    ("Yarım bir cümle", [], "Yarım bir cümle"),
])
def test_sentence_boundaries(text, expected, remainder):
    assert take_speech_chunks(text) == (expected, remainder)


def test_long_text_is_bounded_without_losing_words():
    text = " ".join(["uzun açıklama, ayrıntılı örnekler ve sonuçlar"] * 30)
    chunks, remainder = take_speech_chunks(text, flush=True)
    assert not remainder
    assert all(len(chunk) <= 180 for chunk in chunks)
    assert " ".join(chunks) == text


def test_streaming_partials_preserve_text():
    text = "Merhaba! Bugün 3.14 değerini inceleyelim. Son söz"
    pending, emitted = "", []
    for character in text:
        chunks, pending = take_speech_chunks(pending + character)
        emitted.extend(chunks)
    chunks, pending = take_speech_chunks(pending, flush=True)
    assert " ".join(emitted + chunks) == text
    assert pending == ""
