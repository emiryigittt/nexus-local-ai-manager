# Üçüncü taraf yazılım ve model notları

[English](THIRD_PARTY_NOTICES.md) · **Türkçe** · [Belgeler](docs/INDEX.md)

26 Eylül 2026 tarihli hazırlık envanteridir; tam dağıtım denetimi veya hukuki görüş
değildir. Nexus'a ait kaynak kod [MIT](LICENSE) olarak kalır. Bu; bağımlılık, model,
ses, veri kümesi, ikon veya görüntü lisansını değiştirmez. Bu belge LICENSE çevirisi değildir.

## Dağıtımda dikkat gerektiren bileşenler

| Bileşen | Kaynak bilgisi | Paket dağıtımından önce |
| --- | --- | --- |
| PyQt6 | GPL v3 veya ticari lisans; LGPL değil. Paketlenmiş Qt'nin ayrı koşulları var. [Resmî bilgi](https://www.riverbankcomputing.com/software/pyqt/intro) | Uygun dağıtım yaklaşımını belirle, bildirimleri koru, tüm bileşimi incele. Paketin tamamını yalnızca MIT diye tanımlama |
| Supertonic | Örnek kod MIT, model OpenRAIL-M; ana depo arşivli. [Kaynak](https://github.com/supertone-oss-archive/supertonic) | İndirilen tam sürümü, kısıtları ve bildirimleri doğrula; sağlama toplamını kaydet |
| sherpa-onnx model paketi | Nexus nicemlenmiş modeli [üst proje sürümlerinden](https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models) indirir | Dönüştürülmüş dosyanın bildirimlerini özgün modelle karşılaştır; motor ve ağırlıklar ayrı |
| Whisper / faster-whisper | Motor ve indirilen model ayrı dosyalardır. [Motor kaynağı](https://github.com/SYSTRAN/faster-whisper) | Gerçek sürümleri, model kökenini ve lisans dosyalarını kaydet |
| Edge sesi | İstemci kitaplığı üzerinden çevrimiçi hizmet | Hizmet koşulları/erişilebilirliğini istemci lisansından ayrı incele; hizmet seslerini yeniden dağıtma |
| Seçili LLM / embedding modelleri | Bu depo dışında seçilir | Her modelin koşulları/lisansı ayrıca kontrol edilir; Nexus ağırlıklar için hak vermez |

Bağımlılıklar [requirements.txt](requirements.txt), [requirements-tts.txt](requirements-tts.txt)
ve [requirements-dev.txt](requirements-dev.txt) içindedir. Sürüm aralıkları kilitlenmiş
yazılım envanteri değildir. Qt medya kodekleri, yerel paketler ve dolaylı bağımlılıklar
gerçek dağıtım için ayrıca listelenmelidir.

## Görseller

README, `docs/assets/voice-memory/` altındaki yapay metinli uygulama önizlemesini
kullanır. Görüntüdeki Windows yazı tipleri dosya olarak paketlenmez. Eski kök dizin
görüntüleri silinmedi; varsayılan olarak Git dışında tutulur. Her yeni görüntüyü
kaydetmeden önce kişisel veri açısından incele.

## Açık kontroller

- [ ] PyQt/Qt dağıtım yaklaşımını proje sahibiyle belirle; sessizce lisans değiştirme.
- [ ] Gerçek doğrudan/dolaylı bağımlılık sürümleri ve gerekli lisans metinlerini listele.
- [ ] Model dosyalarını uygulama kodundan ayrı listele ve sağlama toplamlarını al.
- [ ] Demo sesi ve referans kayıtlarının haklarını/izinlerini doğrula.
- [ ] Çalıştırılabilir dosya veya kurulum paketi öncesinde dağıtım incelemesini bitir.

Bu hazırlık lisansı değiştirmez; kurulum paketi veya model dağıtımı yapmaz.
