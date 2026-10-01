# Prepared launch package / Hazırlanan tanıtım paketi

30 September 2026 / 30 Eylül 2026. Prepared locally; no social posts sent.
Yerelde hazırlandı; sosyal paylaşım gönderilmedi.

## Contents / İçerik

The 1 October top-strip/RGB/character/memory refresh has a newer
[launch kit and copy](COMPANION_LAUNCH.md) / [tanıtım paketi ve metinler](COMPANION_LAUNCH.tr.md),
including 36-second portrait/landscape videos with original audio. The files below
describe the earlier 30 September package.

- Two silent MP4 teasers: English and Turkish, 48 seconds, 1600×900, 24 fps, H.264.
- Matching SRT captions and six scene-review PNGs per language.
- [English posts and invitations](LAUNCH_COPY.md) / [Türkçe paylaşım ve davetler](LAUNCH_COPY.tr.md).
- [Bilingual feedback form / İki dilli geri bildirim formu](PILOT_FEEDBACK.md).

Rendered media lives locally in output/launch, which is excluded from Git.
Reproduce with scripts/render_launch_video.py using the existing environment
with PyQt6, numpy and PyAV. No additional app runtime dependency was added.

Üretilen medya yerelde output/launch klasöründe; Git'ten hariç tutuldu.
scripts/render_launch_video.py mevcut PyQt6/numpy/PyAV ortamıyla yeniden üretir.
Uygulamaya yeni çalışma zamanı bağımlılığı eklenmedi.

## What the videos show / Videoların kapsamı

Reviewed actual application screenshots with fictional sample content, composed
into a labelled interface teaser. No live model inference, microphone capture or
speech synthesis was recorded. The persistent label and attachment captions
state that clearly. Do not present it as a live demo or speed benchmark.

İncelenmiş gerçek uygulama görüntülerinde yapay örnek içerik gösteriliyor.
Sürekli etiketli bir arayüz tanıtımıdır. Canlı model çıkarımı, mikrofon kaydı veya
ses sentezi kaydedilmedi. Canlı demo veya hız ölçümü olarak sunma.

A live model server was unavailable during preparation. The
[real recording brief](DEMO_SCRIPT.md) / [gerçek çekim planı](DEMO_SCRIPT.tr.md)
remains available for document answers, approved-memory recall and real speech.
Use isolated test data and the fictional fixture when the server is available.

Hazırlık sırasında yerel model sunucusu kapalıydı. Sunucu açılınca gerçek belge
yanıtını, onaylı hafızayı hatırlamayı ve sesi ayrı test verileriyle kaydetmek gerekiyor.

## First pilot / İlk deneme grubu

Planning targets: ten volunteers, five completed installations, three repeat users.
Share the matching-language video and invitation selectively, and collect setup
and document-task feedback before a wider launch. These are targets, not results.

Plan hedefi: on gönüllü, beş tamamlanan kurulum, üç tekrar kullanıcı.
İlgili dilde video ve daveti küçük bir grupla paylaş; geniş yayından önce kurulum
ve belge görevi geri bildirimlerini topla. Bunlar hedef, ölçülmüş sonuç değil.
