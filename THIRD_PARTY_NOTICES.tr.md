# Üçüncü taraf yazılım ve model bildirimleri

[English](THIRD_PARTY_NOTICES.md) · **Türkçe** · [Belgeler](docs/INDEX.md)

Birleşik Windows Beta 2 dağıtımı [GNU GPL sürüm 3](DISTRIBUTION_LICENSE.tr.md)
kapsamındadır. Nexus'un kendi kaynak kodu [MIT](LICENSE) lisansını korur.
Üçüncü taraf telif ve lisans bildirimleri korunur; bağımlılıkların ve ayrıca
indirilen modellerin lisansları değiştirilmez.

## Dağıtım girdileri

[Sabitlenmiş Windows derleme listesi](packaging/windows-build.lock.txt) Python
paketlerinin tam sürümlerini kaydeder. [Kaynak listesi](packaging/dependency-sources.json)
değişmez arşiv bağlantılarını, SHA-256 özetlerini, yerel medya yapılandırmasını ve
çalışma zamanı eşleşmelerini kaydeder. Kaynak arşivleri kurulumla aynı sürümde
`Nexus-dependency-sources.zip` içinde sunulur; yalnızca üst projeye bağlantı verilmez.
Wheel ve kaynak arşivlerindeki özgün lisans/telif metinleri
`distribution-notices/licenses` içindedir. Nexus kaynağı
`distribution-notices/nexus-source.zip` ve sürümdeki `Nexus-source.zip` içindedir.
**Araçlar → Nexus hakkında ve lisanslar** bildirimleri ve kaynak erişimini açar.

| Dağıtılan bileşen | Koşullar ve eşleşen kaynak |
| --- | --- |
| PyQt6 6.11.0 / SIP 13.12.0 | PyQt için GPLv3 yolu seçildi; tam PyPI kaynakları ve GPL metni sunulur. [Riverbank](https://www.riverbankcomputing.com/software/pyqt/intro) |
| Qt çalışma zamanı 6.11.2 | Qt base, multimedia, SVG, image formats ve translations kaynakları ile özgün LGPLv3/GPLv3/serbest lisans bildirimleri sunulur. DLL değiştirme ve yeniden derleme mümkündür. [Qt yükümlülükleri](https://www.qt.io/development/open-source-lgpl-obligations) |
| PyAV 19.0.0 ve FFmpeg 9.0.2 | PyAV BSD-3-Clause; FFmpeg GPL x264/x265 ve diğer codec'leri içerir. Kaynaklar, başlıklar, tarifler ve yamalar sunulur. FFmpeg çalışma zamanı lisans yazısı LGPL gösterse de birleşik uygulama GPLv3 kullanır. [PyAV tarifleri](https://github.com/PyAV-Org/pyav-ffmpeg/tree/bac889417e26be29615cb6a3f38318151fed55cd), [FFmpeg](https://ffmpeg.org/legal.html) |
| Qt FFmpeg 7.1.5 / zlib 1.3.1 | FFmpeg LGPL-2.1-veya-sonrası, dinamik DLL'ler; tam kaynak ve kaydedilmiş yapılandırma sunulur. zlib bildirimi korunur |
| GCC / libstdc++ çalışma zamanı 16.1.0-5 | GCC Runtime Library Exception içeren GNU koşulları; MSYS2 kaynakları, yamaları, tarifleri ve istisna metni sunulur |
| libiconv 1.19 / winpthreads | Özgün GNU/serbest lisans koşulları; yerel kod MSYS2 paketleriyle eşleştirildi, kaynak paketleri ve bildirimleri sunulur |
| edge-tts 7.2.8 | LGPLv3 istemci, tam kaynak sunulur. Çevrimiçi ses hizmetinin koşulları ayrıdır; hizmet sesleri yeniden dağıtılmaz |
| pyttsx3 2.99 / certifi / tqdm | Özgün MPL/serbest lisans koşulları korunur; tam kaynak arşivleri sunulur |
| Python 3.12.10 / PyInstaller | Python PSF lisansı ve özgün çalışma zamanı bildirimleri; PyInstaller GPL bootloader istisnası. Kaynaklar ve bildirimler sunulur |
| NumPy, OpenBLAS, ONNX Runtime, CTranslate2, sherpa-onnx, lxml, tokenizers ve diğerleri | Yerel bileşenlerin bildirimleri dahil özgün wheel/kaynak bildirimleri sunulur. Python girdileri ve gerçekten paketlenen dosyalar ayrı kaydedilir |
| Microsoft çalışma zamanı DLL'leri | Özgün Python/Qt/yerel wheel paketlerinin taşıdığı değiştirilmemiş yeniden dağıtılabilir dosyalar; Microsoft koşulları geçerlidir. Windows sistem kütüphaneleri haricîdir |

Kullanılmayan QtPdf/qpdf/yazılım OpenGL, SoundFile/libsndfile ve standart dışı
PortAudio arka uçları dışarıda bırakılır. Standart x64 PortAudio özgün lisansını korur.
Paketin `frozen-files.json` dosyası taşınan kaynakları ve DLL/PYD özetlerini listeler;
`build-environment.json` derleme girdileridir, sertifikalı SBOM değildir.
Bu envanter ve kaynak sunumu teknik dağıtım hazırlığıdır; bağımsız hukuk sertifikasyonu değildir.

## Modeller ve görseller

- faster-whisper küçük bir **MIT lisanslı Silero VAD** varlığı içerir. Kaynak arşivi
  ve telif bildirimi sunulur; paket envanterinde kaydedilir.
- LLM, Whisper ve Supertonic ağırlıkları pakette yoktur. Model hazırlama açık bir
  kullanıcı işlemidir. Supertonic modelinin OpenRAIL-M koşulları, sherpa-onnx'ın
  Apache çalışma zamanından ayrıdır. [Özgün Supertonic](https://github.com/supertone-oss-archive/supertonic),
  [dönüştürülmüş model dağıtımı](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models).
- Kullanıcının seçtiği dil/embedding modelleri kendi koşullarını korur; Nexus bu
  ağırlıklara hak vermez. Çevrimiçi sağlayıcıların ve araçların hizmet/gizlilik sınırları ayrıdır.
- Nexus için oluşturulan arayüz sesleri ve görseller proje kaynağıyla sunulur.
  Ekran görüntüleri yapay metin içerir. Windows fontları font dosyası olarak paketlenmez.

Kurulum imzasızdır; uygulama garanti verilmeden sunulur. Sürüm dosyaları sağlama
değerlerini ve temiz Windows kontrol raporunu içerir. Gelecek dağıtımlarda yeni
bağımlılık sürümlerini, yerel bileşenleri ve modelleri yeniden inceleyin;
sabitlenmiş liste Beta 2'ye özgüdür. [Derleme ve doğrulama rehberi](docs/WINDOWS_PREVIEW.tr.md).
