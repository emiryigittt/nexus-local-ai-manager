# Windows dağıtım lisansı

[English](DISTRIBUTION_LICENSE.md) · **Türkçe**

Birleşik Nexus Windows uygulaması **GNU GPL sürüm 3** kapsamında dağıtılır
([tam metin](COPYING)). Nexus tarafından yazılan kaynak kod [MIT lisansını](LICENSE)
korur. MIT telif ve izin bildirimi bu kaynak için geçerlidir. Üçüncü taraf
bileşenler kendi lisanslarını ve telif bildirimlerini korur; bu belge onların
lisansını değiştirmez. [Üçüncü taraf bildirimlerine](THIRD_PARTY_NOTICES.tr.md) bakın.

Birleşik uygulamayı GPL koşullarıyla çalıştırabilir, inceleyebilir, değiştirebilir
ve yeniden dağıtabilirsiniz. Ek bir kullanım sözleşmesi, etkinleştirme anahtarı,
imza zorunluluğu veya değişikliklerin hata ayıklaması için tersine mühendislik
yasağı bulunmaz. Uygulama ilgili lisanslarda açıklandığı gibi garanti verilmeden sunulur.

Kurulum paketinde `distribution-notices`, tam Nexus kaynak kodu ve üçüncü taraf
lisans metinleri bulunur. **Araçlar → Nexus hakkında ve lisanslar** bu dosyaları açar.
Sürümde ayrıca bağımlılıkların kaynak arşivleri, tam sürüm ve SHA-256 listeleri,
derleme talimatları sunulur. İkili paket ile eşleşen kaynakları aynı
[GitHub sürümünden](https://github.com/emiryigittt/nexus-local-ai-manager/releases/tag/v0.3.0-beta.2)
indirin. Yeniden dağıtanların bildirimleri koruması ve ilgili kaynak sunma
yükümlülüklerini karşılaması gerekir. Kaynak sunma yöntemi yalnızca üst projeye
bağlantı vermek değildir; kaynak arşivleri de sürümde sunulur.

Qt ve medya kütüphaneleri dinamik bağlanır. Nexus'u yeniden derleyebilir,
uygulama klasöründeki uyumlu DLL'leri değiştirebilir ve değiştirilmiş derlemeyi
ilgili lisanslarla dağıtabilirsiniz. Kurulum yetkilendirme bilgisi gerekmez.
Derleme imzasızdır. Windows sistem kütüphaneleri karşılık gelen kaynağın dışında
kalır; Microsoft çalışma zamanı dosyalarının özgün koşulları geçerlidir.

LLM, Whisper ve Supertonic model ağırlıkları ayrıca indirilir veya kullanıcı
tarafından sağlanır; kendi koşullarını korur. faster-whisper'ın taşıdığı küçük,
MIT lisanslı Silero VAD varlığı bağımlılık listesine dahildir.
