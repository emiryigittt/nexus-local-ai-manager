# First contribution briefs

**English** · [Türkçe](GOOD_FIRST_ISSUES.tr.md) · [Documentation](INDEX.md)

These are local issue drafts, not already-published GitHub issues. Maintainers should
confirm scope and add `good first issue` / `help wanted` only after publication.
Choose one task and discuss it before opening a large pull request.

## 1. Explain memory approval in the first-use experience

Suggested labels: documentation, good first issue.

Problem: an extracted candidate can look like a missing memory to a new user.
Scope: add a short synthetic walkthrough with screenshots to the user guide.

Acceptance:

- Show candidate, active and disabled states using temporary data.
- Explain the independent memory-use and automatic-extraction settings.
- Show approval and deletion; do not claim automatic activation.
- Keep English/Turkish wording consistent and run the public-repo check.

## 2. Audit accessible names in the main composer

Suggested labels: accessibility, good first issue.

Scope: attach, research, Tools, microphone and send controls in `frontend/spotlight_view.py`.
Do not redesign the window or add a dependency.

Acceptance:

- Each control has a meaningful accessible name and description where needed.
- Add a small Qt test for names and keyboard reachability.
- Record actual Narrator findings if tested; never present offscreen tests as a screen-reader pass.
- Preserve existing shortcuts and layout.

## 3. Add Turkish text-boundary regression cases

Suggested labels: tests, good first issue.

Scope: `backend/speech_chunks.py` and its tests. Use synthetic text, no voice downloads.

Acceptance:

- Cover common abbreviations, decimal numbers, numbered lists and split tokens.
- Assert that text is neither dropped nor duplicated and chunk length remains bounded.
- Document any deliberately unsupported boundary instead of weakening assertions.
- Keep tests independent of network, microphone and installed speech models.

## 4. Extend English UI localization to conversation history

Suggested labels: localization, help wanted (not necessarily a beginner task).

The main-window pilot is implemented. Scope: only the history dialog, using
`frontend/i18n.py`; preserve search, selection and deletion behavior.

Acceptance:

- Respect saved language preference; retain Turkish as a supported choice.
- No hard-coded language choice in business logic or shortcut behavior.
- Test both languages and update screenshots using synthetic data.
- Translate controls and confirmations, never conversation titles or message content.
- Do not claim the entire application is translated after this scoped change.
