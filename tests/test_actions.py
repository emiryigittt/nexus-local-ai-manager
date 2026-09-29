from backend.actions import ActionRegistry


def test_builtin_action_renders_input():
    action = ActionRegistry().get("summarize")

    assert action is not None
    assert action.render("  hello  ").endswith("hello")


def test_user_action_overrides_builtin_and_invalid_is_skipped(tmp_path):
    (tmp_path / "actions.yaml").write_text(
        """
- id: summarize
  name: Özel özet
  description: Kişisel özet biçimi
  prompt: 'Üç maddede özetle: {input}'
- id: invalid
  name: Eksik
  prompt: Girdi alanı yok
""",
        encoding="utf-8",
    )

    actions = ActionRegistry(tmp_path).all()
    selected = next(item for item in actions if item.id == "summarize")

    assert selected.name == "Özel özet"
    assert not any(item.id == "invalid" for item in actions)
