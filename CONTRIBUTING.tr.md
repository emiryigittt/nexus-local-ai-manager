# Nexus'a katkı

[English](CONTRIBUTING.md) · **Türkçe** · [Belgeler](docs/INDEX.md)

Nexus'u daha kullanışlı hale getirmeye yardımcı olduğun için teşekkürler.
Küçük ve tek konuya odaklanan değişikliklerin incelenmesi daha kolaydır.

## Başlamadan önce

Hata bildirirken Windows/Python sürümünü, model sağlayıcısını, tekrar adımlarını,
beklenen sonucu ve sırları temizlenmiş ilgili kayıtları ekle. Büyük özelliklerde
aynı işin tekrarlanmaması için önce öneri aç. Türkçe ve İngilizce bildirimler kabul edilir.
Yapay örnekler kullan; veritabanını, kişisel kayıtlarını veya tüm ortam değişkenlerini
yükleme. [İlk katkı görevleri](docs/GOOD_FIRST_ISSUES.tr.md), gerçek issue'lar
oluşturulana kadar taslaktır.

## Yerel geliştirme

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe scripts\check_public_repo.py
```

Uygulamayı `.\.venv\Scripts\python.exe run_nexus.py` ile aç. `.env` isteğe bağlıdır;
günlük denemelerde normal ayarları kullan. Otomatik testler yalıtılmış veri kullanır;
çalışan model veya mikrofon istemez. `check_voice`, `check_memory`, `check_wake_word`
araçlarının ek gereksinimleri için [kullanım rehberine](docs/USER_GUIDE.tr.md) bak.

## Pull request kontrolü

1. Tek bir konuya odaklan.
2. Davranış değişikliklerine test ekle/güncelle.
3. Ayar veya kısayol değişirse kullanıcı belgelerini güncelle.
4. `.env`, modeller, erişim anahtarları ve kişisel istem verilerini kaydetme.
5. Test ve kod denetimlerini çalıştır; doğrulamayı nasıl yaptığını açıkla.
6. İki dilde belgeleri tutarlı tut; tüm arayüz çevrilmiş gibi anlatma.
7. Yeni bağımlılık/model lisanslarını ve ağ/gizlilik sınırlarını belgele.

Katkıda bulunarak kendi katkının projenin MIT lisansıyla paylaşılmasını kabul edersin.
Bağımlılık ve model lisansları ayrıdır; [üçüncü taraf notlarını](THIRD_PARTY_NOTICES.tr.md) incele.
