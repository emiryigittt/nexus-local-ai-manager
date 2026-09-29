# Nexus kullanım rehberi

[English](USER_GUIDE.md) · **Türkçe** · [Belgeler](INDEX.md)

Kurulum için [Türkçe başlangıca](../README.tr.md#başlangıç) bak. Etiketler mevcut
Türkçe arayüzle eşleşir. Ortam değişkenlerini değiştirmek yerine normal uygulama
ayarlarını tercih et. Bu rehber geliştirme önizlemesini anlatır.

## Arayüz dili

`Ctrl + ,` ile ayarları aç, **Genel → Dil → Türkçe / English → Kaydet** yolunu
izle. Ana pencere yeniden başlamadan; sohbet, taslak ve ekli görsel silinmeden
güncellenir. Genel ve Gizlilik ayarları, bir sonraki açılışta kaydedilen dilde
görünür. Vazgeç, izinler dahil kaydedilmemiş değişiklikleri iptal eder. Bu arayüz
ayarı model yanıtlarını veya yazdığın metni çevirmez. Ses, geçmiş, hafıza
pencereleri ve bazı durum/hata mesajları henüz tamamen çevrilmedi.

## Günlük kontroller

| İşlem | Kısayol / kontrol |
| --- | --- |
| Göster / gizle | `Alt + Space` |
| Gönder | `Enter` veya gönder düğmesi |
| Kontroller arasında dolaş | `Tab` / `Shift + Tab` |
| Panoyu incele | `Ctrl + Shift + V` veya `/clip [talimat]` |
| Başka uygulamadaki seçili metin | `Ctrl + Shift + Space` |
| Sesli girişi başlat / bitir | Nexus odaktayken `F2` |
| Yeni sohbet / geçmiş | `Ctrl + N` / `Ctrl + H` |
| İstem geçmişi | Giriş alanında `↑` / `↓` |
| İşlemi iptal et / boşta gizle | `Esc` |
| Çık | `Ctrl + Q` |
| Web araştırması | `/web <soru>` |
| Açıkça hafızaya kaydet | `/remember <bilgi>` veya `/hatırla <bilgi>` |
| Hafızayı göster / kaynağı düzelt | `/memory` / `/correct <kaynak numarası veya kimliği>` |
| Hazır istemler | `/summarize`, `/rewrite`, `/translate`, `/fix`, `/explain` |

Mesaj alanında **Ekle**, **Araştır** ve **Araçlar** bulunur. Araçlar menüsünden
özel oturum, belgelerden yanıtlama, sesli yanıt ve hafıza yönetimine ulaşılır.
Yanıt başlığında kopyalama düğmesi vardır.

## Belgeler ve hafıza

**Ekle** ile okunabilir belge getir, ardından **Belgelerimden yanıtla** seçeneğini
aç. PDF'deki gömülü metin okunur; OCR yapılmaz. DOCX için şu anda paragraflar okunur,
her tablo veya gömülü nesne değil. Metin modeli çıkarılan metni özetleyebilir;
görsel analizi için görsel anlayan model seçilmelidir.

**Ayarlar → Gizlilik** altında üç ayrı tercih vardır:

1. Kayıtlı hafızayı gelecekteki yanıtlarda kullanma.
2. Normal konuşmalardan otomatik hafıza adayı çıkarma.
3. Konuşma/proje özetlerini gelecekteki yanıtlarda kullanma.

Adaylar kendiliğinden etkinleşmez. **Araçlar → Hafızayı yönet** bölümünde içeriği
inceleyip **Adayı etkinleştir** seçeneğini kullan. Son işlem durumunu kontrol et;
devam eden çıkarma işlemi için **Yenile** düğmesine bas. Konuşmadan kalıcı bilgi
çıkmaması ile çıkarma hatası farklıdır. Model bilgiyi yanlış yorumlayabilir;
onaylamadan önce özellikle hassas içeriği incele.

## Ses

**Ayarlar → Ses** içinde **Giriş** mikrofonu ve F2 davranışını, **Hey Nexus** çağrı
iznini/model hazırlığını, **Yanıt sesi** hoparlörü ve ses motorunu içerir. Bölüm
değiştirmek kaydedilmemiş seçimleri silmez; Kaydet uygular, Vazgeç iptal eder.
F2 davranışları aç/kapat, basılı tutarak konuş veya sessizlikte bitirdir. Normal kayıt en fazla
60 saniyedir; sessizlik algısı mikrofona ve ortama bağlıdır. F2 pencere odağı ister.
Yeni kayıt, mevcut yanıtı ve seslendirmeyi keser.

Otomatik ses modu, modeli ve gerekli paketleri kuruluysa Supertonic'i; aksi halde
Windows sesini kullanır. Açıkça seçilmiş Supertonic çalışmazsa buluta sessizce
geçmek yerine hata verir. Edge için ayrı bulut izni gerekir. Ses karakteri, hız
ve 4/6/8 üretim adımı seçilebilir; daha az adım kaliteyi etkileyebilir. Alt yazı
oynatılan parçayı gösterir, kelime zamanlaması sağlamaz.
[Ölçümler ve sınırlamalar](VOICE_AND_MEMORY_RELIABILITY.md).

**Hey Nexus deneysel ve varsayılan olarak kapalıdır.** Arka planda dinleme ve
uygulamayla başlatma ayrı ayarlardır. Önbellekteki yerel Whisper'ı kullanır,
kendiliğinden model indirmez; kısa ortam seslerini RAM'de tutar. Durum pencere ve
sistem tepsisinde görünür; oradan duraklat veya ertele. Tepsi göstergesi varken
pencereyi gizlemek, izinli arka plan dinlemesini kapatmaz. Tam durdurmak için çıkış
yap. Algılama güvenilir değilse F2 kullan. Fiziksel mikrofon doğruluğu garantisi yoktur.

Açmak için **Ayarlar → Ses → Giriş** bölümünde mikrofonunu seç, ardından
**Hey Nexus** bölümündeki **Modeli kontrol et** düğmesine bas.
Kontrol, önbellekteki Whisper base'i çevrimdışı yükler; mikrofonu
açmaz. Eksikse **Modeli hazırla…** ile ayrı Hugging Face indirme onayını ver.
Bu işlem dinleme izni vermez, seçili dil modelini değiştirmez veya ses göndermez.
Cihaz durumu, eksik/bağlı olmayan mikrofonu açmadan gösterir; Windows iznini veya
kayıt kalitesini doğrulamaz. Ardından **Hey Nexus dinlemesine izin ver** seçeneğini
kaydet. Arka plan dinleyicisi kendiliğinden model indirmez.
Tek başına **Hey Nexus** de, durakla, ardından **Konuşmaya başlayabilirsin** yazısını
bekleyip komutunu söyle. Bu yazı ancak komut mikrofonu başarıyla açıldıktan sonra
görünür. Çağrı ile komutu aynı nefeste söylemek desteklenmiyor.

Ayarları kaydetmek mevcut duraklatma veya ertelemeyi bozmaz; yeniden dinletmek
için pencere/tepsi devam düğmesini kullan. İki saniyeyi aşan model çözümleme
sonuçları ve süresi dolan arayüz bildirimleri sonradan tetikleme yapmaz, atılır.
İşlemcinde bu durum sık yaşanırsa F2 kullan. Model hazırlığı, mikrofon ve algılama
hataları ayrı mesajlarla açıklanır; hatadan sonra otomatik yeniden deneme yapılmaz.

Model hazırlığını **İşlemi durdur** ile iptal edebilirsin. Ayarları kapatmak da
hazırlama sürecini durdurur; beş dakika zaman aşımı vardır. Ayarlardan vazgeçsen
bile indirilmiş veya kısmi dosyalar model önbelleğinde kalabilir. **Vazgeç**, açıkça
onaylanmış indirmeyi geri almaz; kaydedilmemiş ayarları iptal eder. Model hazırlığı
ses kaydetmez. F2 ile ilk sesli giriş, alternatif model hazırlama yolu olarak kalır.

## Sorun giderme

| Belirti | Kontrol |
| --- | --- |
| Sağlayıcıya ulaşılamıyor | Sunucuyu aç, modeli yükle, Genel bölümünde yeniden tara; model kimliğini doğrula |
| Model görseli anlamıyor | Görsel destekli model seç; metin desteği yeterli değil |
| Ses yok | Araçlar → Yanıtları seslendir; çıkış cihazı, motor kurulumu ve Edge için bulut iznini kontrol et |
| Ses geç başlıyor | Yerel 4-adım modunu ve kısa yanıtı dene; LLM beklemesini ses üretiminden ayır |
| Otomatik hafıza yok | Aday çıkarmayı aç, özel oturumdan çık, son işlem durumuna bak; adayları onayla ve hafıza kullanımını aç |
| Belge metni boş | PDF'de metin seçilebildiğini kontrol et veya düz metin çıkar; taranmış sayfalarda OCR yok |
| Mikrofon / uyandırma sorunu | Cihazı yeniden seç, eşiği ayarla; önce odaktayken F2'yi dene |
| 8000 bağlantı noktası dolu | Eski Nexus'u kapat veya `NEXUS_BACKEND_PORT` değiştir; ilgisiz uygulamaları sonlandırma |
| Windows asyncio kapanış uyarısı | Python 3.14'te bilinen aralıklı sorun; sürüm ve yapay tekrar örneği paylaş, özel kayıtları paylaşma |

Sorun giderirken veri klasörünü silme. Önce yerel verilerini özel bir yerde yedekle.

## Katkı verenler için tanılama

Proje klasöründe uygulamanın Python ortamıyla çalıştır:

```powershell
.\.venv\Scripts\python.exe scripts\check_voice.py
.\.venv\Scripts\python.exe scripts\benchmark_tts.py
.\.venv\Scripts\python.exe scripts\check_memory.py
```

İlk komut **yapay örnek sesi oynatır**. Hız ölçümü, geçici ses üretir ama oynatmaz.
Hafıza kontrolü seçili yerel modele yapay tercih gönderir ve geçici veritabanı
kullanır. Hiçbiri mikrofonu açmaz. Ses için ek paket/model; hafıza için çalışan
yerel model gerekir. Başarılı sonuç, doğal ses veya tüm canlı sohbet akışının
doğrulandığı anlamına gelmez.

## Gelişmiş yapılandırma

Geliştirici ayarı gerekiyorsa [.env.example](../.env.example) dosyasını `.env`
olarak kopyala; yayımlama. Ayarlar normalde `%LOCALAPPDATA%\Nexus` içindedir;
`NEXUS_DATA_DIR` konumu değiştirir. [Veri sınırları](PRIVACY.tr.md).

Başlıca ayarlar: `NEXUS_API_BASE_URL`, `NEXUS_API_KEY`, `NEXUS_MODEL`,
`NEXUS_BACKEND_PORT`, `NEXUS_TTS_ENABLED`, `NEXUS_TTS_BACKEND`,
`NEXUS_SUPERTONIC_SPEED`, `NEXUS_SUPERTONIC_SPEAKER`, `NEXUS_SUPERTONIC_STEPS`.
Ses ortam değişkenleri kayıtlı arayüz tercihlerinin önüne geçer. Örnek dosyadaki
model adı, modelin kurulu olduğu anlamına gelmez. Model ve API adreslerini yerel tut.
