# Windows kurulumu ve kaynaktan derleme

**Türkçe** · [English](WINDOWS_PREVIEW.md) · [Belgeler](INDEX.md)

Nexus Beta 2, [GPL dağıtım koşullarıyla](../DISTRIBUTION_LICENSE.tr.md)
Windows x64 kurulum paketi sunar. İmzasızdır ve beta aşamasındadır.
Kurulumu ve eşleşen kaynakları
[sürüm sayfasından](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.2) indirin.

## Kullanıcı için

1. Sürümdeki `NexusSetup.exe` dosyasını açıp Windows hesabın için kur.
   Python veya terminal gerekmez. Hedef Windows 10/11 x64'tür.
2. Başlat menüsünden Nexus'u aç. Türkçe veya İngilizceyi seç.
3. LM Studio, Ollama veya llama.cpp'yi aç; o uygulamada bir model indirip yükle.
   Nexus bu bilgisayardaki sunucuları otomatik arar. Bulamazsa ekrandaki adımları
   uygula ve **Yeniden tara** düğmesine bas.
4. Model seç, **Bağlantıyı test et** düğmesine bas. Gerçek yanıt gelince **Nexus'u aç**.
   **Daha sonra** ile kayıtlı ayarları değiştirmeden çıkabilir, karşılama ekranındaki
   **Bağlantı kurulumu** düğmesiyle geri dönebilirsin.
5. **Örnek belgeyle dene** düğmesine basıp hazırlanan soruyu gönder. Kurgu proje
   belgesi yerel belge kitaplığına eklenir; otomatik üretilmiş yanıt gösterilmez.

İsteğe bağlı ses için **Ayarlar → Ses** bölümüne git. **Hey Nexus** sekmesindeki
model hazırlığı normal konuşmayı yazıya çevirmeyi de hazırlar. Supertonic hazırlığı
ve indirme ilerlemesi **Yanıt sesi** sekmesindedir. İndirme açık bir işlem ve onay
gerektirir; dinlemeyi veya bulut sesini etkinleştirmez. Kontroller modeli çevrimdışı
yükler; fiziksel mikrofonu veya hoparlörü test etmez. Durdurma veya ayarları kapatma,
hazırlık işlemini durdurur. Kısmi indirmeler önbellekte kalabilir. Windows sesi için
Supertonic indirmen gerekmez.

Veriler kurulumdan ayrı olarak `%LOCALAPPDATA%\Nexus` altında tutulur; `NEXUS_DATA_DIR`
ile değiştirilebilir. Kaldırma; sohbetleri, ayarları ve indirilen modelleri korur.
Bu klasörü yalnızca Nexus'u bilerek sıfırlamak istediğinde sil. Kurulum paketi dil
modeli, Whisper/Supertonic ağırlıkları içermez ve model sunucusu kurmaz.

## Paketi üretme ve kontrol

Temiz Windows x64 ortamında **Python 3.12.10** ve
[tam sürüm listesini](../packaging/windows-build.lock.txt) kullanın. Resmî Inno Setup 6
derleyicisini ayrıca kurun. Proje kökünde:

```powershell
python -m pip install -r packaging/windows-build.lock.txt
python -m scripts.prepare_distribution
python -m scripts.build_windows --compiler "C:\yol\Inno Setup 6\ISCC.exe"
python -m scripts.check_windows_package --installer dist/installer/NexusSetup.exe
```

Çıktılar `dist/Nexus/Nexus.exe`, `dist/installer/NexusSetup.exe` ve kurulum dosyasının
yanındaki SHA-256 bildirimidir. Masaüstü paketi kitaplık klasörüyle çalışır; yalnızca
`Nexus.exe` dosyasını kopyalamak yeterli değildir. Kurulum dosyası bu klasörü içerir.
Kişisel ayarlar, veritabanları, kayıtlar, `.env` ve modeller pakete girmez. Derleme
araçları dağıtılan uygulamanın dışında kalır.

Yalıtılmış paket kontrolü için `NEXUS_DATA_DIR` değişkenini ayrı bir test klasörüne,
`QT_QPA_PLATFORM` değişkenini `offscreen` değerine ayarlayıp `Nexus.exe --self-test report.json`
çalıştır. Rapor API yüklemesini, üç kurulum adımını, logoyu ve örnek belgeyi kontrol eder.
Model yanıt kalitesini, ses donanımını veya paketli her işlevi doğrulamaz.

`python -m scripts.check_windows_package --installer dist/installer/NexusSetup.exe`
masaüstü, yerel API, örnek model bağlantısı, belge yükleme, kurma ve kaldırmayı yalıtılmış
olarak kontrol eder. Gerçek kullanıcı verisine dokunmaz; Nexus zaten kurulmuşsa kurulum
testini çalıştırmaz. `build/windows-package-check.json` raporunda test edilen kurulum
dosyasının sağlama değeri bulunur. Buradaki model sunucusu sabit bir test yanıtı verir;
yanıt kalitesini gerçek dil modeliyle ayrıca dene.

## Kaynaklar, bildirimler ve sınırlar

Sürümde kurulumla birlikte `Nexus-source.zip`, `Nexus-dependency-sources.zip`,
`dependency-sources.json`, `windows-package-check.json`, `release-manifest.json`
ve `SHA256SUMS.txt` sunulur. Kaynak listesi özgün arşivlerin tam sürümlerini ve
dosya özetlerini içerir. Bağımlılık arşivinde Python kaynakları, Qt modülleri,
FFmpeg ve codec'ler, PyAV derleme tarifleri ve eşleşen MSYS2 çalışma zamanı
kaynakları, yamaları ve paketleme tarifleri bulunur. Şifreleme veya imza anahtarına
bağlı kilit yoktur.

Değişiklik için Nexus kaynağını çıkarın, sabitlenmiş derleme ortamını kurun ve
yukarıdaki adımları uygulayın. Özgün arşivler derleme dosyalarını korur. Qt için
arşivdeki CMake/configure talimatları, PyQt için SIP talimatları kullanılabilir.
Yerel PyAV kütüphanelerinin derleme betikleri ve yamaları `pyav-ffmpeg-build`
arşivindedir. MSYS2 paketleri PKGBUILD tariflerini, yamaları ve özgün GCC/libiconv/
winpthreads kaynaklarını taşır. Medya yapılandırması `dependency-sources.json`
içindedir. Uyumlu DLL'ler `_internal` içinde yetkilendirme anahtarı olmadan değiştirilebilir.

Donmuş paket envanteri gerçekten paketlenen dosyalardan oluşturulur;
`build-environment.json` ayrı bir derleme envanteridir, sertifikalı SBOM değildir.
Yayın için birim kontrolleri, temiz kurulum, tekrar kurulum ve kaldırma kontrolleri
başarılı olmalıdır. Fiziksel mikrofon, gerçek model kalitesi, etkileşimli kurulumun
iptali ve tüm Windows yapılandırmaları otomatik testin kapsamı dışındadır.
Hey Nexus algılaması deneysel kalır; F2 elle giriş için kullanılabilir.
Bulut ses ve haricî araçlar açık onay/izin kontrollerini korur.
