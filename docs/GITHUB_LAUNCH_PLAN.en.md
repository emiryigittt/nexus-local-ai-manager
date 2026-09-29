# GitHub community and launch plan

**English** · [Türkçe](GITHUB_LAUNCH_PLAN.md) · [Documentation](INDEX.md)

26 September 2026 · Draft; no publication, account change or external sharing has
taken place. Windows packaging follows feature stabilization.

## Completed local preparation

- [x] English/Turkish READMEs and current synthetic-content interface preview.
- [x] Source quick start, usage/troubleshooting and privacy documentation.
- [x] Non-personal demo fixture and recording storyboard; no recorded video yet.
- [x] Four contribution briefs and privacy/verification fields in issue/PR templates.
- [x] Working-tree file, obvious-secret and local-link preflight integrated into CI.
- [x] Git exclusions for old personal screenshots and runtime data.
- [x] Initial licensing inventory with PyQt/Qt/model distribution decisions left open.
- [x] [First-time GitHub guide](GITHUB_SETUP.md).

Prepared materials: [English README](../README.md), [Türkçe README](../README.tr.md),
[usage](USER_GUIDE.md), [privacy](PRIVACY.md), [demo](DEMO_SCRIPT.md),
[contribution briefs](GOOD_FIRST_ISSUES.md), [license notes](../THIRD_PARTY_NOTICES.md).
No account/repository, commit, push or external post was created during preparation.

Previous preparation checkpoint: 187 local tests passed, Ruff passed, four GitHub YAML
files parsed, and preflight reported no findings across 123 Git-visible files.
This does not verify every secret format, image content, Git history, remote link or
hosted workflow. The intermittent Windows cleanup warning was absent in that run,
but its open issue was not closed.

## Positioning

### Bilingual launch preparation

- [x] Thirteen English/Turkish document pairs and a [shared documentation index](INDEX.md).
- [x] Each README routes to usage, privacy and contribution guides in its language.
- [x] Issue/feature/PR templates support both languages.
- [x] [Announcement and pilot invitation drafts](LAUNCH_COPY.md) prepared in both languages; not posted.
- [x] Paired files and reciprocal language links checked during publication preflight.
- [ ] Complete English application UI localization and real demo recordings in both languages.

Bilingual preparation verification: 194 tests passed, Ruff passed and four YAML
files parsed. Preflight found no issues across 138 Git-visible files. The known
intermittent Windows asyncio cleanup warning recurred and remains open. Pair checks
verify files/navigation, not semantic equivalence of translations.

English will be the primary entry with a visible Turkish link. Documentation
translation is neither full application localization nor a visibility guarantee.

### Main message

Final check on 27 September: personal document/photo outputs were preserved and
excluded from publication. Links to unpublished files are now checked. All 199
tests and Ruff passed; preflight found no issues across 138 candidate files. The
cleanup warning was absent in this run but remains an intermittent open issue.
No files were uploaded to GitHub.

Proposed message: a simple desktop assistant that gives your chosen local model
useful abilities while keeping personal memory under your control. The distinction
is the combined everyday workflow: keyboard access, documents, inspectable memory
sources and optional local speech, rather than chat alone.

Stars and Trending placement cannot be guaranteed. First aim for successful setup,
one useful completed task and voluntary feedback from people who return a week
later. Do not add hidden telemetry.

## Ordered deliverables

1. **Reliability gate:** finish live-model and user checks in the voice/memory report;
   keep experimental wake behavior, licensing and known issues visible.
2. **Real 60–90 second demo:** shortcut → document summary → voice → memory candidate
   → approval → recall in a new session. Use synthetic content, disclose edits to
   waiting time and show local/cloud boundaries.
3. **English/Turkish onboarding:** value proposition, demo, environment, short setup
   and one useful example. Do not imply Python-free installation exists. Include
   hardware/model-qualified measurements, privacy table and troubleshooting.
4. **Contribution entry points:** review CONTRIBUTING, SECURITY, templates and CI.
   Scope small translation/accessibility/speech-fixture tasks with acceptance criteria.
   The `good first issue` label can help GitHub surface contribution opportunities.
   [GitHub labels guide](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/encouraging-helpful-contributions-to-your-project-with-labels).
5. **Community space:** propose Q&A, ideas and workflow Discussions separately from
   bug reports. Enable only with the owner's approval at publication time.
   [Discussions guide](https://docs.github.com/en/discussions/quickstart).
6. **Discoverability:** use accurate topics such as `local-ai`, `desktop-assistant`,
   `ollama`, `lm-studio`, `voice-assistant`, `windows`, `python`, plus a clear description.
   Topics support discovery of related repositories; avoid irrelevant keyword stuffing.
   [GitHub topics guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).
7. **Small pilot, then announcement:** try setup/workflows with 5–10 volunteers and
   fix critical issues. Before posting a demo, check each community's current rules
   and disclose that you build the project. No bulk messaging, bought stars or star swaps.
8. **Sustainable follow-through:** publish concise release notes, reproducible bugs
   and contributor acknowledgements. Evaluate response time, resolved setup barriers
   and voluntary repeat-use feedback.

## Public-launch checklist

- [ ] Live-model memory and voice acceptance checks complete.
- [x] Voice limitations and experimental features explicitly documented.
- [ ] Distribution review of dependencies/models/reference voices complete.
- [x] Bilingual quick start prepared.
- [ ] Real demo recorded and reviewed.
- [ ] Documented source installation tested on a clean Windows machine.
- [x] First contribution drafts prepared.
- [ ] Real issues, Discussions and private security/conduct channels opened.
- [ ] Local API authentication and untrusted-provider-address hardening evaluated.
- [ ] Publication contents/history reviewed for private data and secrets.
- [ ] Owner approves publication and external sharing.
