from frontend.history import PromptHistory


def test_history_navigation_and_deduplication():
    history = PromptHistory(max_history=3)
    history.add(" first ")
    history.add("first")
    history.add("second")

    assert history.history == ["first", "second"]
    assert history.get_previous() == "second"
    assert history.get_previous() == "first"
    assert history.get_next() == "second"
    assert history.get_next() == ""


def test_history_respects_max_size():
    history = PromptHistory(max_history=2)
    for prompt in ("one", "two", "three"):
        history.add(prompt)

    assert history.history == ["two", "three"]
