from services.api_keys import gemini_key_candidates


def test_gemini_key_candidates_are_ordered_and_unique(monkeypatch):
    primary = "AIza" + "A" * 30
    second = "AIza" + "B" * 30
    third = "AQ." + "C" * 30
    monkeypatch.setenv("GOOGLE_API_KEY", primary)
    monkeypatch.setenv("GOOGLE_API_KEY_2", second)
    monkeypatch.setenv("GOOGLE_API_KEY_3", third)

    assert gemini_key_candidates(primary) == [primary, second, third]
