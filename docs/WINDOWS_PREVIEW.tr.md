# Windows kurulum önizlemesi

**Türkçe** · [English](WINDOWS_PREVIEW.md) · [Belgeler](INDEX.md)

Nexus artık yeniden üretilebilir bir Windows kurulum paketi ve üç adımlı ilk açılış
ekranı içeriyor. Bu, yerel geliştirme önizlemesidir; yayımlanmış veya imzalanmış sürüm değildir.

## Kullanıcı için

1. Yerel olarak verilen `NexusSetup.exe` dosyasını açıp Windows hesabın için kur.
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

Temiz bir Windows Python 3.11–3.13 ortamı kullan. `requirements-dev.txt`,
`requirements-tts.txt` ve `pyinstaller>=6.22,<7` bağımlılıklarını kur. Resmi Inno Setup 6
derleyicisini ayrıca kur. Proje kökünde:

```powershell
python -m scripts.build_windows --compiler "C:\derleyici\Inno Setup 6\ISCC.exe"
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

## Herkese yayımlamadan önce

- [PyQt/Qt ve bağımlılık dağıtım incelemesini](../THIRD_PARTY_NOTICES.tr.md) tamamla.
  Pakette Nexus kaynak kodu, bulunabilen lisans metinleri ve derleme ortamının kesin
  sürüm listesi bulunur; bu liste tamamlanmış dağıtım denetimi değildir.
- Temiz Windows bilgisayarında kurma, güncelleme, iptal ve kaldırmayı test et.
- Gerçek LM Studio/Ollama yanıtını ve isteğe bağlı model indirmesi, ses çözümleme ve
  seslendirmeyi test et.
- Yerel kitaplıkları ve modelleri ayrı incele. Model dağıtım hakkı varsayılmaz.
- Kurulumu imzala veya imzasız olduğunu açıkça belirtip bağımsız doğrulanabilir
  sağlama değerleri sun. Resmi imzalı sürüm olarak tanıtma.

Projeye ait kaynak kod MIT olarak kalır. Bağımlılıklarla birleşen paket yalnızca MIT
olarak tanımlanamaz. Yerel derleme, herkese dağıtımın açık kontrollerini tamamlamaz.
