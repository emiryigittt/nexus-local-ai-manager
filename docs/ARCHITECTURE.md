# Backend architecture and tool execution map

Working technical record for the API gateway, the tool/MCP execution path and the
process lifecycle. It is written for the next engineer **or AI agent** to be read
before changing `backend/main.py`, `backend/tool_security.py` or
`backend/mcp_client.py`.

**Türkçe:** Bu belge, araç (tool) ve MCP çalışma yolunu, güvenlik sınırlarını ve
süreç yaşam döngüsünü doğrulanmış satır referanslarıyla haritalar. Kodu
değiştirmeden önce okunması amaçlanan teknik bir çalışma kaydına dayanır.

Technical working records in this repository stay in their original language; see
the note at the bottom of [INDEX.md](INDEX.md). Every claim below carries a
symbol reference, and the [verification log](#11-verification-log) records how each
finding was produced, so later agents can re-check rather than trust it.

Line numbers describe the working tree at the time of writing and will drift.
Grep for the **symbol name** first; the number is only a shortcut.

---

## 1. Process topology

Three process levels are involved. The top and the bottom are the ones that get
confused most often.

```text
run_nexus.py                     launcher / supervisor (parent)
  ├── uvicorn backend.main:app   API gateway         (child)
  │     └── MCP server child     node / npx / python (grandchild) ← orphans
  └── python -m frontend.app     PyQt desktop client (child)
```

* `run_nexus.py:main()` starts the backend only when `GET /health` does not
  already answer (`_is_backend_ready()`). If a backend is already listening, the
  launcher never owns it and never stops it.
* `run_nexus.py:_stop()` uses `subprocess.Popen.terminate()`. On Windows that is
  `TerminateProcess()`: no `atexit`, no asyncio cleanup, **no ASGI lifespan
  shutdown**. What catches the processes that survive it is the kill-on-close job
  object both children are assigned to (`run_nexus.py:142-189`,
  [section 9.2](#92-containment-a-kill-on-close-job-object)).
* MCP servers are spawned by `MCPClient.start()` with
  `asyncio.create_subprocess_exec()` (`mcp_client.py:72-96`). They are
  grandchildren of the launcher, in their own stdio pipes, and they inherit the
  launcher's job.
* `--backend` runs `uvicorn.run()` without `reload`, so there is one worker
  process and one event loop; there is no multi-worker re-spawning to reason about.

Consequence: a clean backend exit reaps MCP children through the lifespan handler,
and a hard exit reaps them through the job object. What is *not* covered is a backend
the launcher never started because one was already listening, and therefore never
owns. See [G1](#g1--no-application-shutdown-hook-closed),
[G3](#g3--the-launcher-kills-the-backend-with-terminate-closed).

## 2. Module map

```text
backend/main.py            FastAPI app, pydantic request models, 35 routes
  ├── backend/config.py            Settings.from_env()  (module-level singleton)
  ├── backend/app_paths.py         data dir, nexus.db, mcp_servers.json, settings.json
  ├── backend/providers.py         discovery / probe / select of OpenAI-compatible hosts
  ├── backend/chat_context.py      recent_turns() history trimming
  ├── backend/{memory,memory_retrieval,memory_learning,memory_jobs,
  │            conversation_summaries,conversations,documents,embeddings,
  │            identity,search_engine,model_output,user_settings,actions}
  └── backend/tool_security.py     authorization + audit + execution
        ├── backend/tool_registry.py    ToolDefinition, ToolRegistry, global singleton
        └── backend/mcp_client.py       MCPConfigStore, MCPClient, MCPManager

run_nexus.py                 launcher: supervises the backend and the desktop client
  └── backend/process_job.py          ProcessJob (Windows kill-on-close job object)
```

Import side effects that matter when writing tests:

* `tool_registry`, `mcp_config_store`, `mcp_manager`, `tool_security_store` and
  `tool_executor` are **module-level singletons** created at import time.
* Importing `backend.tool_security` opens (and creates) the SQLite database and
  runs `CREATE TABLE IF NOT EXISTS` for `tool_permissions`, `filesystem_scopes`
  and `tool_audit` inside `ToolSecurityStore.__init__`.
* Importing `backend.tool_security` also registers the only built-in tool,
  `local:file.read`, at the bottom of the module (`tool_security.py:184-196`).
  The registration lives in the security module, not in `tool_registry.py`.
* `backend/config.py` reads `.env` and freezes `Settings` at import time, so a
  test that monkeypatches `os.environ` after import must patch the settings
  object, not the environment.

## 3. Configuration layers

Three unrelated stores are often mistaken for one.

| Layer | Owner | Location | Contents | Reload |
| --- | --- | --- | --- | --- |
| Environment / `.env` | `config.py` | repo `.env` via `load_dotenv` | provider base URL, key, model, timeout, host, port | at import only |
| SQLite | repositories + `ToolSecurityStore` | `<data>/nexus.db` | conversations, documents, memories, tool permissions, filesystem scopes, tool audit | per query |
| JSON files | `MCPConfigStore`, `settings_store` | `<data>/mcp_servers.json`, `<data>/settings.json` | MCP server commands, UI preferences | per request |

`<data>` is resolved by `app_paths.data_dir()`: `NEXUS_DATA_DIR`, else
`%LOCALAPPDATA%\Nexus`, else `~/.local/share/Nexus`.

Two details worth remembering:

* The MCP config file is `mcp_servers.json`, and both `mcp_servers.json` and
  `settings.json` are in `check_public_repo.FORBIDDEN_NAMES` — they must never be
  committed.
* `config.py`'s module docstring says the project "deliberately avoids a
  mandatory dotenv dependency", but the module calls `load_dotenv()`
  unconditionally (`config.py:13-15`). The dependency is optional in
  requirements, present in practice. See [G8](#g8--configpy-docstring-contradicts-the-code).

## 4. Tool execution flow

Tools are **never** executed as a side effect of chatting. There is no
function-calling loop anywhere in the backend.

```text
POST /api/v1/tools/{tool_id}/call        body: { "arguments": {...}, "consent": "once|always|deny"|null }
  └─ main.call_tool()                                        main.py:604
       └─ ToolExecutor.execute(tool_id, arguments, consent)  tool_security.py:151
            ├─ registry.get(tool_id)          → None  → KeyError      → HTTP 404
            ├─ _authorize(tool, consent)      tool_security.py:128
            ├─ branch on tool_id / tool.source
            │    ├─ "local:file.read"  → _safe_file() → scope check → read ≤ 1 MB
            │    └─ source == "mcp"    → manager.clients[server_id].call_tool(name, arguments)
            │                            → JSON-RPC "tools/call" over stdio
            └─ audit(tool_id, status, arguments)             always written
```

`_authorize()` is the whole authorization model (`tool_security.py:128-142`).
Order matters, and it is evaluated top to bottom:

| # | Condition | Effect | Persisted? |
| --- | --- | --- | --- |
| 1 | `consent == "deny"` | write `deny`, raise `PermissionError` → 403 | yes |
| 2 | `consent == "always"` | write `allow`, permit | yes |
| 3 | `consent == "once"` | permit | **no** |
| 4 | stored `allow` | permit | — |
| 5 | stored `deny` | raise `PermissionError` → 403 | — |
| 6 | nothing stored | raise `PermissionRequired` → **409** | — |

Implications that are easy to get wrong:

* The **first** call to any tool with `consent: null` always answers **409**, whatever
  its declared risk. A client must catch 409, ask the human, and retry with a
  `consent` value. Rule 3 means `once` is not remembered, so the prompt repeats on
  every call until someone answers `always`.
* `ToolDefinition.risk` and `.requires_confirmation` are **not consulted** by
  `_authorize()`. They exist, are serialized to the client by `public()`, and are
  otherwise inert. See [G5](#g5--risk-and-requires_confirmation-are-dead-metadata).
* `consent == "always"` writes an unconditional `allow` for the tool id. The
  `tool_permissions` table stores only `(tool_id, decision, updated_at)` — there is
  no record of *who* approved it, from which UI, or with which arguments.
* `PermissionRequired` is a `RuntimeError` subclass, so the ordering of the
  `except` clauses in `main.call_tool()` is load-bearing: the specific handlers must
  stay above the generic `(OSError, RuntimeError, ValueError) → 422` one.
* The `ToolCall` model constrains consent server-side with
  `pattern="^(once|always|deny)$"` (`main.py:165-167`); an unexpected value is a
  pydantic 422 before the handler runs.

### Registry and identifiers

`ToolRegistry` is an in-memory dict keyed by tool id
(`tool_registry.py:24-66`). Ids are namespaced:

* built-in: `local:file.read`
* MCP: `mcp:{server_id}:{tool_name}` (`register_mcp_tools`, line 43)

Every MCP tool is registered with `risk="sensitive"` and
`requires_confirmation=True` hardcoded (`tool_registry.py:49-50`) because the
server-declared schema carries no trust signal. `register()` rejects any risk value
outside `{read, write, network, sensitive}`. Registering a server replaces its
previous tools, and `remove_server()` drops them on disconnect — so the registry
reflects **connected** servers only, while `GET /api/v1/mcp/servers` reports
`connected` by looking at `mcp_manager.clients`.

## 5. MCP client contract

`MCPClient` speaks newline-delimited JSON-RPC over stdio with a hand-rolled
protocol version pinned at `PROTOCOL_VERSION = "2025-06-18"`.

* `start()` spawns the child, injects `NEXUS_MCP_SERVER_ID` into a copy of the
  environment, sends `initialize`, then `notifications/initialized`, then
  `tools/list`. The `initialize` **result is discarded** — server capabilities and
  the echoed protocol version are never validated.
* `request()` holds a single `asyncio.Lock` for the whole exchange and reads until
  it finds a matching `id`, discarding anything else. All traffic to one server is
  therefore serialized, and notifications are silently dropped.
* Every read has a hard `REQUEST_TIMEOUT` (15 s) `asyncio.wait_for`. There is no
  retry and no reconnect: after a timeout the client stays in `manager.clients`, so a
  caller must disconnect and connect again. The `TimeoutError` that surfaces quotes
  the tail of the server's stderr, where the reason usually is.
* `start()` spawns a reader for the child's stderr and keeps its last 40 lines
  (`mcp_client.py:106-135`); `stop()` lets it reach EOF before dropping the process
  (`mcp_client.py:137-147`). A pipe nobody reads fills up, and the child then blocks
  in `write(2)` in the middle of a conversation.
* `stop()` closes stdin first (even when the child already exited — a comment in the
  source ties this to Windows proactor cleanup), then `terminate()`, waits 3 s, then
  `kill()`.
* `MCPManager` exposes `connect()`, `disconnect()` and `shutdown()`
  (`mcp_client.py:215-274`). `connect()` replaces an existing client for the same id
  and stops the old one; on a failed start it stops the half-built client before
  re-raising. `shutdown()` empties `clients` first, then stops the children
  concurrently and drops every server's tools — see
  [section 9.1](#91-shutdown-path-mcpmanagershutdown-and-the-lifespan).

## 6. HTTP surface

No route is authenticated. `README.md` states this outright and tells operators to
keep the bind address on `127.0.0.1`. CORS allows only the backend's own
`http://<host>:<port>` and `http://localhost:<port>` origins with
`Content-Type`/`Authorization` headers.

Tool and MCP routes (`main.py:599-665`):

| Method and path | Action | Failure mapping |
| --- | --- | --- |
| `GET /api/v1/tools` | registry dump via `public()` | — |
| `POST /api/v1/tools/{tool_id}/call` | `ToolExecutor.execute()` | 404 unknown id · 409 confirmation required · 403 denied or out of scope · 422 execution error |
| `GET /api/v1/tools/audit` | newest audit rows, `limit` 1–500 | — |
| `GET /api/v1/tools/filesystem-scopes` | resolved scope list | — |
| `POST /api/v1/tools/filesystem-scopes` | add a scope, 201 | 422 unless the path is an existing directory |
| `GET /api/v1/mcp/servers` | stored configs + `connected` flag | — |
| `POST /api/v1/mcp/servers` | upsert config, 201 | — |
| `POST /api/v1/mcp/servers/{id}/connect` | spawn and register tools | 404 missing or disabled · 502 spawn or protocol failure |
| `DELETE /api/v1/mcp/servers/{id}/connection` | `disconnect()`, 204 | — |

Everything else in `main.py` is provider, conversation, document, memory, settings
and health plumbing: `GET /` and `/health` (577, 582), settings and actions
(588, 594), documents (668–704), memories (711–770), preferences and providers
(777–802), conversations (812–837), `/health/provider` (844), `POST /chat` (857)
and `POST /chat/stream` (895).

`POST /chat` builds a prompt (identity, memories, documents, `/web` research,
actions), forwards a plain chat-completion body and returns text.
`_model_payload()` (`main.py:458-482`) sends only `model`, `messages`,
`max_tokens`, `temperature` and `stream` — **no `tools`, no `tool_choice`**. Tool
execution is strictly a separate, human-driven HTTP call.

## 7. Security boundary: enforced vs. assumed

| Control | Enforced where | Real scope |
| --- | --- | --- |
| Per-tool consent | `_authorize()` | every tool, but only as a stored allow/deny per tool id |
| Filesystem scopes | `_safe_file()` | **`local:file.read` only** |
| Size and encoding cap | `execute()` | `local:file.read` only, 1 MB, lossy UTF-8 |
| Argument redaction | `redact()` | audit rows only, exact key match against `SENSITIVE_KEYS`, case-insensitive |
| Audit trail | `audit()` | all four terminal states: `allowed`, `confirmation_required`, `denied`, `error` |
| OS-level sandbox | — | **none**; an MCP server runs with the backend's full user privileges |
| Authentication | — | **none** on any route |

The scopes table is a *policy store that one function reads*. `POST
/api/v1/tools/filesystem-scopes` accepts any existing directory, and MCP tools
never consult it. Adding a scope therefore does not constrain a third-party MCP
server in any way; it only widens what the built-in reader may touch.

Because there is no authentication, `POST /api/v1/mcp/servers` plus `.../connect`
is, from the operating system's point of view, an arbitrary-process-launch endpoint
for anything that can reach the port. The documented mitigation is the loopback
bind address; do not widen `NEXUS_BACKEND_HOST` without re-reading
[SECURITY.md](../SECURITY.md) and [PRIVACY.md](PRIVACY.md).

## 8. Verified gaps

Findings, not TODOs. Each was confirmed against the source in this working tree.

### G1 — no application shutdown hook (closed)

**Closed.** `main.py:45-49` defines an `@asynccontextmanager` lifespan that awaits
`mcp_manager.shutdown()` after yielding, and `app` receives it through
`lifespan=lifespan` (`main.py:52-57`). A backend that exits cleanly now stops every
MCP server it started, instead of leaving each one running as an orphan — typically
`node`/`npx` holding a port or a stdin pipe.

The path that reaches `MCPClient.stop()` is no longer only `MCPManager.disconnect()`;
the shutdown event is a second one. What still bypasses it is a crash, a kill, or the
launcher's `terminate()` — that is [G3](#g3--the-launcher-kills-the-backend-with-terminate-closed).

### G2 — `MCPManager` had no shutdown path (closed)

**Closed.** `MCPManager.shutdown()` exists (`mcp_client.py:188-214`). The manager
still has no `stop()`, deliberately: `MCPClient.stop()` reaps one child, and giving
the manager the same verb invites the `await mcp_manager.stop()` call that used to
raise `AttributeError` at the worst possible moment.

### G3 — the launcher kills the backend with `terminate()` (closed)

**Closed for the leak, open for the etiquette.** `terminate()` is still
`TerminateProcess()` and still skips every Python-level cleanup — that part cannot be
fixed from outside. It no longer decides who survives: `run_nexus.py` keeps both
children in a kill-on-close job object (`backend/process_job.py`), so closing its
handle makes the OS terminate the gateway, the desktop client and every MCP server the
gateway started, whether the launcher exited, crashed or was killed outright.
`tests/test_process_job.py` spawns a grandchild the test never touches and asserts
that it dies when the job closes.

What remains: when a backend was already listening, the launcher never owned it
(`backend_process` stays `None`), so it is not in the job and nothing stops it.

### G4 — the child's stderr is never drained (closed)

**Closed.** `start()` now runs a reader for the pipe to EOF and keeps the last 40
lines; a request that times out quotes them. The reading is the part that mattered: an
OS pipe holds a few dozen kilobytes, so a server that logs to stderr blocks in
`write(2)` and the conversation stalls behind its own noise. `DEVNULL` would also have
emptied the pipe, at the cost of never learning why a server died.

### G5 — `risk` and `requires_confirmation` are dead metadata

`ToolDefinition` carries both fields and `public()` ships them to clients, but
`_authorize()` never reads them: the decision depends only on the `consent` argument
and the stored row. A UI that colours tools by risk is displaying decoration, not
policy. See section [7](#7-security-boundary-enforced-vs-assumed).

### G6 — scopes do not contain MCP tools

Covered in section 7. Enlarging a scope is a strictly widening operation for one
built-in tool.

### G7 — the tool surface has no client

No file under `frontend/` references `/api/v1/tools` or `/api/v1/mcp`. The routes
are exercised only by `tests/test_tools.py` and a manual HTTP client, and no caller
handles the 409 retry. The subsystem is complete on the server side and unreachable
from the product today.

### G8 — `config.py` docstring contradicts the code

The docstring claims the project avoids a mandatory dotenv dependency; the module
imports and calls `load_dotenv()` at line 15. Either the docstring or the import
should change; do not infer dotenv behaviour from the comment.

### G9 — one lock, one timeout, no recovery

Per-client serialization plus the fixed 15 s timeout means a slow tool call blocks
every other call to the same server, and a timed-out client is never restarted or
reaped automatically.

### G10 — noisy repository scans

`search_codebase` results are dominated by `.pytest-tmp/`, `.pytest_cache/` and
`tmp/` fixtures that contain `settings.json`-like files. `.pytest-tmp` is already in
`check_public_repo.FORBIDDEN_DIRS`. Filter paths when grepping, or scope the search
to `backend/` and `frontend/`.

## 9. Closing the lifecycle gaps

Four edits over two passes. The first gave the gateway a way to stop its own
children; the second contained the whole process tree and emptied the pipe it was
blocking on. Every one of them is pinned by a test named in
[section 9.4](#94-tests).

### 9.1 Shutdown path: `MCPManager.shutdown()` and the lifespan

Two edits, in this order.

```python
# backend/mcp_client.py:248 — MCPManager owns the shutdown path.
    async def shutdown(self) -> None:
        """Stop every connected client and drop its tools from the registry."""
        clients = list(self.clients.items())
        # Drop the references first: a stop that raises must not leave a client
        # behind that a later connect() would treat as still live.
        self.clients.clear()
        results = await asyncio.gather(
            *(client.stop() for _, client in clients),
            return_exceptions=True,
        )
        for (server_id, _), result in zip(clients, results, strict=True):
            if isinstance(result, BaseException):
                print(
                    f"MCP server '{server_id}' did not stop cleanly: {result!r}",
                    file=sys.stderr,
                    flush=True,
                )
            self.registry.remove_server(server_id)
```

```python
# backend/main.py:45 — defined above the app so the name exists at construction.
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Reap MCP children spawned by this process before it exits."""
    yield
    await mcp_manager.shutdown()


app = FastAPI(
    title="Nexus Local API",
    description="Local gateway for the Nexus desktop command center.",
    version="0.3.0-beta.2",
    lifespan=lifespan,
)
```

Three decisions inside `shutdown()`. Sequential `disconnect()` calls would add
`MCPClient.stop()`'s three-second wait to every exit for each wedged server, so the
stops run concurrently under `asyncio.gather(..., return_exceptions=True)`. Clearing
`clients` first keeps the handler total and leaves no client that a later `connect()`
could mistake for live. `registry.remove_server()` still runs for a server whose stop
raised, so no phantom tool survives. `main.py` gained `asynccontextmanager` in its
imports; the handler ignores the app it is handed, hence the `_`.

### 9.2 Containment: a kill-on-close job object

`terminate()` cannot be made graceful from outside, so the launcher stopped relying on
it to reap anything. `backend/process_job.py` wraps `CreateJobObjectW` and
`SetInformationJobObject` with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`; the launcher
assigns every child it starts, and its `finally` block releases the job:

```python
# run_nexus.py:142 — opened before the children, closed after them.
job = ProcessJob()
...
    job.assign(backend_process)
...
finally:
    _stop(frontend_process)
    _stop(backend_process)
    job.close()  # the OS terminates every member still running
```

Windows places a new process in its creator's job, so the MCP servers the gateway
starts later join the same job without the launcher ever learning they exist. Closing
the last handle terminates every member whether the launcher exited, crashed or was
killed outright — the last case being exactly the one a polite stop request cannot
cover.

Two findings from wiring it up:

* A process handle opened by pid with only `PROCESS_SET_QUOTA | PROCESS_TERMINATE`
  was refused here with error 5, while the handle `subprocess` already holds was
  accepted, so `assign()` reuses that one and only falls back to `OpenProcess`.
* Shells on this machine already run inside a job, and nesting the Nexus job under it
  still worked, which matters because CI agents and terminals bring jobs of their own.

A `POST /api/v1/shutdown` was considered and rejected: the API is unauthenticated, so
such a route hands every local process a way to stop the app, and it would still not
survive `taskkill /F`. Containment was both smaller and stronger.

### 9.3 Draining the child's stderr

`start()` hands the pipe to a reader task, and `stop()` lets it finish before dropping
the process:

```python
# backend/mcp_client.py:86 — started with the child, awaited by stop().
self._stderr_task = asyncio.create_task(self._drain_stderr(self.process))
```

The reader consumes chunks rather than lines and keeps `stderr_tail` to the last 40
entries. A chunk boundary can split a line, which is cosmetic; a line longer than the
stream's limit would abort the reader and re-open the very deadlock this closes. What
the tail is for is the message `request()` raises on a timeout:

```python
except TimeoutError as exc:
    raise TimeoutError(
        f"'{self.config.id}' sent nothing for {REQUEST_TIMEOUT:.0f}s. "
        f"stderr: {self.recent_stderr() or 'empty'}"
    ) from exc
```

### 9.4 Tests

| Test | Locks down |
| --- | --- |
| `test_manager_shutdown_reaps_every_connected_server` | both children exit, the registry empties, a second `shutdown()` is harmless |
| `test_manager_shutdown_stops_the_rest_when_one_child_is_wedged` | a client that raises in `stop()` neither escapes nor aborts the others |
| `test_app_lifespan_reaps_connected_mcp_servers` | the app is wired to `lifespan`, and the child is gone once it exits |
| `test_a_chatty_stderr_server_still_answers` | two megabytes on stderr no longer stall the handshake, and the tail survives `stop()` |
| `test_a_silent_server_reports_what_it_written_to_stderr` | the timeout text carries the server's own marker line |
| `test_closing_the_job_reaps_a_grandchild_that_was_never_touched` | closing the job kills a grandchild nothing else touched |

The first three drive `tests/fixtures/fake_mcp_server.py`; the stderr pair drives
`tests/fixtures/noisy_mcp_server.py`, which either floods the pipe or logs once and
then refuses to answer; `tests/test_process_job.py` needs a real Windows job and skips
elsewhere.

None of this touches G5-G10, and the launcher still does not own a backend it found
already listening.

## 10. Working rules for the repository

Gate commands, matching `.github/workflows/ci.yml` on Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts\check_public_repo.py
```

Documentation rules enforced by `scripts/check_public_repo.py`:

* Every inline Markdown link in any `.md` file must resolve to a file inside the
  repository that is also visible to `git ls-files`. Broken or escaping links fail CI.
* Content inside triple-backtick fences is **not** link-checked, which is why the
  diagrams above live in fences.
* Anything listed in `docs/languages.json` must exist in both languages and each
  file must link to its counterpart. Adding a pair is a commitment to maintain two
  files; this document is deliberately **not** a pair, per the technical-record note
  in [INDEX.md](INDEX.md).
* `settings.json`, `mcp_servers.json`, `last_debug.json`, `.env*` (except
  `.env.example`), databases, logs, model files and recordings are unpublishable;
  never add a link that points at one of them.

Code rules worth knowing before the first patch:

* Tests must not depend on the real data directory; `ToolSecurityStore` and the
  repositories all take an explicit `path` argument, and the suite relies on it.
* `NEXUS_DATA_DIR` overrides every data path if you need a scratch directory.
* The singletons in section 2 are shared across tests in one process — reset
  `tool_registry` and `mcp_manager.clients` in fixtures rather than assuming a clean
  import.
* User-facing text is Turkish in code and partially translated to English; see
  [CONTRIBUTING.md](../CONTRIBUTING.md) before adding strings.

## 11. Verification log

How each finding was derived, so it can be re-checked instead of trusted:

| Finding | Method |
| --- | --- |
| G1 | Regex sweep for `FastAPI(`, `lifespan`, `on_event`, `@asynccontextmanager` across the repository: one hit, the constructor itself |
| G2 | Read of `MCPManager`; regex for `mcp_manager.(stop|start|initialize)`: no hits |
| G3 | Read of `run_nexus.py` `_stop()` and the `finally` block in `main()` |
| G4 | Read of `MCPClient.start()`; no reader exists for `process.stderr` |
| G5 | Read of `_authorize()` next to the `ToolDefinition` dataclass |
| G6 | `execute()` calls `_safe_file()` only under `tool_id == "local:file.read"` |
| G7 | Regex for `api/v1/tools` and `api/v1/mcp`: backend definitions only, zero frontend callers |
| G8 | Read of `config.py` docstring against its `load_dotenv()` call |
| G1/G2 fix | `pytest` and `ruff check .` clean; the tests in [section 9.4](#94-tests) each assert the child process has actually exited |
| G3 fix | Measured before coded, with a throwaway probe: this process already runs inside a job, assignment through the handle `subprocess` owns succeeded where one opened by pid with `PROCESS_SET_QUOTA` and `PROCESS_TERMINATE` returned error 5, and closing the job handle ended a grandchild nothing had touched |
| G4 fix | `tests/fixtures/noisy_mcp_server.py` writes about 2 MB to stderr before it serves anything; remove the reader and the handshake stops answering, which is the failure this closes |

Related: [INDEX.md](INDEX.md) for the document set,
[AGENTS.md](../AGENTS.md) for the short agent brief,
[tests/test_tools.py](../tests/test_tools.py) for executable behaviour,
[PRIVACY.md](PRIVACY.md) for the network boundary.




