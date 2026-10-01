# Nexus kullanım rehberi

[English](USER_GUIDE.md) · **Türkçe** · [Belgeler](INDEX.md)

Kurulum için [Türkçe başlangıca](../README.tr.md#başlangıç) bak. Etiketler mevcut
Türkçe arayüzle eşleşir. Ortam değişkenlerini değiştirmek yerine normal uygulama
ayarlarını tercih et. Bu rehber geliştirme önizlemesini anlatır.

İlk açılışta dili seç, yerel sağlayıcıları tara ve seçtiğin modeli test et.
Daha sonra dersen kayıtlı ayarlar değişmez. Karşılama ekranındaki **Bağlantı kurulumu**
ile geri dönebilirsin. **Örnek belgeyle dene** kurgu bir belgeyi yükleyip göndermen
için soruyu hazırlar. Python gerektirmeyen kurulum ve uygulama içindeki isteğe bağlı
ses hazırlığı için [Windows önizleme rehberine](WINDOWS_PREVIEW.tr.md) bak.

## Arayüz dili

Panel ile Sohbet arasında geçiş, düğmeler ve belge bırakma alanı kısa animasyonlar
kullanır. Asistan dinlerken, düşünürken ve yanıtı seslendirirken farklı hareketler
gösterir; işlem tamamlanınca kısa bir onay, hata olunca farklı bir tepki verir.
Ses dalgası ses seviyesini ölçmez. **Ayarlar → Genel → Hareketi azalt** bütün
hareketleri ve göz kırpmayı kapatır; durum yazıları ve işlevler korunur.

Asistan karşılama ekranında daha büyük görünür. Geniş sohbet penceresinde yanıtın
yanında kalır; küçük pencerede başlığa taşınarak okuma alanını korur. Hazırken yavaş
bir nefes hareketi, dinleme ve seslendirmede daha belirgin renkli halkalar kullanır.

`Ctrl + ,` ile ayarları aç, **Genel → Dil → Türkçe / English → Kaydet** yolunu
izle. Ana pencere yeniden başlamadan; sohbet, taslak ve ekli görsel silinmeden
güncellenir. Genel ve Gizlilik ayarları, bir sonraki açılışta kaydedilen dilde
görünür. Vazgeç, izinler dahil kaydedilmemiş değişiklikleri iptal eder. Bu arayüz
ayarı model yanıtlarını veya yazdığın metni çevirmez. Ses, geçmiş, hafıza
pencereleri ve bazı durum/hata mesajları henüz tamamen çevrilmedi.

## Günlük kontroller

Nexus üst kenarın ortasında 180×36 boyutunda küçük bir şeritte açılır. Fareyi
üzerinde kısa süre tutunca 460×188 mini panel görünür. Uzaklaştırınca kapanır;
**Sabitle** ile açık tutabilirsin. Şeride tıkla veya **Sohbeti aç** ile genişle.
Konum, görev çubuğunun kaplamadığı ekranın üst kenarına sabitlenir.
Asistanın yüzü ve durum yazısı gerçek
dinleme/yanıt hazırlama durumunu gösterir. Belge ekleme, hafıza, araştırma ve sesli
giriş buradan açılır. **Sohbet** sekmesi daha geniş çalışma alanını gösterir;
yanıt başladığında kendiliğinden açılır. Panel ve Sohbet arasında geçiş yapmak
konuşmayı, yazdığın taslağı veya ekli görseli silmez. Alt bölümdeki **Model**
düğmesi bağlantı kurulumunu açar. **Özel oturum** doğrudan mesaj alanında da bulunur.

| İşlem | Kısayol / kontrol |
| --- | --- |
| Sohbeti aç / üst şeride dön | `Alt + Space` |
| Gönder | `Enter` veya gönder düğmesi |
| Kontroller arasında dolaş | `Tab` / `Shift + Tab` |
| Panoyu incele | `Ctrl + Shift + V` veya `/clip [talimat]` |
| Başka uygulamadaki seçili metin | `Ctrl + Shift + Space` |
| Sesli girişi başlat / bitir | Nexus odaktayken `F2` |
| Yeni sohbet / geçmiş | `Ctrl + N` / `Ctrl + H` |
| İstem geçmişi | Giriş alanında `↑` / `↓` |
| İşlemi iptal et / boşta üst şeride dön | `Esc` |
| Çık | `Ctrl + Q` |
| Web araştırması | `/web <soru>` |
| Açıkça hafızaya kaydet | `/remember <bilgi>` veya `/hatırla <bilgi>` |
| Hafızayı göster / kaynağı düzelt | `/memory` / `/correct <kaynak numarası veya kimliği>` |
| Hazır istemler | `/summarize`, `/rewrite`, `/translate`, `/fix`, `/explain` |

Mesaj alanında **Ekle**, **Araştır** ve **Araçlar** bulunur. Araçlar menüsünden
özel oturum, belgelerden yanıtlama, sesli yanıt ve hafıza yönetimine ulaşılır.
Yanıt başlığında kopyalama düğmesi vardır.

## Renk, yol arkadaşı ve ses efektleri

**Ayarlar → Görünüm** bölümünde hazır renklerden seçebilir, R/G/B değerlerini
girebilir veya renk seçiciyi açabilirsin. Canlı önizleme kaydedilmemiş tercihini
gösterir. **Kaydet** uygulamaya aktarır; **Vazgeç** önceki ayarlarını korur.
Mini bot ve Nexus kedisi aynı gerçek dinleme/düşünme/konuşma durumlarını izler.
**Yavaş RGB kenar ışığı** isteğe bağlıdır; Hareketi azalt açıkken sabit görünür.
RGB, göz kırpma ve hareketler görünmeyen pencerelerde çalışmaz.

Ses efektleri başlangıçta kapalıdır. Etkinleştirip ses düzeyini seçebilir,
**Sesi dene** ile kısa onay sesini dinleyebilirsin. Açma/küçültme, gerçek kayıt
başlangıcı, belge ekleme, tamamlanma ve hata için özgün kısa sesler kullanılır.
Üzerine gelmek ses çıkarmaz. Bu ayar, sesli yanıt ve mikrofon izinlerinden ayrıdır.

Hafıza ekranında arama ve tür/durum filtreleri kartları daraltır. Seçili kaydı
sağ tarafta düzenle; **Onayla** yalnızca aday kayıtta açılır. **Ayrıntılar** kapsam,
proje ve güven/önem alanlarını gösterir. **Profil özeti** ayrı sekmede kaydedilir.

## Belgeler ve hafıza

**Ekle** ile okunabilir belge getir veya PDF, DOCX ya da metin dosyasını pencereye
sürükle. Belge yerel kitaplığa eklenir ve **Belgelerimden yanıtla** açılır.
Sürükleyince mevcut taslağın korunur; alan boşsa bir özet sorusu hazırlanır.
Soruyu göndermek için Enter'a bas. Dosya bırakmak kendiliğinden bir model isteği
göndermez. Yeni sohbet açmak kitaplıktaki belgeleri silmez.
PDF'deki gömülü metin okunur; OCR yapılmaz. DOCX için şu anda paragraflar okunur,
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
