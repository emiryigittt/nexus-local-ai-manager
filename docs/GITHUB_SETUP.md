# Starting on GitHub from scratch

**English** · [Türkçe](GITHUB_SETUP.tr.md) · [Documentation](INDEX.md)

The public repository is now [emiryigittt/nexus-local-ai-manager](https://github.com/emiryigittt/nexus-local-ai-manager).
The README includes its real clone URL. The instructions below describe the initial
setup process; see the [publication verification](PREPUBLICATION_CHECK.md) for current results.

## 1. Create your account

Choose your own username on [GitHub signup](https://github.com/signup), verify your
email and enable two-factor authentication. Complete credentials, verification and
recovery steps yourself; do not share passwords or codes in chat.
[Official account guide](https://docs.github.com/en/account-and-profile/how-tos/account-management/creating-an-account-on-github).

## 2. Open the local project in GitHub Desktop

[GitHub Desktop](https://desktop.github.com/) is an optional alternative to terminal
commands. After installation and sign-in, choose **File → Add local repository**
and select the existing Nexus folder. This workspace already has Git metadata;
do not delete `.git` or initialize a replacement repository.
[Official local repository guide](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-a-repository-from-your-local-computer-to-github-desktop).

## 3. Review before the first commit

- Read both README versions and inspect the screenshot.
- Keep `.env`, virtual environments, models, recordings, SQLite databases, personal
  screenshots and MCP configuration out of the change list.
- Personal document outputs under `output/pdf/` and `tmp/pdfs/` are excluded, not
  deleted. Keep them private; do not force-add them to Git. The preflight checks
  these paths even when tracked, and rejects links to files excluded from publication.
- Run `scripts/check_public_repo.py`; it is a preliminary check, not a full secret/history audit.
- Review each file in Desktop and commit only prepared source/docs. Example message:
  `Prepare Nexus development preview`.
- Check commit-email privacy in GitHub and Desktop settings.
- Read [third-party notices](../THIRD_PARTY_NOTICES.md) without silently changing the license.

## 4. Private review first, public launch later

For initial review, choose your repository name in **Publish repository** and keep
**Keep this code private** selected. `nexus` is only a name suggestion; the choice
is yours. Publishing uploads files to GitHub; it is distinct from a local commit.
[Official publishing guide](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-an-existing-project-to-github-using-github-desktop).

Review all history before uploading: deleting a secret now does not remove it from
earlier commits. No remote was configured, removed or changed during this preparation.
Check CI and a clean-machine installation in the private repository. Before public release:

- [ ] Complete live-model memory and everyday workflow tests.
- [ ] Test a clean Windows installation and hosted GitHub CI.
- [ ] Decide PyQt/Qt and model distribution terms and required notices.
- [ ] Review files, images and Git history for private data/secrets.
- [ ] Record a real demo with accurate limitations.
- [ ] Obtain the owner's public-publication approval.

## 5. After repository creation

- Suggested description: “A Windows desktop assistant for your local AI model —
  documents, voice, and user-controlled memory, one shortcut away.”
- Add the real URL to README installation and demo end card.
- Add a real CI badge only after hosted checks run successfully.
- Publish [first-task briefs](GOOD_FIRST_ISSUES.md) as issues and create suitable labels.
- Enable Discussions for questions; never link to a support channel that is not open.
- Enable private vulnerability reporting and check notifications. A SECURITY file
  alone does not enable the feature.
  [Official reporting guide](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
- Add the owner's chosen private conduct-reporting contact.
- After pilot feedback, follow the [launch plan](GITHUB_LAUNCH_PLAN.en.md).

A Windows installer is not part of this preparation; it follows feature stabilization.
