# Security policy

**English** · [Türkçe](SECURITY.tr.md) · [Documentation](docs/INDEX.md)

## Reporting a vulnerability

Please do not open a public issue with vulnerability details. Once the repository
owner enables it, use private vulnerability reporting in the **Security** tab.
This local preparation has not created a GitHub repository or enabled that channel.
If it is unavailable, request a private reporting channel without posting exploit
details, credentials, or personal data. Enabling a working channel is a public-launch gate.
Include reproduction steps, affected versions, impact, and any suggested fix.

Maintainers aim to acknowledge reports promptly; no response-time SLA is promised.
Allow time for a fix and coordinated disclosure before publishing details.

## Scope and safe defaults

Nexus binds its API to `127.0.0.1` by default and does not require an API key
for that local gateway. Do not expose the gateway port to an untrusted network.
Provider keys belong in `.env`, which is ignored by Git.

Loopback binding and CORS are not authentication or process isolation. Other local
programs can reach the unauthenticated gateway. Gateway authentication is an open
hardening task, not a shipped feature. SQLite data is not encrypted by Nexus.
Third-party MCP processes are not OS-sandboxed by tool permission prompts.

The `/web` command and optional Edge TTS feature contact third-party services.
See the privacy section in the README before using them with sensitive data.

Read [the full boundaries](docs/PRIVACY.md). Only the current development branch is
maintained; there is not yet a supported stable-release series.
