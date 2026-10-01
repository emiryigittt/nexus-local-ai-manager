# Ses ve hafıza güvenilirliği

[English](VOICE_AND_MEMORY_RELIABILITY.en.md) · **Türkçe** · [Belgeler](INDEX.md)

Güncelleme: 1 Ekim 2026. Yanıtlar kullanıcının seçtiği sağlayıcıdan alınır.
Bu rapor ölçülen sonuçları, uygulanan değişiklikleri ve açık testleri birbirinden ayırır.

## Doğal konuşma ve kayıt bitişi — 1 Ekim

- Komut çözümleme, çağrı algılamasının hafif modelinden ayrıldı. **Doğal konuşma**
  seçimi çok dilli Whisper small kullanır; varsayılan **Dengeli** seçimi base kullanır. Küçük model
  henüz hazırlanmadıysa mevcut base ile devam edilir. İkisinin de bulunmaması halinde
  model hazırlama yönlendirmesi gösterilir; konuşma sırasında otomatik indirme yapılmaz.
- Komut çözümlemede beş aday ve sıfır sıcaklık kullanılır; yalnızca kısa çağrı algılama
  tek adayla devam eder. Zayıf kayıtlara sınırlı ses yükseltme uygulanır, DC bileşeni
  çıkarılır. Kaynak örnekler değiştirilmez; çalışma kopyaları işlem sonrasında silinir.
- F2 başlat/durdur modunda **Konuşma bitince otomatik gönder** varsayılan açıktır.
  Mevcut ayarlarda bu yeni alan yoksa açık kabul edilir. Basılı konuş modu tuşu bırakmayı
  beklemeye devam eder; otomatik bitiş kapatılarak ikinci F2 ile sonlandırma kullanılabilir.
- Kayıt bitişi, paketle gelen yerel Silero konuşma algılayıcısıyla belirlenir. Model
  işlemi mikrofon geri çağrısında çalışmaz; kayıt çalışanında, sınırlı bağlamla ilerler.
  Kısa duraklamalardan sonra konuşma sürerse sessizlik sayacı yenilenir. Varsayılan
  bitirme sessizliği 1,2 saniyedir; Ayarlar → Ses → Giriş bölümünde değiştirilebilir.
- İsteğe bağlı **Göndermeden önce metni kontrol et**, sonucu düzenlenebilir alanda
  bekletir. Enter ile gönderilir. Varsayılan hızlı akış, tanınan metni otomatik gönderir.
- **Konuşma modelini hazırla** yalnızca model dosyalarını indirir ve çevrimdışı
  yüklemeyi doğrular. Ses kaydı veya bulut çözümlemesi yapılmaz. Daha güçlü model
  daha fazla işlem gücü kullanır; her cihazda önceki yanıt hızını koruma garantisi yoktur.
- 367 otomatik test geçti. Sabit yapay Türkçe örneklerin normal ve %20 ses düzeyinde,
  %12 hızlandırılmış sürümleri kontrol edildi. Hafif modelde zorlaştırılmış bir örnekte
  iki kelime hatası görüldü; kusursuz doğruluk iddia edilmez. Yapay arka plan gürültüsü
  sürerken örnek kayıt sona erdi. Bu testler gerçek kullanıcının aksanını/gürültüsünü
  temsil etmez; fiziksel mikrofon açılmadı.
- Small modeli indirildi, resmi SHA256 kaydıyla doğrulandı ve hem kaynak başlatıcıda
  hem Windows paketinde çevrimdışı yüklenebildi. Son sabit örnek karşılaştırmasında
  base 1,1–1,6 sn, small 3,4–3,9 sn sürdü. Small iki örnekte aynı tek kelimeyi hatalı
  tanıdı; base bu altı örnekte kelime hatası yapmadı (noktalama farklılıkları hariç).
  Bu küçük, yapay örnek kümesi gerçek kullanıcı doğruluğunu ölçmez. Daha büyük modelin
  her örnekte daha iyi olduğu iddia edilmez; varsayılan, hız için base olarak korundu.

## Çağrı, yanıt gecikmesi ve ses takibi — 1 Ekim (önceki geçiş)

Bu bölüm güncel davranışı anlatır. Aşağıdaki 27 Eylül ölçümleri ve sınırları tarihsel kayıttır.

- Kısa çağrılar için ayrı **Çağrı ses eşiği** eklendi; varsayılan %0,40.
  Normal komut kaydının eşiği değişmez. Türkçe aksan ve bitişik yazım varyantları
  kabul edilir; “Hey next”, yalnızca “Nexus” veya cümle içindeki anmalar tetiklemez.
- Yerel çözümleme tek adayla yapılır. Çözümleme sonrası geçersiz sayılma sınırı
  iki saniyeden altı saniyeye çıkarıldı; iptal ve eski kayıt kontrolleri korunur.
  Bu sınır, çalışan yerel çözümlemeyi zorla kesme garantisi değildir.
- **Ayarlar → Ses → Hey Nexus → Çağrıyı dene (5 sn)** yalnızca tıklanınca mikrofonu
  açar. Önce arka plan dinleyicisinin cihazı bırakmasını bekler. Yetersiz ses düzeyi
  ile algılanamayan çağrı ayrı bildirilir. Ses diske kaydedilmez veya gönderilmez;
  sürekli dinleme izni değişmez. “Hey Nexus” deyip duraklayın; ardından komutu söyleyin.
- Çağrı sırasında yüklenmiş Whisper modeli komut çözümlemesinde yeniden kullanılır.
  Yanıt ekranı ilk parçayı hemen gösterir; sonraki parçalar 40 ms aralıklarla birleştirilir.
- Ses parçaları en fazla 110 karakterdir. Noktalamasız akışta 25 karakter ve 0,45 saniye
  sonrasında tamamlanmış kelimeler gönderilebilir. Motor ve sağlayıcı süreleri ayrıca eklenir.
- Alt yazı ve ana yanıttaki kelime vurgusu gerçek oynatıcı konumunu takip eder.
  Edge zaman bilgisi sağladığında kelime sınırları kullanılır. Yerel seslerde kelime
  hizası yaklaşık hesaplanır; her kelime için kesin eşzamanlılık iddiası yoktur.
- Hafıza/belge vektör aramasına sorgu başına 0,6 saniye ayrılır; aşılırsa metin eşleşmesine
  dönülür. Yeni etkileşim, isteğe bağlı hafıza çıkarma/özetleme işlerini iptal eder.
  Böylece bu işlerin modeli meşgul etmesi azaltılır; iptal edilen tur için yeni otomatik
  hafıza adayları veya özet oluşmayabilir. Onaylı kayıtlar silinmez.
- 358 otomatik test ve Ruff geçti. Sabit yapay seslerle çevrimdışı kontrolde 6/6 çağrı
  algılandı, 9 olumsuz cümlede tetiklenme olmadı; tampon işleme 0,48–0,61 saniye sürdü.
  Fiziksel mikrofon açılmadı. Bu sonuç gerçek ses/gürültü başarısını kanıtlamaz.
  Seçili LM Studio sunucusu kontrol sırasında erişilebilir olmadığından gerçek modelin
  uçtan uca yanıt süresi ölçülemedi. Bulut sesi zamanlaması sahte akışla doğrulandı;
  canlı bulut hizmeti çağrılmadı.

## Hey Nexus takibi — 27 Eylül

- Ayar kaydı oturumdaki duraklatma, erteleme veya hata nedeniyle durmayı kaldırmaz.
  Yalnızca yeni izin verme dinlemeyi başlatır; açılışta dinleme ayrı tercihtir.
- İki saniyelik çözümleme sınırı, geciken arayüz sinyallerinin geçersizleşmesi,
  iptal ve cihaz bırakma kontrolleri eski çağrıların tetiklemesini önler.
  Geçersiz güven puanları reddedilir.
- Çağrı kontrolleri, tepsi durumları ve model/cihaz/algılama hata açıklamaları iki
  dildedir. Komut ekranı ancak mikrofon başarıyla açılınca hazır olduğunu söyler.
- `scripts/check_wake_word.py --repetitions 3`, kurulu Supertonic ve önbellekteki
  Whisper base ile 6/6 yapay çağrıyı algıladı; 9 olumsuz cümlede tetiklenmedi.
  Tamponlanan örneklerin işlenmesi 0,49–0,56 saniye sürdü. Bu uçtan uca çağrı
  gecikmesi değildir: canlı sessizlik algılama, arayüz ve mikrofon açılışı süre ekler.
- Sabit yapay cümleler gerçek ortam doğruluğunu veya önceki rastlantısal ses üretimi
  denemelerine göre iyileşmeyi kanıtlamaz. Fiziksel mikrofon açılmadı, ortam sesi
  kaydedilmedi, bulut modeli çağrılmadı. Algılama deneysel kalıyor.
- 232 otomatik test ve Ruff geçti. Fiziksel mikrofon/gürültü doğrulaması açık;
  daha önce aralıklı görülen Windows kapanış uyarısı çözülmüş sayılmıyor.

## Bu turda uygulananlar

- Ses üretimi metin akarken başlar. Uzun metinler en fazla 180 karakterlik parçalara
  bölünür; mümkün olduğunda cümle, ara noktalama veya kelime sınırı korunur.
- Noktalamasız akışta en az 50 karakter birikmiş ve 1,2 saniye geçmişse tamamlanmış
  kelimeler üretime gönderilir. Bu bir sesin başlama garantisi değildir; model ve
  oynatıcı gecikmesi ayrıca eklenir.
- Yerel motor, dil modeli yanıt üretirken önceden yüklenir. Sonraki parçanın
  üretimi önceki parçanın oynatılmasıyla örtüşebilir.
- Oynatıcıya verilen parçanın metni alt satırda görünür. Ana yanıt metni bekletilmez.
  Bu, kelime zamanlamalı senkronizasyon veya gerçek PCM akışı değildir.
- Ayarlar → Ses: 10 Supertonic sesi, bulut ses seçimi, konuşma hızı ve 4/6/8 üretim
  adımı. Varsayılan 8 adım korunur; hızlı modun kalite farkı dinlenmelidir.
- Bulut ses izni denetimi korunur. Bu turdaki testler bulut ses hizmetini çağırmadı.

## Bu bilgisayardaki ölçümler

`scripts/benchmark_tts.py`: geçici veritabanı/ayarlar, sabit yapay Türkçe cümle,
mevcut Supertonic 3 int8 modeli, ses oynatılmadan dosyaya üretim.

| Deneme | Üretim | Ses süresi | Üretim / ses süresi |
| --- | ---: | ---: | ---: |
| 8 adım, ilk yükleme dahil | 1,686 sn | 4,012 sn | 0,420 |
| 8 adım, motor hazır | 0,819 sn | 4,012 sn | 0,204 |
| 4 adım, motor hazır | 0,436 sn | 4,012 sn | 0,109 |
| 4 adım, tekrar | 0,435 sn | 4,012 sn | 0,108 |

Bu kısa örnekte 4 adım, sıcak 8-adım üretiminden yaklaşık %47 daha hızlıydı.
Bu sonuç genel bir hız garantisi, eski sürümle karşılaştırma, kalite puanı veya
uçtan uca konuşma gecikmesi değildir. Cümle uzunluğu, yük ve donanım sonucu değiştirir.

`scripts/check_voice.py`: gerçek Qt/Realtek çıkışında iki yapay cümle üretildi ve
iki parçanın da oynatımı tamamlandı; iki metin bildirimi geldi, hata görülmedi.
İlk ses dosyası yaklaşık 0,997 saniyede hazır oldu. Bu ölçüm LLM beklemesini içermez;
insanın sesi duyduğunu veya doğal bulduğunu kanıtlamaz.

## Güncel yerel ses seçenekleri

Aşağıdaki öneriler kaynaklardaki yeteneklerden yaptığımız değerlendirmedir;
Supertonic dışındaki modeller bu makinede ölçülmedi veya kurulmadı.

| Seçenek | Türkçe / kaynak bilgisi | Nexus için değerlendirme |
| --- | --- | --- |
| [Supertonic 3](https://github.com/supertone-oss-archive/supertonic) | Türkçe dahil 31 dil, 99M, ONNX. Depo 9 Eylül 2026'da arşivlendi; destek sona erdi. Kod MIT, ağırlıklar ayrı OpenRAIL-M koşullarında. | Kurulu hafif motoru koru; bakım riskini açıkla. Sürüm/lisans sabitlemeden yeni dağıtım yapma. |
| [Chatterbox Multilingual](https://www.resemble.ai/learn/models/chatterbox-multilingual) | Yayıncı Türkçe, ifade kontrolü, yerel kullanım ve MIT lisanslı V3 bildiriyor. | Daha karakterli Türkçe için sonraki A/B adayı. Hafiflik veya düşük CPU gecikmesi varsayma; ayrı isteğe bağlı çalışma ortamında ölç. Turbo ile dil desteğini karıştırma. |
| [Pocket TTS](https://github.com/kyutai-labs/pocket-tts) | 100M, CPU odaklı, ses akışı. Resmî dil listesinde Türkçe yok. | Türkçe varsayılanı yapma; desteklenen diller için ileride isteğe bağlı seçenek. Yayıncı hızlarını Nexus ölçümü olarak sunma. |
| [Qwen3-TTS 0.6B](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base) | Resmî 10 dil arasında Türkçe yok. | Bu aşamada Türkçe asistan ihtiyacını karşılayan aday sayma. |

Önce mevcut sesleri ve 4/6/8 adımları aynı Türkçe metinlerle karşılaştıracağız.
Sonra Chatterbox'ın belirli model sürümünü, lisansını, indirme boyutunu ve donanım
gereksinimini kaydedip isteğe bağlı entegrasyona karar vereceğiz. Kullanıcının
izni olmadan ses örneği yükleme veya gerçek kişilerin sesini klonlama yok.

## Hafıza: kayıt, onay ve kullanım farklı aşamalardır

1. Gizlilik ayarlarında otomatik aday çıkarma açıksa, normal konuşma bitiminde
   yerel modelden kalıcı bilgiler çıkarılır. Özel oturumlar bu işe girmez.
2. Bilgi SQLite'a **aday** olarak kaydedilir; kendiliğinden aktif olmaz.
3. Araçlar → Hafızayı yönet → Adayı etkinleştir ile kullanıcı onaylar.
4. Hafızayı kullanma ayarı açıkken ilgili aktif kayıtlar sonraki yanıta seçilebilir.

Artık hafıza penceresi son çıkarma işinin sonucunu gösterir: aday sayısı, bağlantı
sorunu, zaman aşımı veya geçersiz model çıktısı. Yenile düğmesi son durumu getirir.
Durum tablosu yalnızca son işin durumunu, sayısını, kimliğini ve zamanını tutar;
konuşma, çıkarılan bilgi, anahtar veya sunucu hata gövdesi içermez.

JSON şemasını desteklemediğini bildiren yerel sunucularda yalnızca bir kez sade
JSON istemine geri dönülür. Sonuç yine doğrulanır; geçersiz çıktı artık sessizce
“bilgi yok” sayılmaz. Kullanıcı işlem sırasında otomatik öğrenmeyi kapatırsa kayıt
öncesinde izin tekrar kontrol edilir. Hassas bilgi filtresi korunur; bunun bütün
hassas bilgileri yakalayacağı garanti edilmez.

Kontroller: şema geri dönüşü, bozuk/boş JSON ayrımı, aday → onay → yeniden açma,
izin kapatma, özel oturum ve içeriksiz hata durumu otomatik testlerle doğrulandı.
Bu güvenilirlik aşamasındaki test çalışması: 170 başarılı test; Ruff temiz. Önceden görülen Windows
Python 3.14 asyncio kapalı-pipe temizleme uyarısı tekrar görüldü ve açık tutuldu.
Canlı kullanıcı verileri değiştirilmedi. `scripts/check_memory.py` gerçek model
kontrolünde bağlantı hatası aldı; seçili yerel sunucu açılınca tekrar çalıştırılmalı.
Önceki oturumların neden kaydedilmediği kesinleşmiş değildir.

## Açık kabul testleri

- Aynı cümleler için 20 tekrar: soğuk/sıcak ilk oynatma, parçalar arası sessizlik,
  p50/p95 gecikme, CPU/RAM ve LLM eşzamanlı yükü; donanım/sürüm bilgisiyle raporla.
- Türkçe sayılar, kısaltmalar, teknik terimler, uzun yanıtlar ve kesinti/yeniden başlama.
- Kullanıcıyla kör ses karşılaştırması: doğallık, anlaşılırlık ve karakter.
- İzinli bulut uçtan uca ses testi; gerçek ağ gecikmesi ve bağlantı kesilmesi.
- Gerçek yerel modelle hafıza çıkarma, uygulama yeniden açıldıktan sonra onaylı
  bilginin sonraki yanıtta kaynak gösterilerek kullanılması.
- Gerçek PCM akışı, kelime zamanlamaları ve uzun yanıtlarda kuyruk geri basıncı
  ayrı işlerdir; bu sürümde tamamlandı sayılmamalıdır.
