# Gizlilik ve güven sınırları

[English](PRIVACY.md) · **Türkçe** · [Belgeler](INDEX.md)

Mevcut kaynak kodun davranışını açıklar; güvenlik sertifikası değildir.

## Veri ve ağ haritası

| İşlem | Kullanılan veri | Saklama / alıcı |
| --- | --- | --- |
| Normal sohbet | İstem, seçili bağlam, yanıt | Seçili model sunucusu; geçmiş yerel SQLite'ta |
| Görsel analizi | Eklenen / panodaki görsel | Görsel destekli seçili model sunucusu |
| Belge alma | Çıkarılan metin ve parçaları; isteğe bağlı vektörler | Yerel SQLite; vektör isteği yapılandırılan model sunucusuna |
| Hafıza | Açık kayıtlar, adaylar, onaylı bilgiler, özetler | Yerel SQLite; çıkarma/özetleme/getirme işlemleri için seçili model |
| Özel sohbet | RAM'deki yakın konuşma | Nexus sohbet/hafıza kaydı yok; sağlayıcı istekleri kaydedebilir |
| F2 transkripsiyon | Mikrofon sesi ve metni | Yerel Whisper; ilk model indirmesi ağ kullanabilir |
| Yerel seslendirme | Yanıt metni ve üretilen ses | Yerel motor; normal temizlikte silinen geçici oynatma dosyaları |
| Edge sesi | Okunacak metin | Bulut izninden sonra Microsoft çevrimiçi ses hizmeti |
| Web araştırması | Sorgu, sonuçlar, sayfa adresleri/alınan metin | `ddgs` arama hizmetleri ve Jina Reader; metin sonra seçili modele |
| Deneysel uyandırma | Kısa ortam sesi parçaları | Sınırlı RAM tamponu, önbellekteki Whisper; kayıt/sohbet/bulut aktarımı yok |
| Çağrı modeli hazırlığı | Yalnızca model dosyası istekleri | Kontrol çevrimdışı; Modeli hazırla, Hugging Face indirmesi için ayrı onay ister; mikrofon/sohbet verisi kullanılmaz |
| MCP araçları | Onaylı argümanlar, sonuçlar ve süreç etkinliği | Üçüncü taraf yerel süreç; kendi ağ/kayıt davranışı olabilir |

## Yerel olmak, şifreli veya yalıtılmış olmak değildir

Varsayılan veri klasörü `%LOCALAPPDATA%\Nexus`; `NEXUS_DATA_DIR` bunu değiştirebilir.
Ayarlar, `nexus.db` ve araç bilgileri burada bulunur. SQLite izin ve denetim kayıtlarını
da içerir. Nexus dosyaları şifrelemez; Windows hesabını ve yedekleri koru. Supertonic
dosyaları projedeki `models/` klasöründe, Whisper modeli önbellekte tutulur.
Python paketleri ve model kurulumu internet kullanır.

Ses ayarları Whisper'ı mikrofon açmadan doğrulayabilir. Model hazırlığı dinleme/bulut
izinlerini veya seçili dil modelini değiştirmez. İşlemi durdurmak ya da ayarları
kapatmak hazırlama sürecini sonlandırır; önbellekteki/kısmi indirmeler kalabilir.
Ayarlardan vazgeçmek, ayrıca onaylanmış model indirmesini geri almaz.

Sağlayıcı adreslerini aynı bilgisayarda tut. Kayıtlı “yerel” etiketi güvenlik duvarı
değildir; özel uzak URL, verinin alıcısını değiştirir. CORS kimlik doğrulama değildir.
Mevcut API kimlik doğrulamasızdır; yerel ağa, herkese açık tünele veya çok kullanıcılı
hizmete dönüştürme. Başka yerel süreçler API'ye ulaşabilir.

Araç izinleri ve dosya kapsamları uygulama kontrolleridir; MCP programını işletim
sistemi düzeyinde yalıtmaz. Yalnızca güvendiğin araçları çalıştır. Maskeleme her hassas
değerin kayıtlardan silineceğini garanti etmez. Özel oturum; araçları yalıtmaz, izinli
web/bulut sesini kapatmaz, hafızayı şifrelemez veya sağlayıcı kayıtlarını silmez.
Çökme sonrasında geçici ses dosyaları kalabilir; özel oturum sıfır iz garantisi değildir.

## Kullanıcı kontrolleri

- Pano için sor/izin ver/engelle tercihleri vardır; gereksiz geniş izin verme.
- Web ve bulut sesi ayrı izin ister; yalnızca çevrimdışı çalışmak için kapat.
- Hafıza kullanımı, aday çıkarma ve geçmişe başvurma birbirinden bağımsızdır.
- Adayları etkinleştirmeden önce incele; hafıza yöneticisinden düzenle/sil.
- Sohbet ve belgeleri ilgili kontrollerden sil. Sohbeti silmenin ayrıca onaylanmış
  kişisel hafıza kayıtlarını da sildiğini varsayma.
- Arka plan dinlemesini pencere/tepsiden duraklat veya Nexus'tan çık. Gizlemek çıkmak değildir.

Veritabanı, `.env`, MCP yapılandırması, hafıza dışa aktarımı, ses kaydı veya ham
destek günlüğü yayımlama. Bildirimlerde [yapay örnek belgeyi](demo/project-brief.md)
kullan. Açık bildirimleri için [güvenlik politikasına](../SECURITY.tr.md) bak.
