# GitHub'a sıfırdan hazırlık

[English](GITHUB_SETUP.md) · **Türkçe** · [Belgeler](INDEX.md)

Bu dosya bir rehberdir; hesap açılmadı, program kurulmadı, dosyalar yüklenmedi.
Hesabın ve depo adresin belli olmadığı için README'de uydurma klonlama bağlantısı yok.

## 1. Hesabını oluştur

[GitHub kayıt sayfasında](https://github.com/signup) kullanıcı adını kendin seç,
e-postanı doğrula ve iki aşamalı doğrulamayı aç. Şifreni, doğrulama kodlarını ve
kurtarma kodlarını sohbete yazma; bu adımları kendin tamamla.
[Resmî hesap rehberi](https://docs.github.com/en/account-and-profile/how-tos/account-management/creating-an-account-on-github).

## 2. GitHub Desktop ile yerel projeyi aç

İstersen terminal yerine [GitHub Desktop](https://desktop.github.com/) kullan.
Kurulumdan sonra kendi hesabınla giriş yap. **File → Add local repository** ile
mevcut Nexus klasörünü seç; başka bir boş klasör oluşturmana gerek yok. Bu çalışma
klasöründe Git altyapısı zaten var; `.git` klasörünü silme veya yeniden başlatma.
[Resmî yerel depo rehberi](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-a-repository-from-your-local-computer-to-github-desktop).

## 3. İlk kayıt öncesi kontrol

- README'deki iki dili ve ekran görüntüsünü incele.
- `.env`, sanal ortamlar, model dosyaları, ses kayıtları, SQLite veritabanları,
  kişisel ekran görüntüleri ve MCP yapılandırmaları değişiklik listesinde olmamalı.
- `output/pdf/` ve `tmp/pdfs/` içindeki kişisel belge çıktıları silinmeden paylaşım
  dışında tutulur; zorla Git'e ekleme. Ön kontrol, takip edilen dosyalarda da bu
  yolları denetler; paylaşım dışı dosyalara verilen bağlantıları reddeder.
- `scripts/check_public_repo.py` kontrolünü çalıştır. Bu araç basit bir ön denetimdir;
  kapsamlı sır taraması veya geçmiş denetimi yerine geçmez.
- Desktop'ta her dosyayı gözden geçir; sadece hazırlanan kaynak/dokümanları kaydet.
  İlk kayıt açıklaması örneği: `Prepare Nexus development preview`.
- Commit e-postanın gizliliğini hesap ve Desktop ayarlarında kontrol et.
- Projenin lisansını değiştirmeden [üçüncü taraf notlarını](../THIRD_PARTY_NOTICES.tr.md) incele.

## 4. Önce özel depo, sonra açık kaynak yayını

İlk kontrol için öneri: **Publish repository** penceresinde depo adını seç ve
**Keep this code private** işaretli bırak. `nexus` kullanılabilecek bir ad önerisidir;
seçim sana aittir. Bu işlem dosyaları GitHub'a yükler; yerel commit ile aynı şey değildir.
[Resmî yayınlama rehberi](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-an-existing-project-to-github-using-github-desktop).

Yüklemeden önce tüm geçmişi de kontrol et: sonradan bir sırrı silmek önceki commit'ten
silmez. Henüz uzak depo adresi yapılandırılmadığı için bu hazırlıkta hiçbir uzak depo
silme/değiştirme işlemi yapılmadı.

Özel depoda CI sonuçlarını ve temiz kurulum denemesini kontrol et. Açık kaynak yayını
için aşağıdaki kapılar kapanınca görünürlüğü birlikte değerlendirebiliriz:

- [ ] Gerçek modelle hafıza ve günlük kullanım testi.
- [ ] Temiz Windows ortamında kurulum; GitHub CI sonuçları.
- [ ] PyQt/Qt ve model dağıtım koşulları için karar ve gerekli bildirimler.
- [ ] Dosya, görüntü ve Git geçmişinde kişisel veri/sır incelemesi.
- [ ] Gerçek demo ve doğru sınırlama açıklamaları.
- [ ] Proje sahibinin herkese açık yayın onayı.

## 5. Depo oluşturulduktan sonra

- Açıklama taslağı: “A Windows desktop assistant for your local AI model — documents,
  voice, and user-controlled memory, one shortcut away.”
- Gerçek depo URL'sini README kurulumuna ve demo bitiş kartına ekle.
- CI başarılı olduktan sonra gerçek duruma bağlı CI rozeti eklenebilir.
- [İlk görev taslaklarını](GOOD_FIRST_ISSUES.tr.md) issue olarak açıp uygun etiketleri oluştur.
- Kullanıcı soruları için Discussions aç; henüz açılmamış bir destek kanalına link verme.
- Güvenlik bildirimleri için özel raporlamayı aç ve bildirimleri kontrol et.
  Bu özellik ayrıca etkinleştirilmelidir; SECURITY dosyasının varlığı yetmez.
  [Resmî özel raporlama rehberi](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
- Topluluk davranış bildirimleri için sahibinin seçtiği özel iletişim kanalını ekle.
- İlk pilot geri bildirimleri sonrası [yaygınlaştırma planını](GITHUB_LAUNCH_PLAN.md) uygula.

Windows kurulum paketi bu hazırlığın parçası değildir; özellikler kararlı hale gelince ele alınacak.
