"""Small explicit UI catalog; never translate prompts, model output or provider IDs."""

from weakref import ref

from PyQt6 import sip

ENGLISH = {
    "Nexus hakkında ve lisanslar": "About Nexus and licenses",
    "Dengeli · hızlı yerel model": "Balanced · fast local model",
    "Göndermeden önce metni kontrol et": "Review text before sending",
    "Metin hazır. Düzenleyip Enter ile gönderebilirsin.": "Text is ready. Edit it and press Enter to send.",
    "Konuşma bitince otomatik gönder": "Send automatically when speech ends",
    "Başlat / durdur modunda kısa duraklamaları bekler, konuşma bitince kaydı sonlandırır. Basılı konuş modunda tuşu bırakmanız beklenir.":
        "In start/stop mode, waits through short pauses and ends capture when speech finishes. Push-to-talk waits for key release.",
    "Doğal konuşma · daha güçlü yerel model": "Natural speech · stronger local model",
    "Hızlı · hafif yerel model": "Fast · lightweight local model",
    "Konuşmayı anlama": "Speech recognition",
    "Doğal konuşma seçeneği daha fazla işlem gücü kullanır. Henüz hazırlanmadıysa mevcut hafif model kullanılır. Modeli aşağıdan hazırlayabilirsiniz; Hey Nexus izni gerekmez.":
        "Natural speech uses more processing power. The existing lightweight model is used until prepared. Prepare it below; Hey Nexus permission is not required.",
    "Konuşma modeli yerelde çalışır. Hazırlama işlemi mikrofonu açmaz.":
        "Speech recognition runs locally. Preparation does not open the microphone.",
    "Konuşma modelini hazırla…": "Prepare speech model…",
    "Konuşma modelini hazırla": "Prepare speech model",
    "Seçili modeli kontrol edin veya hazırlayın. Sesiniz buluta gönderilmez.":
        "Check or prepare the selected model. Your audio is not sent to the cloud.",
    "Seçili Whisper modeli Hugging Face üzerinden indirilir; internet ve yüzlerce MB disk alanı kullanabilir. İndirme sonrası konuşmalar yerelde çözümlenir. Mikrofon açılmaz, ses gönderilmez. Devam edilsin mi?":
        "The selected Whisper model downloads from Hugging Face, using internet and potentially hundreds of MB of disk space. Speech is then transcribed locally. No microphone or audio upload. Continue?",
    "Konuşma modeli hazırlanıyor… Mikrofon kapalı.": "Preparing speech model… Microphone off.",
    "Konuşma modeli indiriliyor… Mikrofon kapalı.": "Downloading speech model… Microphone off.",
    "Hazırlama durduruldu. Mikrofon kapalı; kısmi indirme önbellekte kalabilir.":
        "Preparation stopped. Microphone off; partial downloads may remain cached.",
    "Seçili konuşma modeli hazır. Kaydet düğmesiyle seçiminizi uygulayın.":
        "Selected speech model is ready. Click Save to apply your choice.",
    "Konuşma modeli hazır değil. Hazırla seçeneğini kullanın; internet ve disk alanını kontrol edin.":
        "Speech model isn't ready. Use Prepare; check your internet connection and disk space.",
    "Konuşma modeli hazır değil. Ayarlar → Ses → Giriş bölümünden modeli hazırlayın.":
        "Speech model isn't ready. Prepare it under Settings → Voice → Input.",
    "Mikrofon verisi geçersiz. Yeniden deneyin.": "Invalid microphone data. Try again.",
    "Çağrı ses eşiği": "Wake call threshold",
    "Kısa çağrılar için ayrı hassasiyet. Sessiz konuşmayı kaçırıyorsa azalt; ortam gürültüsü algılamayı yoruyorsa artır.":
        "Separate sensitivity for short wake calls. Lower it for quiet speech; raise it if background noise overloads detection.",
    "Ses eşiğine ulaşılmadı. Doğru mikrofonu seç veya Çağrı ses eşiğini azaltıp tekrar dene. Mikrofon kapalı.":
        "Audio stayed below the threshold. Choose the right microphone or lower the Wake call threshold and retry. Microphone off.",
    "Çağrıyı dene (5 sn)": "Try wake call (5 sec)",
    "Yalnızca tıklayınca mikrofon beş saniye açılır. Hey Nexus deyip durakla. Ses kaydedilmez veya gönderilmez.":
        "Click to open the microphone for five seconds. Say Hey Nexus and pause. Audio is never saved or sent.",
    "Mikrofon açık · şimdi Hey Nexus deyip durakla. Test beş saniyede biter.":
        "Microphone on · say Hey Nexus and pause. The test ends in five seconds.",
    "Hey Nexus algılandı. Test tamamlandı; mikrofon kapalı.":
        "Hey Nexus detected. Test complete; microphone off.",
    "Ses eşiğine ulaşılmadı. Doğru mikrofonu seç veya Giriş sekmesindeki ses eşiğini azaltıp tekrar dene. Mikrofon kapalı.":
        "Audio stayed below the threshold. Choose the right microphone or lower the threshold on the Input tab and retry. Microphone off.",
    "Ses geldi ama çağrı algılanmadı. Hey Nexus deyip kısa bir duraklama yaparak tekrar dene. Mikrofon kapalı.":
        "Audio arrived but the wake call wasn't detected. Say Hey Nexus, pause briefly and retry. Microphone off.",
    "Nexus ile tanış": "Meet Nexus",
    "Tanışalım": "Meet Nexus", "Tanışma": "Introduction",
    "Merhaba, {name}.": "Hello, {name}.",
    "Ben Nexus. Nasıl çalıştığını ve hedeflerini tanımak isterim.\nTanışalım mı?":
        "I'm Nexus. I'd like to learn how you work and what you're working toward.\nLet's get acquainted?",
    "Tanışma, kişisel hafızanı düzenler. Kullanmak için özel oturumdan çık.":
        "Introductions update your personal memory. Leave the private session to use this feature.",
    "Uygun anlarda beni tanımak için kısa sorular sor": "Ask brief questions to get to know me when it fits",
    "Hafıza: {enabled} · Otomatik öneriler: {learning}": "Memory: {enabled} · Automatic suggestions: {learning}",
    "açık": "on", "kapalı": "off",
    "Henüz bir otomatik hafıza işlemi yok.": "No automatic memory task yet.",
    "Son işlem: {count} yeni aday. Adayları seçip etkinleştirin.": "Latest task: {count} new suggestions. Review and approve them.",
    "{count} kayıt · {active} etkin · {candidates} aday": "{count} records · {active} active · {candidates} suggestions",
    "Görünüm": "Appearance", "Renk ve RGB": "Color and RGB",
    "Rengini seç. Karakteri ve ışığı önizlemede hemen gör.": "Choose a color. Preview your character and glow instantly.",
    "Senin rengin. Senin asistanın.": "Your color. Your companion.",
    "Renk kanalı": "Color channel", "Renk seç…": "Choose color…",
    "Yavaş RGB kenar ışığı": "Slow RGB edge glow",
    "Hareketi azalt açıkken RGB ışığı sabit kalır.": "RGB stays static when reduced motion is on.",
    "Yol arkadaşın": "Your companion", "Mini bot": "Mini bot", "Nexus kedisi": "Nexus cat",
    "Karakter": "Character", "Karakteri selamla": "Say hello",
    "Göz kırpar, dinler, düşünür ve konuşur. Uygulamanın gerçek durumunu takip eder.":
        "Blinks, listens, thinks and speaks. Follows the application's actual state.",
    "Küçük sesler": "Little sounds", "Arayüz ses efektlerini aç": "Enable interface sounds",
    "Ses düzeyi": "Volume", "Sesi dene": "Try sound",
    "Fareyle üzerine gelince ses çıkmaz. Sesler isteğe bağlıdır; konuşma sesi ayrı ayarlanır.":
        "Hovering is silent. Sounds are optional; speech is configured separately.",
    "Nexus · Kişisel Hafıza": "Nexus · Personal Memory",
    "Seni tanıyan bir hafıza": "A memory that knows you",
    "Kayıtlar bu bilgisayarda saklanır. Önerileri incele; neyi hatırlayacağına sen karar ver.":
        "Records stay on this computer. Review suggestions and choose what Nexus remembers.",
    "Kayıtlar": "Records", "Profil özeti": "Profile summary",
    "Nexus seni nasıl tanısın?": "How should Nexus know you?",
    "Tercihlerin ve çalışma biçimin hakkında kısa bir özet…": "A short summary of your preferences and how you work…",
    "Özeti kaydet": "Save summary", "Özet kaydedildi.": "Summary saved.",
    "Hafızada ara…": "Search memory…", "Hafıza kayıtları": "Memory records",
    "Tüm türler": "All types", "Tüm durumlar": "All statuses",
    "Tercih": "Preference", "Bilgi": "Fact", "Hedef": "Goal", "Talimat": "Instruction", "Proje kararı": "Project decision",
    "Onay bekliyor": "Awaiting approval", "Etkin": "Active", "Eski sürüm": "Previous version", "Devre dışı": "Disabled",
    "Kaydı incele": "Review record", "Hatırlanacak bilgi": "Information to remember",
    "Tür": "Type", "Durum": "Status", "Bu bilgiyi önceliklendir": "Prioritize this information",
    "Ayrıntılar": "Details", "Kapsam": "Scope", "Proje": "Project", "Proje kimliği": "Project ID",
    "Güven": "Confidence", "Önem": "Importance", "Kaynak": "Source", "Onayla": "Approve", "Unut": "Forget",
    "Henüz kayıt yok. Sohbette /remember ile bir bilgi ekleyebilirsin.": "No records yet. Add information with /remember in chat.",
    "Aramana uygun kayıt bulunamadı.": "No records match your search.",
    "Yenile": "Refresh", "Dışa aktar": "Export", "Tümünü sil": "Clear all", "Kapat": "Close",
    "Nexus sohbetini aç": "Open Nexus chat",
    "Üzerine gel: mini panel · Tıkla: sohbet": "Hover: mini panel · Click: chat",
    "Küçült · Esc": "Collapse · Esc",
    "Küçült": "Collapse",
    "Mini paneli sabitle": "Pin mini panel",
    "Sabitlemeyi kaldır": "Unpin mini panel",
    "Belgeyi veya görseli buraya bırak": "Drop a document or image here",
    "Nexus konuşuyor": "Nexus speaking",
    "Yanıt seslendiriliyor.": "Playing the response audio.",
    "Yerel kitaplığa eklendi · {name}": "Added to local library · {name}",
    "Eklediğim belgedeki önemli noktaları özetle.": "Summarize the key points in the document I added.",
    "Nexus'a yerel belge ekle": "Add a local document to Nexus",
    "Belge eklendi": "Document added",
    "Belge eklenemedi": "Could not add document",
    "Belge yalnızca yerel bilgi tabanına eklendi.": "The document was added to the local knowledge library only.",
    "Dosya okunamadı veya yerel Nexus bağlantısı kurulamadı. Dosyayı ve bağlantı ayarlarını kontrol et.":
        "Could not read the file or connect to local Nexus. Check the file and connection settings.",
    "Kontrol paneli": "Control panel",
    "Panel": "Panel",
    "Sohbet": "Chat",
    "Sohbeti aç": "Open chat",
    "Hafıza": "Memory",
    "Bir soru sor veya araç seç.": "Ask a question or choose a tool.",
    "Kontrol sende. İzinler ayarlardan yönetilir.": "You are in control. Manage permissions in settings.",
    "Ses yerel olarak işleniyor.": "Audio is processed locally.",
    "Alt + Space": "Alt + Space",
    "Konuşmayı yazıya çevirmek için Hey Nexus sekmesindeki Modeli hazırla düğmesini kullanabilirsiniz. Dinleme izni vermeniz gerekmez.": "To prepare speech transcription, use Prepare model in the Hey Nexus tab. Listening permission is not required.",
    "Örnek belgeyle dene": "Try a sample document",
    "Bağlantı kurulumu": "Connection setup",
    "Örnek belge yüklenemedi. Nexus'u yeniden açıp dene.": "Could not load the sample document. Restart Nexus and try again.",
    "Örnek proje belgesini özetle ve sıradaki üç adımı çıkar.": "Summarize the sample project brief and identify the next three steps.",
    "Hareketi azalt": "Reduce motion",
    "Logo ve pencere animasyonlarını kapatır; durum bilgileri görünür kalır.":
        "Disable logo and window animations; status information stays visible.",
    "Nexus hazır": "Nexus ready",
    "Nexus dinliyor": "Nexus listening",
    "Nexus düşünüyor": "Nexus thinking",
    "DÜŞÜNMEK İÇİN BİR ALAN": "A LITTLE SPACE TO THINK",
    "Kopyaladığın içerikle çalış": "Work with what you copied",
    "Kaynaklarla daha derine in": "Explore with sources",
    "Aklındakini anlat": "Say what's on your mind",
    "Tercihlerin. Senin kontrolünde.": "Your preferences. Your control.",
    "Çalışma alanın": "Your workspace",
    "Erişim izinleri": "Access permissions",
    "Kişisel hafızan": "Your personal memory",
    "Giriş": "Input",
    "Yanıt sesi": "Response voice",
    "Mikrofon": "Microphone",
    "Hoparlör": "Speaker",
    "Sistem varsayılanı": "System default",
    "F2 ile başlat / durdur": "Press F2 to start / stop",
    "F2 basılıyken konuş": "Hold F2 to talk",
    "F2 ile başlat, sessizlikte bitir": "Start with F2, stop on silence",
    "Sesli giriş": "Voice input",
    " sn": " s",
    "Bitirme sessizliği": "End-of-speech pause",
    "Ses eşiği": "Voice threshold",
    "Sessiz konuşmayı kaçırıyorsa azaltın; ortam gürültüsünü konuşma sayıyorsa artırın.":
        "Lower if quiet speech is missed; raise if background noise is treated as speech.",
    "Otomatik · yerel": "Automatic · local",
    "Supertonic · yerel": "Supertonic · local",
    "Windows sesi · yerel": "Windows voice · local",
    "Edge · bulut izni gerektirir": "Edge · cloud permission required",
    "Yerel ses {number}": "Local voice {number}",
    "Supertonic karakteri": "Supertonic voice",
    "Bulut karakteri": "Cloud voice",
    "Konuşma hızı": "Speaking speed",
    "Hızlı · 4 adım": "Fast · 4 steps",
    "Dengeli · 6 adım": "Balanced · 6 steps",
    "Ayrıntılı · 8 adım": "Detailed · 8 steps",
    "Yerel üretim": "Local synthesis",
    "Daha az adım üretimi hızlandırır; ses kalitesi değişebilir.":
        "Fewer steps speed up synthesis; voice quality may change.",
    "Supertonic ve Edge için geçerli; Windows sesi kendi hız ayarını kullanır.":
        "Applies to Supertonic and Edge; Windows voice uses its own speed setting.",
    "Normal sesli giriş en fazla 60 saniyedir. Hey Nexus ayrı izin gerektirir.":
        "Voice input is limited to 60 seconds. Hey Nexus requires separate permission.",
    "Ses cihazlarını yenile": "Refresh audio devices",
    "Mikrofonlar listelenemedi. Bağlantıyı kontrol edip yenileyin.":
        "Could not list microphones. Check the connection and refresh.",
    "Önceki seçim (bağlı değil)": "Previous selection (disconnected)",
    "Yerel model bulunamadı veya yüklenemedi. Modeli hazırla seçeneğini kullanabilirsiniz.":
        "The local model was not found or could not load. You can use Set up model.",
    "Yerel model henüz kontrol edilmedi. Bu kontrol mikrofonu açmaz.":
        "The local model has not been checked. This check does not open the microphone.",
    "Modeli kontrol et": "Check model",
    "Modeli hazırla…": "Set up model…",
    "İşlemi durdur": "Stop task",
    "Yerel ses modelini hazırla": "Set up local speech model",
    "Whisper base dosyaları Hugging Face (Systran/faster-whisper-base) üzerinden indirilebilir. İnternet ve disk alanı kullanılır. Mikrofon açılmaz; ses veya sohbet gönderilmez. Bu işlem dinleme izni vermez. İptalde önbellekte kısmi dosyalar kalabilir. Devam edilsin mi?":
        "Whisper base files may be downloaded from Hugging Face (Systran/faster-whisper-base). This uses internet access and disk space. No microphone is opened; no audio or conversations are sent. This does not grant listening permission. Cancelling may leave partial files in the cache. Continue?",
    "Model hazırlanıyor… Mikrofon kapalı.": "Preparing model… Microphone off.",
    "Yerel önbellek kontrol ediliyor… Mikrofon kapalı.": "Checking local cache… Microphone off.",
    "Model dosyaları indiriliyor… Mikrofon kapalı.": "Downloading model files… Microphone off.",
    "Model çevrimdışı yüklenerek doğrulanıyor… Mikrofon kapalı.":
        "Validating model by loading it offline… Microphone off.",
    "Model doğrulandı; dinleme izni ayrı verilir. Mikrofon erişimi test edilmedi.":
        "Model verified; listening permission is separate. Microphone access was not tested.",
    "Model hazırlanamadı. İnternet, disk alanı ve model önbelleğini kontrol edip yeniden deneyin.":
        "Model setup failed. Check internet access, disk space and the model cache, then retry.",
    "Model hazırlığı zaman aşımına uğradı. Yeniden deneyebilirsiniz.":
        "Model setup timed out. You can retry.",
    "İşlem durduruldu. Dinleme izinleri değişmedi; kısmi indirme önbellekte kalabilir.":
        "Task stopped. Listening permissions are unchanged; partial downloads may remain cached.",
    "Model kontrolü başlatılamadı. Nexus kurulumunu kontrol edin.":
        "Model check could not start. Check your Nexus installation.",
    "Mikrofon listesi okunamadı. Cihazları yenileyin.": "Could not read the microphone list. Refresh devices.",
    "Seçili mikrofon bağlı değil. Başka bir mikrofon seçin.": "Selected microphone is disconnected. Select another microphone.",
    "Mikrofon bulunamadı. Cihaz bağlayıp listeyi yenileyin.": "No microphone found. Connect a device and refresh the list.",
    "Mikrofon listede görünüyor; Windows erişim izni ve ses alımı henüz test edilmedi.":
        "A microphone is listed; Windows permission and audio capture have not been tested.",
    "Mikrofon hazırlanıyor… Konuşmak için hazır işaretini bekle.":
        "Preparing the microphone… Wait for the ready indicator before speaking.",
    "Dinleniyor…": "Listening…",
    "DİNLİYORUM": "LISTENING",
    "Konuşmaya başlayabilirsin.": "You can start speaking now.",
    "F2'yi bırakınca kayıt biter.": "Release F2 to finish recording.",
    "Konuşma bitince kayıt otomatik durur. F2 ile de bitirebilirsin.":
        "Recording stops after you finish speaking. You can also press F2 to finish.",
    "Bitirmek için F2'ye yeniden bas.": "Press F2 again to finish.",
    "Ses yerel Whisper ile çözümleniyor…": "Transcribing with local Whisper…",
    "Kapalı": "Off",
    "Durduruluyor": "Stopping",
    "Duraklatıldı": "Paused",
    "15 dakika ertelendi": "Snoozed for 15 minutes",
    "Asistan meşgul": "Assistant busy",
    "Bekleme süresi": "Cooldown",
    "Görünür gösterge bekleniyor": "Waiting for a visible indicator",
    "Hazırlanıyor · mikrofon kapalı": "Preparing · microphone off",
    "Dinliyor · yerel mikrofon açık": "Listening · local microphone on",
    "Dinliyor · algılama gecikti, eski çağrı atlandı": "Listening · detection delayed, old call skipped",
    "● Hey Nexus · Dinliyor": "● Hey Nexus · Listening",
    "○ Hey Nexus · Beklemede": "○ Hey Nexus · Standby",
    "○ Hey Nexus · Kapalı": "○ Hey Nexus · Off",
    "○ Hey Nexus · Kontrol gerekli": "○ Hey Nexus · Check needed",
    "Hey Nexus · {state}\nTıkla: duraklat / devam et": "Hey Nexus · {state}\nClick to pause / resume",
    "Hey Nexus: duraklat": "Hey Nexus: pause",
    "Hey Nexus: devam et": "Hey Nexus: resume",
    "15 dakika ertele": "Snooze for 15 minutes",
    "Nexus'u göster": "Show Nexus",
    "Ayarlar": "Settings",
    "Çıkış": "Quit",
    "Hey Nexus modeli hazır değil. Ayarlar → Ses bölümünden Modeli hazırla seçeneğini kullanıp yeniden deneyin.":
        "The Hey Nexus model is not ready. Use Set up model under Settings → Voice, then retry.",
    "Hey Nexus mikrofonu kullanamıyor. Ses ayarlarındaki cihazı ve Windows mikrofon iznini kontrol edin.":
        "Hey Nexus cannot use the microphone. Check the device in Voice settings and Windows microphone permission.",
    "Hey Nexus ses algılaması durdu. Yerel modeli F2 ile kontrol edip yeniden deneyin.":
        "Hey Nexus recognition stopped. Check the local model with F2, then retry.",
    "Hey Nexus dinlemesine izin ver (deneysel)": "Allow Hey Nexus listening (experimental)",
    "Nexus açılınca Hey Nexus dinlemesini başlat": "Start Hey Nexus listening when Nexus opens",
    "İzin verirseniz arka planda kısa ses parçaları yalnızca yerel Whisper ile incelenir; kaydedilmez veya buluta gönderilmez. 'Hey Nexus' deyip duraklayın; pencere açılınca komutunuzu söyleyin. İşlemci kullanımı ve algılama gecikmesi olabilir. Penceredeki Hey Nexus düğmesinden veya sistem tepsisinden duraklatabilirsiniz. Yerel modeli aşağıdan mikrofon açmadan kontrol edebilir veya hazırlayabilirsiniz.":
        "With your permission, short background audio clips are processed only by local Whisper; they are not saved or sent to the cloud. Say 'Hey Nexus', then pause; speak your command after the window opens. CPU use and detection delay are possible. Pause from the Hey Nexus button or system tray. Check or set up the local model below without opening the microphone.",
    "{name} hakkında ne öğrenmek istersin?": "What would you like to know about {name}?",
    "Görsel eklendi  ·  {name}": "Image attached  ·  {name}",
    "WEB ERİŞİMİ": "WEB ACCESS",
    "Kişisel alanın.": "Your personal space.",
    "Yeni sohbet · Ctrl+N": "New conversation · Ctrl+N",
    "Geçmiş · Ctrl+H": "History · Ctrl+H",
    "Ayarlar · Ctrl+,": "Settings · Ctrl+,",
    "Pencereyi gizle · Esc": "Hide window · Esc",
    "Aklında ne var?": "What's on your mind?",
    "Bir fikir, bir soru, yarım kalan bir iş.\nBirlikte devam edelim.":
        "An idea, a question, something unfinished.\nLet's work on it together.",
    "Panoyu incele": "Explore clipboard",
    "Bir konuyu araştır": "Research a topic",
    "Sesli konuş": "Talk to Nexus",
    "Yanıtı kopyala": "Copy response",
    "Yanıt kopyalandı": "Response copied",
    "Nexus'a bir şey sor…": "Ask Nexus anything…",
    "Nexus komut alanı": "Nexus message field",
    "Mesajınızı yazıp Enter'a veya gönder düğmesine basın.":
        "Type a message and press Enter or the send button.",
    "Belge ekle": "Add document",
    "Ekle": "Attach",
    "Web araştırması": "Web research",
    "Araştır": "Research",
    "Sohbet araçları": "Conversation tools",
    "Araçlar": "Tools",
    "Özel oturum": "Private session",
    "Belgelerimden yanıtla": "Answer from my documents",
    "Yanıtları seslendir": "Read responses aloud",
    "Hafızamı göster": "Show my memory",
    "Hafızayı yönet · adayları incele": "Manage memory · review candidates",
    "Durdur": "Stop",
    "Sesli konuş · F2": "Talk to Nexus · F2",
    "Mesajı gönder · Enter": "Send message · Enter",
    "YEREL MODEL": "LOCAL MODEL",
    "ÖZEL OTURUM": "PRIVATE SESSION",
    "AĞ SAĞLAYICISI": "NETWORK PROVIDER",
    "YEREL MODEL · BULUT SESİ": "LOCAL MODEL · CLOUD SPEECH",
    "Ayarlar'dan bir model seç": "Choose a model in Settings",
    "model seçilmedi": "no model selected",
    "Hey Nexus dinlemesini duraklat veya devam ettir": "Pause or resume Hey Nexus listening",
    "Enter  gönder": "Enter  send",
    "Panodan ekle  ·  Önce iznin istenir": "Add from clipboard  ·  Permission required",
    "Panoda bir görsel var  ·  İncelemek için tıkla": "Image on clipboard  ·  Click to inspect",
    "Panodan ekle  ·  {snippet}": "Add from clipboard  ·  {snippet}",
    "Özel oturum açık · hiçbir konuşma kaydedilmez": "Private session on · no conversation history saved",
    "Özel oturum · geçmişe kaydetme": "Private session · do not save history",
    "Yerel bilgi tabanı açık": "Local document context on",
    "Yerel bilgi tabanını kullan": "Use local document context",
    "Nexus · Ayarlar": "Nexus · Settings",
    "Nexus'u kendine göre ayarla": "Make Nexus your own",
    "Genel": "General", "Gizlilik": "Privacy", "Ses": "Voice",
    "Dil": "Language", "Sağlayıcı": "Provider", "Model": "Model",
    "Embedding modeli": "Embedding model",
    "Nexus çalışan LM Studio, Ollama ve llama.cpp sunucularını bulur. Dil modeli isteği seçtiğin yerel sağlayıcıda kalır.":
        "Nexus discovers running LM Studio, Ollama and llama.cpp servers. Language-model requests stay with your selected local provider.",
    "Örnek: nomic-embed-text. Boş bırakılırsa yalnızca anahtar kelime araması kullanılır.":
        "Example: nomic-embed-text. Leave empty to use keyword search only.",
    "Web araştırmasına gerektiğinde izin ver": "Allow web research when needed",
    "Bulut sesini gerektiğinde onayla ve kullan": "Allow cloud speech when needed",
    "Açıkça kaydettiğim kişisel hafızayı kullan": "Use my explicitly saved personal memory",
    "Konuşmalardan yerel modelle hafıza adayları çıkar": "Extract memory candidates locally from conversations",
    "Konuşma ve proje özetlerini gelecekteki yanıtlarda kullan": "Use conversation and project summaries in future answers",
    "Kişisel hafızayı yönet…": "Manage personal memory…",
    "Her kullanımda sor": "Ask each time",
    "Her zaman izin ver": "Always allow",
    "Pano erişimini engelle": "Block clipboard access",
    "Pano erişimi": "Clipboard access",
    "Çalışan yerel sağlayıcıları bulmak için tara.": "Scan to find running local providers.",
    "Yerel sağlayıcıları tara": "Scan local providers",
    "Kaydet": "Save", "Vazgeç": "Cancel",
    "Yerel sağlayıcılar aranıyor…": "Looking for local providers…",
    "Çalışan sağlayıcı bulunamadı. LM Studio, Ollama veya llama.cpp'yi başlatıp yeniden tara.":
        "No running provider found. Start LM Studio, Ollama or llama.cpp and scan again.",
    "{count} çalışan yerel sağlayıcı bulundu.": "Found {count} running local providers.",
    "Dil değişikliği Kaydet ile uygulanır. Ses, geçmiş ve hafıza pencerelerinin bazı metinleri henüz çevrilmedi.":
        "Language changes apply on Save. Some voice, history and memory dialog text is not yet translated.",
    "Yerel model düşünüyor…": "The local model is thinking…",
    "Yanıtını hazırlıyorum…": "Preparing your response…",
    "  ·  Görsel dahil": "  ·  Image included",
    "Nexus servisi hata döndürdü ({status}).": "The Nexus service returned an error ({status}).",
    "Model yanıtı zaman aşımına uğradı. Yeniden deneyin.": "The model response timed out. Please try again.",
    "Nexus servisine ulaşılamadı. Uygulamayı yeniden başlatmayı deneyin.":
        "Could not reach the Nexus service. Try restarting the application.",
    "Bilinmeyen hata": "Unknown error",
    "Nexus bağlantısı yanıt tamamlanmadan kesildi. Yeniden deneyin.":
        "The Nexus connection closed before the response completed. Please try again.",
    "İşlemler durduruluyor…": "Stopping active tasks…",
    "Yanıt uzunluk sınırına ulaştı": "Response length limit reached",
}


class UiText:
    """Window-owned language bindings; updating labels never rebuilds live widgets."""

    def __init__(self, language="tr"):
        self.language = language if language in {"tr", "en"} else "tr"
        self._bindings = []

    def __call__(self, source, **values):
        template = ENGLISH.get(source, source) if self.language == "en" else source
        return template.format(**values) if values else template

    def bind(self, target, method, source):
        # A catalog must not extend a widget's lifetime beyond its Qt owner.
        self._bindings.append((ref(target), method, source))
        getattr(target, method)(self(source))

    def set_language(self, language):
        self.language = language if language in {"tr", "en"} else "tr"
        live = []
        for target_ref, method, source in self._bindings:
            target = target_ref()
            if target is not None and not sip.isdeleted(target):
                getattr(target, method)(self(source))
                live.append((target_ref, method, source))
        self._bindings = live
