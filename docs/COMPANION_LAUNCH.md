# New Nexus launch package

**English** · [Türkçe](COMPANION_LAUNCH.tr.md) · [Documentation](INDEX.md)

1 October 2026. Prepared for the new local development preview.
No social posts or new public installer release were made.

The latest promo revision contains Turkish and English **50-second, 1080×1920,
60 fps** videos in the local `output/launch/social-film-v2` folder, with matching
subtitles, covers and `nexus-social-film-v2-tr-en-kit.zip`. It uses original music
and rounded, echoing low-mid effects; the page-sweep sound was removed.
The older 36-second files below are kept for reference.

For the current announcement, link the
[first source beta](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.1).
Say explicitly that Python 3.11–3.13 and a running local model are required;
no public installer is attached. The UI film is not a live model demo.

The local `output/launch` folder contains two 36-second Turkish promos:
`nexus-promo-reels-tr.mp4` (1080×1920) and `nexus-promo-landscape-tr.mp4`
(1920×1080), matching SRT captions, eight scene stills each, scope metadata and
`nexus-companion-launch-kit.zip`. Use portrait for Reels/Shorts and landscape for
YouTube/GitHub presentations. The corresponding Turkish post drafts are linked above.

Actual Qt animations show the top strip, hover preview, chat, RGB/cat choices and
local memory approval. Desktop wallpaper is illustrative; model responses and voice
states are fictional and disclosed on every frame. Audio is original synthesized
music and Nexus chimes. Do not describe it as live inference or a speed benchmark.

Reproduce using `python -m scripts.render_companion_promo`, optionally `--landscape`,
in the existing Qt/PyAV/NumPy preview environment. These are optional media tools;
no new application runtime dependency was introduced.

## Ready-to-use English caption

Meet Nexus: a little local AI companion at the top of your Windows screen.

Hover for tools. Click for chat. Choose your RGB accent, mini bot or cat, and
optional interface sounds. Review and approve what it remembers.

Connect your running Ollama, LM Studio or llama.cpp model server.
The new interface is a development preview; this video uses sample content and states.

Follow the project: https://github.com/emiryigittt/nexus-local-ai-manager

#Nexus #LocalAI #Ollama #Windows

Start with a small pilot of 5–10 volunteers and collect feedback on panel usefulness,
discoverability of appearance choices and memory editing. Then test real model and
voice workflows. The local installer needs no Python but still needs a separate model
server. Do not imply that a signed public installer has already been released.
Check the destination community's current posting rules before sharing.
