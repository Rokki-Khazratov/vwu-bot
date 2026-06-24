import pytest

from app.modules.writing.word_count import count_words, normalize_text


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", 0),
        ("Hello world", 2),
        ("I don't know", 3),  # contraction counts as one word
        ("It's a well-known fact", 4),  # hyphenated compound = one word
        ("One,  two   three\nfour", 4),
        ("  spaced  ", 1),
    ],
)
def test_count_words(text, expected):
    assert count_words(text) == expected


def test_normalize_text_strips_and_nfc():
    assert normalize_text("  café  ") == "café"
