# Contributing to Nexus

**English** · [Türkçe](CONTRIBUTING.tr.md) · [Documentation](docs/INDEX.md)

Thanks for helping make Nexus more useful. Small, focused pull requests are the
easiest to review and merge.

## Before you start

For a bug, open an issue with Windows and Python versions, model provider, steps
to reproduce, expected behavior, and relevant logs with secrets removed. For a
large feature, open a proposal first so implementation work is not duplicated.

Reports and contributions in English or Turkish are welcome. Use synthetic content and do
not upload your database, personal recordings or full environment dumps. For small
scoped tasks, see [first contribution briefs](docs/GOOD_FIRST_ISSUES.md). They are
drafts until the maintainer creates the corresponding GitHub issues.

## Local development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts\check_public_repo.py
```

Run with `.\.venv\Scripts\python.exe run_nexus.py`. `.env` is optional; use normal
settings for day-to-day testing. The automated suite uses isolated data and does not
require a running model or microphone. The scripts named `check_voice`, `check_memory`
and `check_wake_word` have additional runtime requirements; see the user guide.

## Pull requests

1. Keep changes scoped to one concern.
2. Add or update tests for behavior changes.
3. Update user-facing documentation when configuration or shortcuts change.
4. Never commit `.env`, model files, credentials, or personal prompt data.
5. Confirm tests and lint checks pass and explain how the change was verified.
6. Keep README.md and README.tr.md consistent. Do not claim full English UI translation.
7. Document any new dependency/model license and network/privacy boundary.

By contributing, you agree that your contribution is licensed under the MIT
License used by this project.

Dependency and model licenses remain separate; see [third-party notices](THIRD_PARTY_NOTICES.md).
