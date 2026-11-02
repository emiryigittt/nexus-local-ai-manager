# Agent guide

Instructions for AI coding agents working in this repository. Read this first, then
open [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before touching the API gateway,
the tool subsystem or the MCP client. The architecture map contains verified line
references, the process lifecycle, the consent model and a list of findings with the
method used to confirm each one.

**Türkçe:** Bu depoda çalışan yapay zeka ajanları için kısa talimat. API ağ geçidi,
araç alt sistemi veya MCP istemcisi ile çalışmadan önce
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) dosyasını oku; oradaki bulgular doğrulanmış
satır referanslarına dayanıyor.

## Gate commands

CI runs all three on Windows with Python 3.11, 3.12 and 3.13. Run them locally
before proposing a change; see [CONTRIBUTING.md](CONTRIBUTING.md) for setup.

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts\check_public_repo.py
```

`check_public_repo.py` fails on any Markdown link that does not resolve to a
git-visible file, on unpublishable paths, and on language pairs in
`docs/languages.json` that are missing a file or a reciprocal link. Text inside
triple-backtick fences is not link-checked.

## Non-negotiables

* **The local API has no authentication.** Keep the bind address on `127.0.0.1`;
  never widen `NEXUS_BACKEND_HOST` casually. See [SECURITY.md](SECURITY.md).
* Do not commit `settings.json`, `mcp_servers.json`, `last_debug.json`, `.env`,
  databases, logs, models or recordings. They are runtime state.
* Add or update tests for behaviour changes. Tests must not touch the real data
  directory; pass an explicit `path` to the stores or set `NEXUS_DATA_DIR`.
* Turkish is the primary user-facing language in code. Keep `README.md` and
  `README.tr.md` consistent and never claim a fully translated UI.

## Things that will bite you

* `MCPManager.shutdown()` (`mcp_client.py:248-274`) stops every connected client, and
  `main.py:45-49` calls it from the ASGI lifespan, so a clean backend exit reaps its
  MCP children. There is still **no** `MCPManager.stop()` — writing
  `await mcp_manager.stop()` raises `AttributeError`.
* `run_nexus.py` stops the backend with `terminate()`, which skips all Python-level
  cleanup. What reaps the survivors is a Windows kill-on-close job
  (`backend/process_job.py`), not the shutdown handler.
* MCP stderr is drained into a bounded tail by a background task. Never read
  `process.stderr` yourself: a pipe nobody reads fills and the child blocks in
  `write(2)`.
* `ToolDefinition.risk` and `requires_confirmation` are never read by the
  authorizer. Authorization depends only on the `consent` request field and the
  stored `tool_permissions` row.
* A tool call with no stored permission returns **HTTP 409**, not 403. A client must
  prompt and retry with `consent`. `consent: "once"` is not persisted.
* Filesystem scopes apply only to the built-in `local:file.read` tool. MCP tools run
  unsandboxed in their own processes.
* `POST /chat` performs no tool calling. The outbound payload has no `tools` field;
  tool execution is a separate endpoint that nothing in `frontend/` currently calls.
* Importing `backend.tool_security` creates the SQLite schema and registers
  `local:file.read` as an import side effect.
* Search results are polluted by `.pytest-tmp/`, `.pytest_cache/` and `tmp/`
  fixtures. Scope greps to `backend/` and `frontend/`.

## Where things live

| Area | File |
| --- | --- |
| Routes, request models, chat plumbing | `backend/main.py` |
| Consent, scopes, audit, execution | `backend/tool_security.py` |
| Tool metadata and ids | `backend/tool_registry.py` |
| MCP config, stdio client, manager | `backend/mcp_client.py` |
| Data directory and file locations | `backend/app_paths.py` |
| Environment-backed settings | `backend/config.py` |
| Launcher and process supervision | `run_nexus.py` |
| Windows job object that reaps the tree | `backend/process_job.py` |
| Executable behaviour for tools | [tests/test_tools.py](tests/test_tools.py) |

Documentation index: [docs/INDEX.md](docs/INDEX.md).
