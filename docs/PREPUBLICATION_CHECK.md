# Local publication check / Yerel yayın kontrolü

29 September 2026 / 29 Eylül 2026

## Verification / Doğrulama

- Windows, Python 3.14.7, existing `venv` environment.
- First full pytest run ended with a native access violation near the end of the
  suite. A subsequent full run completed: **262 passed in 5.49 seconds**, exit 0.
  The intermittent crash remains unresolved; a passing retry is not a fix.
- Ruff passed after correcting import formatting in `frontend/motion.py`.
- `pip check`: no broken requirements in the tested environment.
- Publication preflight passed before these documentation edits: 170 Git-visible
  files, zero findings. The checker covers selected private-file patterns, common
  credential formats, file sizes, language-pair links and local Markdown links.
  It is not an exhaustive secret audit or a review of image contents.
- No fresh model, microphone, speaker or clean-machine installation test was run.
- Hosted Windows/Python 3.11–3.13 CI still needs to run after upload.

Türkçe: Windows/Python 3.14.7 üzerinde ilk tam test koşusu sonlara doğru yerel
erişim ihlaliyle kesildi. İkinci tam koşuda **262 test 5,49 saniyede geçti**.
Aralıklı çöküş çözülmüş sayılmıyor. Import düzeni düzeltildikten sonra Ruff geçti;
bağımlılık denetimi sorun bulmadı. Belge güncellemeleri öncesindeki yayın denetimi
170 dosyada sıfır bulgu verdi; bu kapsamlı bir sır veya görsel içerik denetimi değil.
Gerçek model/ses ve temiz bilgisayar testleri bu kontrolde tekrarlanmadı.
GitHub CI yükleme sonrasında ayrıca doğrulanmalı.

## Repository presentation / Depo sunumu

Repository / Depo: [nexus-local-ai-manager](https://github.com/emiryigittt/nexus-local-ai-manager)

Suggested About description / About açıklaması:

> Local-first AI desktop assistant for Windows with Ollama, LM Studio, documents,
> voice and user-controlled memory.

Suggested topics / Konu etiketleri:

`local-ai`, `ai-assistant`, `desktop-assistant`, `ollama`, `lm-studio`, `llama-cpp`,
`windows`, `python`, `pyqt6`, `voice-assistant`, `rag`

These metadata are prepared for the repository; this document does not confirm
they have been applied. Relevant topics help people find related repositories;
they do not guarantee search rank, stars or Trending placement.
[GitHub topic documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).

Bu metadata depo için hazırlandı; bu belge GitHub'a uygulandığını doğrulamaz.
İlgili etiketler keşfedilmeyi destekler; sıralama, yıldız veya Trending garantisi yok.

Next priorities / Sonraki öncelikler: hosted CI, clean Windows setup, intermittent
native-crash investigation, a real demo with synthetic content, and a small pilot.
GitHub CI, temiz Windows kurulumu, aralıklı yerel çöküşün araştırılması, örnek
içerikle gerçek demo ve küçük bir pilot önceliklidir.
