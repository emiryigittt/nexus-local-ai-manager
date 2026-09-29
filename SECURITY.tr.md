# Güvenlik politikası

[English](SECURITY.md) · **Türkçe** · [Belgeler](docs/INDEX.md)

## Güvenlik açığı bildirme

Açık ayrıntılarını herkese açık issue'ya yazma. Depo sahibi etkinleştirdikten sonra
**Security** sekmesindeki özel açık bildirimini kullan. Yerel hazırlık bu kanalı
açmadı veya GitHub deposu oluşturmadı. Kanal yoksa saldırı ayrıntısı, anahtar veya
kişisel veri paylaşmadan özel iletişim kanalı iste. Çalışan kanal, yayın koşuludur.
Özel rapora tekrar adımlarını, etkilenen sürümleri, etkiyi ve varsa düzeltme önerisini ekle.

Bildirimlere mümkün olduğunca hızlı dönüş hedeflenir; belirli yanıt süresi taahhüdü
yoktur. Ayrıntıları yayımlamadan önce düzeltme ve koordineli duyuru için zaman tanı.

## Kapsam ve varsayılanlar

Nexus API'si varsayılan olarak `127.0.0.1` üzerinde çalışır ve bu yerel API için
anahtar istemez. Portu güvenilmeyen ağa açma. Sağlayıcı anahtarları Git dışında
tutulan `.env` dosyasında olmalıdır.

Yerel adres ve CORS, kimlik doğrulama veya süreç yalıtımı değildir. Başka yerel
programlar API'ye ulaşabilir. API kimlik doğrulaması tamamlanmış özellik değil,
açık geliştirme işidir. SQLite şifrelenmez; araç izinleri üçüncü taraf MCP
süreçlerini işletim sistemi düzeyinde yalıtmaz.

`/web` ve isteğe bağlı Edge sesi üçüncü taraflarla iletişim kurar. Hassas veriler
için kullanmadan önce [gizlilik sınırlarını](docs/PRIVACY.tr.md) incele.
Şu an yalnızca mevcut geliştirme dalı sürdürülür; desteklenen kararlı sürüm serisi yoktur.
