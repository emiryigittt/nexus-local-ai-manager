# Desktop interface refresh

The main window prioritizes the conversation instead of presenting every capability
as an equally prominent icon. This is an implemented PyQt interface, not a mockup.

- Header: Nexus identity, new conversation, history, settings, and hide.
- Welcome: a short invitation and three practical starting points.
- Composer: full-width input, attach, research, Tools, microphone, and send.
- Tools: private session, knowledge-grounded answers, response speech, and memory.
- Response: persistent prompt context, copy, and paragraph/list spacing.
- Footer: local/cloud/private disclosure and bounded provider/status text. Wake controls
  remain visible when wake consent is enabled, including during background listening.

Graphite surfaces, warm text, a restrained mint accent, and drawn line icons replace
the purple icon-heavy header. Icons no longer depend on emoji/symbol font availability.
Provider names and errors are elided visually but remain available as tooltips.

Settings has General, Privacy, and Voice tabs; Save/Cancel stays outside scroll areas.
No permission defaults were loosened. Tab and Shift+Tab navigate controls; clipboard
inspection moves to Ctrl+Shift+V. Enter and the send button use the same request path.

## Verification

### 27 September refinement

The implemented desktop now uses a left-aligned welcome, small action cards with
descriptions/shortcut hints, an input-adjacent send button and a visible focus border.
Cards are real buttons reachable by keyboard; their labels follow saved UI language.
The decorative welcome identity row yields space below 600 px window height, avoiding
clipped actions. The local/cloud/private disclosure remains in the footer.

General and Privacy use grouped cards. Voice has Input, Hey Nexus and Response voice
sections rather than one long form; values and permission choices survive section
switches without being saved. Save/Cancel remains outside scrolling content. Voice
controls support EN/TR; this does not claim all application errors/dialogs are translated.

254 automated tests and Ruff passed. EN/TR welcome, response, settings and voice pages
were rendered from synthetic content; 640x560 main and 560x600 settings previews were
also inspected. A compact-card clipping issue found visually was corrected and the
test now checks parent bounds, not just the outer window. One UI-subset run had a native
Qt access violation at cleanup; reruns passed after explicit test-window disposal.
Its root cause remains open, as do physical high-DPI and screen-reader validation.

Current previews:

![Refined welcome](assets/localization/en/welcome.png)

![Voice sections](assets/localization/en/voice-wake.png)

### Earlier interface pass

140 automated tests passed, including the existing chat, privacy, voice, and memory
regressions plus five new UI interaction checks. Ruff passed. The known Windows asyncio
pipe-cleanup warning recurred in the final full run; it remains tracked in the roadmap.
Welcome, response, and
all three settings tabs were rendered and visually inspected with temporary settings,
no network calls, and no microphone access. Preview response content is synthetic.

```powershell
.\venv\Scripts\python.exe scripts\preview_ui.py --output docs/assets/ui-refresh
```

The preview tool explicitly loads local Windows fonts when the offscreen Qt platform
cannot discover them. It does not alter installed fonts or live application settings.
Offscreen previews do not prove native high-DPI behavior or screen-reader compatibility;
those checks and user preference feedback remain open.

![Welcome](assets/ui-refresh/welcome.png)

![Response](assets/ui-refresh/response.png)
