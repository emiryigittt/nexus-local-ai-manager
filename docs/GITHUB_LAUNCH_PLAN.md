# GitHub topluluk ve duyuru planı

[English](GITHUB_LAUNCH_PLAN.en.md) · **Türkçe** · [Belgeler](INDEX.md)

26 Eylül 2026 · Taslak; henüz yayın, hesap değişikliği veya paylaşım yapılmadı.
Windows kurulum paketi özellikler kararlı hale geldikten sonra hazırlanacak.

## Yerel hazırlık — tamamlanan işler

- [x] İngilizce README ve Türkçe eş sayfa; güncel, yapay içerikli arayüz görüntüsü.
- [x] Kaynak koddan hızlı başlangıç, kullanım/sorun giderme ve gizlilik rehberleri.
- [x] Kişisel veri içermeyen demo belgesi ve kayıt senaryosu (video henüz çekilmedi).
- [x] Dört katkı görevi taslağı; hata/PR şablonlarında doğrulama ve gizlilik alanları.
- [x] Çalışma ağacı için dosya, belirgin sır ve yerel bağlantı ön kontrolü; CI'a ekleme.
- [x] Eski kişisel görüntüleri ve çalışma verilerini Git dışında tutan kurallar.
- [x] Lisans envanteri başlangıcı; PyQt/Qt ve model dağıtım kararlarını açık tutma.
- [x] [GitHub'a sıfırdan başlama rehberi](GITHUB_SETUP.tr.md).

Hazır dosyalar: [English](../README.md), [Türkçe](../README.tr.md),
[kullanım](USER_GUIDE.tr.md), [gizlilik](PRIVACY.tr.md), [demo](DEMO_SCRIPT.tr.md),
[katkı işleri](GOOD_FIRST_ISSUES.tr.md), [lisans notları](../THIRD_PARTY_NOTICES.tr.md).
Hiçbir hesap/depo oluşturulmadı; commit, push veya dış paylaşım yapılmadı.

Önceki hazırlık kontrolü: 187 yerel test başarılı; Ruff temiz; dört GitHub YAML dosyası ayrıştırıldı.
Git'e görünür 123 dosyada ön kontrol bulgusu yok. Bu, tüm sır türlerinin, görüntü
içeriklerinin, Git geçmişinin, dış bağlantıların veya GitHub sunucusunda iş akışının
doğrulandığı anlamına gelmez. Son testte Windows kapanış uyarısı görülmedi; aralıklı
olduğu için ilgili açık iş kapatılmadı.

## Konumlandırma

### İki dilli yayın hazırlığı

- [x] 13 İngilizce/Türkçe belge çifti ve [ortak belge dizini](INDEX.md).
- [x] Her README kendi dilindeki kullanım, gizlilik ve katkı belgelerine yönleniyor.
- [x] Hata/özellik/PR şablonları iki dilde kullanılabiliyor.
- [x] [Tanıtım ve pilot daveti metinleri](LAUNCH_COPY.tr.md) iki dilde hazır; paylaşılmadı.
- [x] Eş dosyalar ve karşılıklı dil bağlantıları yayın kontrolünde sınanıyor.
- [ ] İngilizce uygulama arayüzü ve iki dilde gerçek demo çekimi tamamlanacak.

İki dilli hazırlık doğrulaması: 194 test geçti, Ruff temiz, dört YAML dosyası geçerli.
138 Git'e görünür dosyada ön kontrol bulgusu yok. Bilinen aralıklı Windows asyncio
kapanış uyarısı tekrar görüldü; ilgili iş açık kalıyor. Belge eşleme testi yalnızca
dosya/dil bağlantılarını doğrular, çevirinin anlamsal eşitliğini garanti etmez.

İngilizce ana giriş olacak; Türkçe bağlantı görünür kalacak. Belge çevirisini tüm
arayüzün çevrilmiş olması veya görünürlük garantisi olarak sunmayacağız.

### Ana mesaj

27 Eylül son kontrolü: kişisel belge/fotoğraf çıktıları silinmeden paylaşım dışında
tutuldu. Paylaşım dışı dosyalara bağlantı denetimi eklendi. 199 test ve Ruff geçti;
138 paylaşım adayında ön kontrol bulgusu yok. Son çalışmada kapanış uyarısı görülmedi,
ancak aralıklı sorun kapanmış sayılmadı. Hiçbir dosya GitHub'a yüklenmedi.

Önerilen ana mesaj: “Seçtiğin yerel modele masaüstünde iş yaptıran, kişisel hafızası
senin kontrolünde olan sade bir asistan.” Ayırt edici nokta yalnızca sohbet değil:
klavye ile hızlı erişim, belgeyle çalışma, kaynakları görülen kişisel hafıza ve
isteğe bağlı yerel sesin tek günlük iş akışında birleşmesi.

Yıldız veya Trending sırası garanti edilemez. İlk hedef: kullanıcıların kurulumu
tamamlaması, gerçek bir işi çözmesi ve bir hafta sonra yeniden kullanması.
Bu geri bildirimler gönüllü alınmalı; gizli telemetri eklenmemeli.

## Sıralı teslimler

1. **Güvenilirlik kapısı.** Ses/hafıza raporundaki gerçek model ve kullanıcı testlerini
   tamamla. Deneysel wake-word, lisanslar ve bilinen sorunlar görünür kalsın.
2. **60–90 saniyelik gerçek demo.** Alt+Space → belge özeti → sesli yanıt → bir
   tercihi hafızaya aday çıkarma → onay → yeni oturumda hatırlama. Gerçek süreleri
   saklamadan, yapay örnek verilerle kaydet. Yerel/bulut ayrımını ekranda göster.
3. **Türkçe/İngilizce başlangıç.** README'nin ilk ekranında değer önerisi, demo,
   desteklenen ortam, kısa kurulum ve bir başarılı kullanım örneği. Python-free
   kurulum hazır değilken varmış gibi anlatma. Donanım ve model sürümleriyle
   ölçümler; izin/veri tablosu ve sorun giderme rehberi ekle.
4. **Katkı girişleri.** Mevcut CONTRIBUTING, SECURITY, issue şablonları ve CI'ı
   gözden geçir. Çeviri, erişilebilirlik ve ses test örnekleri için küçük, açık
   kabul ölçütlü `good first issue` işleri hazırla. Bu etiket GitHub'ın katkı
   fırsatlarını öne çıkarmasına yardımcı olabilir.
   [GitHub katkı etiketleri](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/encouraging-helpful-contributions-to-your-project-with-labels)
5. **Topluluk alanı.** Kullanıcı sorularını hatalardan ayırmak için Discussions
   içinde Q&A, fikirler ve örnek iş akışları kategorileri açılmasını öner.
   Açma işlemi yayın aşamasında sahibinin onayıyla yapılır.
   [GitHub Discussions rehberi](https://docs.github.com/en/discussions/quickstart)
6. **Keşfedilebilirlik.** Gerçek yetenekleri karşılayan `local-ai`, `desktop-assistant`,
   `ollama`, `lm-studio`, `voice-assistant`, `windows`, `python` konuları ve net depo
   açıklaması kullan. Konular benzer depoların bulunmasını kolaylaştırır; ilgisiz
   anahtar kelime doldurma yok.
   [GitHub topics rehberi](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
7. **Küçük pilot, sonra duyuru.** Önce 5–10 gönüllüyle kurulum ve günlük iş akışı
   denemesi; kritik sorunları düzelt. Ardından ilgili yerel-AI/açık-kaynak
   topluluklarının o günkü paylaşım kurallarını kontrol ederek geliştirici
   kimliğini açıklayan demo paylaşımı hazırla. Toplu mesaj, yıldız satın alma veya
   karşılıklı yıldız kampanyası yapma.
8. **Sürdürülebilir devam.** Düzenli kısa sürüm notları, tekrarlanabilir hata
   örnekleri ve katkı sahiplerine teşekkür. İlk yanıta kadar süre, çözülmüş
   kurulum engelleri ve gönüllü tekrar kullanım geri bildirimiyle ilerlemeyi değerlendir.

## Yayın kontrol listesi

- [ ] Gerçek yerel modelle hafıza ve ses kabul testleri tamamlandı.
- [x] Doğallık/gecikme sınırlamaları ve deneysel özellikler açıkça yazıldı.
- [ ] Model, bağımlılık ve örnek ses lisansları dağıtım için incelendi.
- [x] İki dilde hızlı başlangıç hazır.
- [ ] Gerçek demo çekildi ve gözden geçirildi.
- [ ] Temiz Windows ortamında belgelenmiş geliştirici kurulumu denendi.
- [x] İlk katkı işleri taslakları hazır.
- [ ] Gerçek issue'lar, Discussions, özel güvenlik ve davranış bildirim kanalları açıldı.
- [ ] Yerel API kimlik doğrulaması ve güvenilmeyen sağlayıcı adresleri için sertleştirme değerlendirildi.
- [ ] Depo/paylaşım içeriğinde kişisel veri ve sır bulunmadığı doğrulandı.
- [ ] Depo sahibi yayın ve dış paylaşımı onayladı.
