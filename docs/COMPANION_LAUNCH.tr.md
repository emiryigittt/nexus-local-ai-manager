# Yeni Nexus tanıtım paketi

**Türkçe** · [English](COMPANION_LAUNCH.md) · [Belgeler](INDEX.md)

1 Ekim 2026. Bu içerikler yeni yerel geliştirme önizlemesi içindir.
Dosyalar hazırlandı; sosyal paylaşım ve yeni herkese açık kurulum yayını yapılmadı.

En güncel tanıtım: yerel `output/launch/social-film-v2` klasöründe Türkçe ve
İngilizce **50 saniye, 1080×1920, 60 fps** videolar, altyazılar, kapaklar ve
`nexus-social-film-v2-tr-en-kit.zip`. Özgün müzik ve tok, ekolu sesler kullanılır;
sayfa sürtme efekti kaldırıldı. Aşağıdaki 36 saniyelik dosyalar eski sürümdür.

Yeni duyuruda
[ilk kaynak kod betasına](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.1)
yönlendir. Python 3.11–3.13 ve çalışan yerel model gerektiğini açıkça belirt;
bu yayında herkese açık `.exe` yok. Video canlı model çalışmasını göstermez.

## Video ve kapak

Yerel `output/launch` klasöründeki yeni dosyalar:

- `nexus-promo-reels-tr.mp4`: 1080×1920, 36 saniye, Reels/Shorts/TikTok için.
- `nexus-promo-landscape-tr.mp4`: 1920×1080, 36 saniye, YouTube/GitHub sunumu için.
- İkisinin SRT altyazıları, sekiz sahne görseli ve JSON kapsam bilgisi.
- `nexus-companion-launch-kit.zip`: videolar, altyazılar, kapaklar ve bu paylaşım metinleri.

Gerçek uygulama hareketleri; üst şerit, üzerine gelince açılan panel, sohbet,
RGB/kedi seçimi ve hafıza adayının gerçek yerel onayını gösterir. Masaüstü arka
planı temsili, yanıtlar ve sesli durumlar kurgudur. Etiket her karede bulunur.
Özgün sentezlenmiş fon müziği ve Nexus ses efektleri içerir; üçüncü taraf müzik yoktur.
Canlı çıkarım, mikrofon kaydı veya performans ölçümü diye paylaşma.

Yeniden üretmek için mevcut önizleme ortamında:

```powershell
python -m scripts.render_companion_promo
python -m scripts.render_companion_promo --landscape
```

## Reels / Shorts açıklaması

Ekranın üstünde küçük bir yerel yapay zekâ asistanı: Nexus.

Üzerine gelince araçların açılıyor; bir tıkla sohbete geçiyorsun. RGB rengini,
mini bot veya kedini ve kısa ses efektlerini kendin seçiyorsun. Hafızasında ne
kalacağını da sen belirliyorsun.

Ollama, LM Studio veya llama.cpp'de çalışan modeline bağlanan Windows asistanı.
Yeni arayüz geliştirme önizlemesinde; videoda örnek içerik ve durumlar gösteriliyor.

Projeyi takip et: https://github.com/emiryigittt/nexus-local-ai-manager

#Nexus #LocalAI #YapayZeka #Ollama #Windows

## LinkedIn paylaşımı

Nexus'un yeni masaüstü deneyimini hazırlıyorum: çalışma alanını kaplamayan,
ekranın üstünde küçük bir şerit olarak duran yerel yapay zekâ asistanı.

Fareyle yaklaştığında belge, hafıza, araştırma ve ses araçlarını gösteriyor.
Sohbet için genişliyor; küçüldüğünde taslağı ve devam eden işi korunuyor.

Yeni sürüme RGB renk seçimi, mini bot/kedi karakterleri, isteğe bağlı kısa sesler
ve daha okunaklı bir hafıza ekranı da ekledim. Önerilen hafıza kayıtları kullanıcı
onayı olmadan etkinleşmiyor.

Windows ve çalışan Ollama, LM Studio veya llama.cpp sunucusu kullanıyorsan,
özellikle mini panel ve hafıza akışı üzerine geri bildirimini merak ediyorum.
Bu video gerçek arayüzün kurgu içerikli tanıtımı; canlı model çalışması değil.

Proje: https://github.com/emiryigittt/nexus-local-ai-manager

## Kısa paylaşım

Nexus'u ekranın üstünde küçük bir şeride taşıdım: üzerine gel → araçları gör,
tıkla → sohbeti aç. RGB renkleri, kedi/bot seçimi ve kullanıcı kontrollü hafıza.
Windows için yerel AI asistanının yeni geliştirme önizlemesi. Videodaki içerik örnek.

https://github.com/emiryigittt/nexus-local-ai-manager

## İlk paylaşım sırası

1. Dikey videoyu ve kısa açıklamayı kendi sosyal hesabında paylaş.
2. Yatay videoyu ve LinkedIn metnini kullan; depoya yönlendir.
3. Yerel önizleme kurulumunu 5–10 gönüllüyle ayrı paylaş; imzalı herkese açık
   sürüm yayımlanmış gibi sunma. Python gerektirmeyen yerel paket hazırdır;
   ayrı model sunucusu gereklidir.
4. Önce üç soru sor: Panel işini kolaylaştırdı mı? Renk/karakter ayarını buldun mu?
   Hafızayı inceleyip düzenleyebildin mi? Sonra gerçek model ve ses denemeleri yap.

Paylaşımdan önce ilgili topluluğun o günkü tanıtım kurallarını kontrol et.
Henüz ölçülmemiş kullanıcı sayısı, yanıt hızı veya donanım başarısı iddia etme.
