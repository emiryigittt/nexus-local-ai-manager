# İlk katkı görevi taslakları

[English](GOOD_FIRST_ISSUES.md) · **Türkçe** · [Belgeler](INDEX.md)

Bunlar yayımlanmış GitHub issue'ları değil, yerel taslaklardır. Sorumlular kapsamı
doğrulayıp yayın sonrasında `good first issue` / `help wanted` etiketlerini eklemelidir.
Büyük değişiklikten önce tek görev seçip kapsamı konuş.

## 1. İlk kullanımda hafıza onayını açıkla

Önerilen etiketler: documentation, good first issue.
Sorun: aday kayıt, yeni kullanıcıya hafıza kaydedilmemiş gibi görünebilir.
Kapsam: kullanım rehberine yapay verili, ekran görüntülü kısa anlatım ekle.

Kabul ölçütleri:

- Geçici verilerle aday, etkin ve devre dışı durumlarını göster.
- Hafıza kullanımı ile otomatik aday çıkarmanın bağımsızlığını açıkla.
- Onay ve silmeyi göster; kendiliğinden etkinleştiğini söyleme.
- İki dilde anlatımı eşleştir; yayın ön kontrolünü çalıştır.

## 2. Mesaj alanındaki erişilebilir adları denetle

Önerilen etiketler: accessibility, good first issue.
Kapsam: `frontend/spotlight_view.py` içindeki ekle, araştır, araçlar, mikrofon ve
gönder kontrolleri. Arayüzü yeniden tasarlama veya bağımlılık ekleme.

Kabul ölçütleri:

- Her kontrolün anlamlı erişilebilir adı, gerektiğinde açıklaması olsun.
- Adlar ve klavyeyle erişim için küçük Qt testi ekle.
- Narrator denendiyse gerçek bulguları kaydet; ekran dışı testleri ekran okuyucu testi sayma.
- Mevcut kısayolları ve yerleşimi koru.

## 3. Türkçe metin parçalama testleri ekle

Önerilen etiketler: tests, good first issue.
Kapsam: `backend/speech_chunks.py` ve testleri. Yapay metin kullan; ses modeli indirme.

Kabul ölçütleri:

- Yaygın kısaltmalar, ondalık sayılar, numaralı listeler ve bölünmüş metin parçalarını kapsa.
- Metnin kaybolmadığını/tekrarlanmadığını ve parça uzunluğu sınırını doğrula.
- Desteklenmeyen sınır durumlarını testleri gevşetmek yerine belgele.
- Ağ, mikrofon ve kurulu ses modeli gerektirme.

## 4. İngilizce arayüz çevirisini sohbet geçmişine genişlet

Önerilen etiketler: localization, help wanted; başlangıç düzeyi olmak zorunda değil.
Ana pencere pilotu tamamlandı. Kapsam: `frontend/i18n.py` yapısını kullanarak yalnızca
geçmiş penceresini çevir; arama, seçim ve silme davranışlarını koru.

Kabul ölçütleri:

- Kayıtlı dil tercihini uygula; Türkçeyi desteklemeyi sürdür.
- İş mantığı veya kısayollara sabit dil seçimi koyma.
- Her iki dili test et; görüntüleri yapay verilerle güncelle.
- Kontrolleri ve onayları çevir; sohbet başlıklarını veya mesaj içeriğini çevirme.
- Bu sınırlı iş sonunda tüm uygulama çevrilmiş gibi anlatma.
