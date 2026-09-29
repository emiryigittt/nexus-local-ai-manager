from backend.memory_learning import parse_candidates, unsafe_for_automatic_memory


def test_candidate_parser_accepts_strict_valid_payload():
    candidates = parse_candidates(
        '{"candidates":[{"content":"Kısa yanıtları sever","key":"response.length",'
        '"memory_type":"preference","confidence":0.9,"importance":0.8,'
        '"sensitive":false}]}'
    )

    assert len(candidates) == 1
    assert candidates[0].memory_type == "preference"


def test_candidate_parser_rejects_malformed_or_unknown_types():
    assert parse_candidates("not-json") == []
    assert parse_candidates(
        '{"candidates":[{"content":"x","key":"unknown.value","memory_type":"secret",'
        '"confidence":1,"importance":1,"sensitive":false}]}'
    ) == []


def test_sensitive_information_is_blocked_from_automatic_memory():
    assert unsafe_for_automatic_memory("API key: sk-abcdefghijklmnop")
    assert unsafe_for_automatic_memory("TC kimlik numaram 12345678901")
    assert unsafe_for_automatic_memory("Teşhis bilgim burada")
    assert not unsafe_for_automatic_memory("Kısa teknik cevapları tercih ederim")
