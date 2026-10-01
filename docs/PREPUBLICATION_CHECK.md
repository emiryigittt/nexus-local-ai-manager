# Local publication check / Yerel yayın kontrolü

## 1 October 2026 beta preparation / 1 Ekim 2026 beta hazırlığı

- The local Windows Python 3.12.14 build environment passed 377 tests, Ruff, and
  13 packaged smoke checks. The package used a synthetic HTTP model fixture;
  no real microphone, clean-PC installation or real LLM quality claim follows.
- The earlier Python 3.14 test instability remains open. This beta recommends
  Python 3.11–3.13.
- Source beta publication is gated on all three current Windows CI jobs. The
  publisher pins the tested commit, preserves existing releases/tags, and never
  uploads installers, downloaded models, local outputs or user data.
- Local speech model checks passed without downloading during recording.
  Real-user transcription and wake accuracy still need testing.
- The public beta offers source code only. The local unsigned installer remains
  pending a documented PyQt/Qt distribution decision and dependency review.
- Turkish/English 50-second, 1080×1920, 60 fps promo files were prepared locally.
  They contain original audio and fictional sample UI content, not live inference.
  No social posts or direct invitations were sent.

Türkçe: Yerel Python 3.12.14 ortamında 377 test, Ruff ve 13 paket kontrolü geçti.
Paket testinde kurgu model sunucusu kullanıldı; gerçek mikrofon, model kalitesi
ve temiz bilgisayar kurulumu bu sonuçla doğrulanmıyor. Kaynak kod betası üç
Windows CI işi geçince test edilen commit üzerinden yayımlanır. Kurulum paketi,
modeller ve kullanıcı verileri yüklenmez. Yerel imzasız kurulumun PyQt/Qt dağıtım
kararı ve bağımlılık incelemesi açık. Önceki Python 3.14 sorunu nedeniyle 3.11–3.13
önerilir. İki dilde 50 saniyelik tanıtımlar yerelde hazır; sosyal paylaşım yapılmadı.

## Historical checkpoint / Önceki kontrol kaydı

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
- Hosted CI was pending at the local checkpoint; see the verified follow-up below.

Türkçe: Windows/Python 3.14.7 üzerinde ilk tam test koşusu sonlara doğru yerel
erişim ihlaliyle kesildi. İkinci tam koşuda **262 test 5,49 saniyede geçti**.
Aralıklı çöküş çözülmüş sayılmıyor. Import düzeni düzeltildikten sonra Ruff geçti;
bağımlılık denetimi sorun bulmadı. Belge güncellemeleri öncesindeki yayın denetimi
170 dosyada sıfır bulgu verdi; bu kapsamlı bir sır veya görsel içerik denetimi değil.
Gerçek model/ses ve temiz bilgisayar testleri bu kontrolde tekrarlanmadı.
Yerel kontrol sırasında bekleyen GitHub CI sonucu aşağıda ayrıca doğrulandı.

## GitHub follow-up / GitHub doğrulaması

The source publication commit `2dac660` has the same complete Git tree as the
verified local checkout: `8fba0dacd159a367d18ed9a6417137200dc4410a` (171 files).
[GitHub Actions run 36627956686](https://github.com/emiryigittt/nexus-local-ai-manager/actions/runs/36627956686)
completed successfully on 29 September 2026 for Windows/Python 3.11, 3.12 and 3.13.
Each job passed dependency installation, Ruff, publication preflight and pytest.
This verifies automated CI, not physical microphone/speaker behavior or a manual
clean-PC installation. The intermittent local Python 3.14 crash is still open.

Türkçe: `2dac660` yayın commitinin 171 dosyalık Git ağacı yerel doğrulanmış sürümle
birebir eşleşiyor. Bağlantıdaki GitHub Actions koşusu 29 Eylül 2026'da Windows ve
Python 3.11, 3.12, 3.13 üzerinde başarıyla tamamlandı. Her işte bağımlılık kurulumu,
Ruff, yayın ön denetimi ve pytest geçti. Bu sonuç fiziksel mikrofon/hoparlör veya
temiz bilgisayarda elle kurulum testi yerine geçmez; Python 3.14 çöküşü açık kalıyor.

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
