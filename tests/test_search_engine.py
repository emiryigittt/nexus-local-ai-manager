from backend.search_engine import score_relevance


def test_title_matches_are_weighted_more_than_body_matches():
    title_score = score_relevance("local ai", "Local AI for Windows", "")
    body_score = score_relevance("local ai", "Unrelated", "local ai")

    assert title_score > body_score


def test_matching_uses_words_instead_of_substrings():
    assert score_relevance("cat", "Concatenate strings", "") == 0
