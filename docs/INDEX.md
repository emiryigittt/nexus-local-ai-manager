# Documentation / Belgeler

Choose your language. English is the global entry point; Turkish is maintained
alongside it. Dilini seç: İngilizce global giriş, Türkçe eş belgelerle desteklenir.

| Topic / Konu | English | Türkçe |
| --- | --- | --- |
| Windows installer beta / Windows kurulum betası | [Release notes](releases/v0.3.0-beta.3.md) | [İki dilli sürüm notları](releases/v0.3.0-beta.3.md#türkçe) |
| First source beta / İlk kaynak kod betası | [Release notes](releases/v0.3.0-beta.1.md) | [İki dilli sürüm notları](releases/v0.3.0-beta.1.md#türkçe-başlangıç) |
| Introduction and setup / Tanıtım ve kurulum | [README](../README.md) | [README](../README.tr.md) |
| Windows installer preview / Windows kurulum önizlemesi | [Build and use](WINDOWS_PREVIEW.md) | [Kurulum ve kullanım](WINDOWS_PREVIEW.tr.md) |
| Usage and troubleshooting / Kullanım ve sorun giderme | [Guide](USER_GUIDE.md) | [Rehber](USER_GUIDE.tr.md) |
| Identity and introduction / Kimlik ve tanışma | [Meet Nexus](IDENTITY.md) | [Nexus ile tanış](IDENTITY.tr.md) |
| Privacy / Gizlilik | [Boundaries](PRIVACY.md) | [Sınırlar](PRIVACY.tr.md) |
| Contributing / Katkı | [Contributing](../CONTRIBUTING.md) | [Katkı](../CONTRIBUTING.tr.md) |
| Security reporting / Güvenlik bildirimi | [Security](../SECURITY.md) | [Güvenlik](../SECURITY.tr.md) |
| Community conduct / Topluluk davranışı | [Conduct](../CODE_OF_CONDUCT.md) | [Kurallar](../CODE_OF_CONDUCT.tr.md) |
| Third-party notices / Üçüncü taraf notları | [Notices](../THIRD_PARTY_NOTICES.md) | [Notlar](../THIRD_PARTY_NOTICES.tr.md) |
| First tasks / İlk görevler | [Briefs](GOOD_FIRST_ISSUES.md) | [Taslaklar](GOOD_FIRST_ISSUES.tr.md) |
| GitHub from scratch / Sıfırdan GitHub | [Setup](GITHUB_SETUP.md) | [Kurulum](GITHUB_SETUP.tr.md) |
| Community launch / Topluluk yayını | [Plan](GITHUB_LAUNCH_PLAN.en.md) | [Plan](GITHUB_LAUNCH_PLAN.md) |
| Demo recording / Demo çekimi | [Storyboard](DEMO_SCRIPT.md) | [Çekim planı](DEMO_SCRIPT.tr.md) |
| Launch copy / Tanıtım metinleri | [Drafts](LAUNCH_COPY.md) | [Taslaklar](LAUNCH_COPY.tr.md) |
| Prepared launch package / Hazırlanan tanıtım paketi | [Package](LAUNCH_PACKAGE.md) | [Paket](LAUNCH_PACKAGE.md) |
| First-user feedback / İlk kullanıcı geri bildirimi | [Form](PILOT_FEEDBACK.md) | [Form](PILOT_FEEDBACK.md) |
| Voice and memory evidence / Ses ve hafıza kanıtları | [Report](VOICE_AND_MEMORY_RELIABILITY.en.md) | [Rapor](VOICE_AND_MEMORY_RELIABILITY.md) |
| New launch kit / Yeni tanıtım kiti | [Kit](COMPANION_LAUNCH.md) | [Paket](COMPANION_LAUNCH.tr.md) |

The [synthetic demo fixture](demo/project-brief.md) includes both languages.
[Örnek demo belgesi](demo/project-brief.md) iki dili aynı dosyada içerir.

[Logo and visual identity / Logo ve görsel kimlik](BRAND.md) is bilingual / iki dillidir.

The interface supports English and Turkish. The main window, settings, memory, history,
About, clipboard consent, voice status, tray menu and error messages follow
**Settings → General → Language**; the first-run wizard, the introduction and local
speech setup keep their own bilingual copy. Answers, saved memory text and user input
are never translated. Documentation translation does not mean full application
localization.
Arayüz Türkçe ve İngilizceyi destekler. Ana pencere, ayarlar, hafıza, geçmiş, hakkında,
pano izni, ses durumu, sistem tepsisi menüsü ve hata mesajları
**Ayarlar → Genel → Dil** seçimini izler; karşılama sihirbazı, tanışma ve yerel ses
kurulumu kendi çift dilli metinlerini kullanır. Yanıtlar, kayıtlı hafıza metinleri ve
kullanıcı girdisi çevrilmez; belge çevirisi tüm uygulamanın çevrildiği anlamına gelmez.

Technical working records remain in their original language:
[architecture map](ARCHITECTURE.md) for agents and maintainers,
[Roadmap](../ROADMAP.md), [changelog](../CHANGELOG.md),
[AI reliability history](AI_RELIABILITY.md), [UI design](UI_DESIGN.md) and the
[pre-publication checklist](PREPUBLICATION_CHECK.md).
Teknik çalışma kayıtları özgün dilindedir; bu sayfa onların tam çevirisini vaat etmez.

## Maintaining translations / Çevirileri sürdürme

Update paired documents together, especially permissions, installation, limitations,
numbers and release status. `languages.json` lists the maintained pairs; the publication
check verifies file presence and reciprocal language links, not translation accuracy.

Eş belgeleri birlikte güncelle; özellikle izinler, kurulum, sınırlamalar, sayılar ve
yayın durumu eşleşmeli. `languages.json` eşleri listeler; yayın kontrolü dosyaları ve
karşılıklı dil bağlantılarını doğrular, çeviri doğruluğunu değil.

## Gate status / Kapı durumu

Measured on 4 November 2026 in this working tree / bu çalışma ağacında ölçüldü:

| Check / Kontrol | Result / Sonuç |
| --- | --- |
| Publication gate findings (`scripts/check_public_repo.py`) / Yayın kapısı bulguları | 0 findings / 0 bulgu |
| Collected tests / Toplanan testler | 415 tests in 43 files / 43 dosyada 415 test |
| Localhost routes in `backend/main.py` / Yerel ağ rotaları | 35 (17 GET, 11 POST, 4 DELETE, 2 PUT, 1 PATCH) |
| Registered built-in tools / Kayıtlı yerleşik araçlar | 1 static (`local:file.read`); MCP tools register dynamically / MCP araçları dinamik kaydolur |
| Built-in safe actions / Yerleşik güvenli eylemler | 5 |
| Maintained bilingual pairs in `docs/languages.json` / İki dilli belge çifti | 17 |
| Links resolved from this page / Bu sayfadan çözümlenen bağlantı | 49 links, 46 unique targets / 49 bağlantı, 46 benzersiz hedef |

Only the gate result binds a release; the other rows move with the code and must be
re-measured before they are quoted elsewhere.
Yayın için yalnızca kapı sonucu bağlayıcıdır; diğer satırlar kodla birlikte değişir ve
başka bir yerde alıntılanmadan önce yeniden ölçülmelidir.

