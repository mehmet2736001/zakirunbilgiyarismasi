# 📖 ZÂKİRÛN KUR'AN PLATFORMU // KULLANIM KILAVUZU (2026)

Bu kılavuz, **Zâkirûn Kur'an Öğrenme ve Yarışma Platformu**'nun kurulumunu, modüler klasör mimarisini, Turso LibSQL bulut veritabanı entegrasyonunu, Google/Supabase kimlik doğrulama sistemini ve tüm bileşenlerin kullanımını detaylandırmaktadır.

---

## 1. 🚀 Hızlı Başlangıç (Tek Tıkla Çalıştırma)

Platformu çalıştırmak için herhangi bir komut ezberlemenize gerek yoktur:

1. **`E:\ZAKİRUN.COM\bilgiyarismasi\baslat.bat`** dosyasına **çift tıklayın**.
2. Betik otomatik olarak:
   - Port 8000 üzerinde çalışan eski bir süreç varsa temizler (port çakışmasını engeller).
   - Python 3.11 çalışma ortamını tespit eder.
   - Quantum FastAPI backend sunucusunu başlatır (`server.py 8000`).
   - Varsayılan tarayıcınızda doğrudan anasayfayı açar: **`http://127.0.0.1:8000/`**
3. Siyah sunucu penceresini oyun süresince açık tutun. Kapatmak istediğinizde pencereyi çarpıdan kapatabilir veya `CTRL + C` yapabilirsiniz.

---

## 2. 📁 Kusursuz & Modüler Klasör Yapısı

Platform gereksiz tüm dağınıklıktan arındırılarak kurumsal bir dosya hiyerarşisine kavuşturulmuştur:

```text
E:\ZAKİRUN.COM\bilgiyarismasi\
│
├── baslat.bat                          ★ Tek tıkla başlatıcı betik
├── server.py                           ★ Quantum FastAPI / Uvicorn Sunucusu
├── config.json                         ★ Turso ve Supabase bulut kimlik bilgileri
├── turso_sync.py                       ★ Turso Bulut senkronizasyon ve sorgu modülü
├── README.md                           ★ Proje tanıtımı
├── KULLANIM_KILAVUZU.md                ★ Bu kullanım kılavuzu
├── OYUNLAR_VE_MODULLER_KATALOGU.md     ★ 11 Modülün detaylı kataloğu
│
├── pages/                              📂 Web Arayüzleri (Tüm Oyun ve Ekranlar)
│   ├── index.html                      - Ana Lobi, 20 Bot Arenası ve Masalar
│   ├── giris.html                      - Google ile Giriş & Hesap / Ayarlar Merkezi
│   ├── kuran_ogrenme_portali.html      - 87 Derslik Elifbâ & Tecvid Portalı
│   ├── oyun_bilgi_yarismasi.html       - 11 Basamaklı Soru Merdiveni
│   ├── oyun_okunan_kelime.html         - Okunan Kelimeyi Bul & Dinleme Oyunu
│   ├── oyun_sure_ezberleme.html        - Sûre Ezberleme (Kolay & Zor Mod)
│   ├── oyun_ayet_tamamlama.html        - Âyet Tamamlama & Daktilo Efekti
│   ├── oyun_ayet_bloklari.html         - Âyet İçi Kelime Kuleleri
│   ├── oyun_kelime.html                - Kur'an Bulmaca / Kelime Oyunu
│   ├── oyun_turnuva.html               - Haftalık Şampiyonalar & 16'lı Ağaç
│   ├── hifz_karne.html                 - Detaylı Hıfz Karnesi & Zayıf Âyet Analizi
│   └── archive/                        - Arşivlenen eski monolitik dosyalar
│
├── assets/                             📂 Görseller, Yazı Tipleri ve PWA Dosyaları
│   ├── LOGO.png                        - Zakirun Kur'an TV amblemi
│   ├── zakirun.com.woff2               - Orijinal Medine Mushafı Uthmânî 2 hattı
│   ├── manifest.json                   - PWA (Progressive Web App) tanımı
│   └── sw.js                           - Çevrimdışı Service Worker
│
├── audio/                              📂 Yerel Ses Arşivleri (2.000+ Otantik Dosya)
│   ├── diyanet/                        - 1.837 Diyanet Elifbâ & Tecvid telaffuz sesi
│   ├── learn/                          - 113 Özel harf & kural eğitim sesi
│   └── elifletter/                     - 58 Harf mahreç ve telaffuz MP3 kaydı
│
├── database/                           📂 Veritabanı Çekirdeği
│   ├── kuran_master_fihrist_v2.db      - 3.14 GB Master SQLite veritabanı (WAL mod)
│   ├── bilgi_yarismasi.db              - 3.12 MB Hızlı Kompakt SQLite veritabanı
│   └── turso_sync.py                   - Turso Bulut köprüsü kopyası
│
├── data/                               📂 Müfredat & Veri Modülleri
│   ├── diyanet_curriculum_v2.json      - Diyanet Kur'an Portalı resmi müfredatı
│   ├── listen_find_game_data.py        - Okunan Kelime veri motoru
│   ├── quran_learn_data.py             - Kur'an Öğrenme veri motoru
│   └── supabase_client.js              - Supabase Auth istemcisi
│
└── tests/                              📂 Otomasyon & Kalite Kontrol
    └── test_gameshow_suite.py          - 78 Testlik Kapsamlı Otomasyon Süiti
```

---

## 3. ☁️ Turso LibSQL Bulut Veritabanı Mimarisi

Platform **Çift Modlu (Hybrid)** veritabanı mimarisine sahiptir:

1. **Turso Bulut Bilgileri (`config.json`):**
   * **URL:** `libsql://zakirunbilgiyarismasi-zakirun002.aws-eu-west-1.turso.io`
   * **HTTP Pipeline API:** `https://zakirunbilgiyarismasi-zakirun002.aws-eu-west-1.turso.io/v2/pipeline`
   * **Bölge:** AWS EU West (Frankfurt / İrlanda)
   * **Canlı Durum Kontrolü:** `http://127.0.0.1:8000/api/turso/status` adresinden anlık olarak izlenebilir.
2. **Taşınan Tablolar:**
   * `surahs` (114 Sûre künyesi)
   * `ayahs` (6.236 Âyet ve Medine Uthmânî 2 hattı)
   * `translations` (Diyanet Türkçe meâlleri)
   * `hafizlik_leaderboard` (Liderlik sıralaması)
   * `hafizlik_elo` (ELO puanları ve seviyeler)
   * `hafizlik_tournaments` (Turnuva ağaçları)
   * `hafizlik_matches` (Maç geçmişi)
   * `hafizlik_mistakes_log` (Hatalı cevap takibi)
   * `hafizlik_users` (Kullanıcı hesapları)
   * `surah_descriptions`, `locations_juz`, `quran_places`, `asbab_al_nuzul`
3. **Manuel Senkronizasyon:**
   * Konsoldan `python turso_sync.py` çalıştırılarak bulut bağlantısı her zaman test edilebilir.

---

## 4. 🔑 Giriş ve Kimlik Doğrulama (Google & Supabase)

Kullanıcılar sağ üst köşedeki **"Giriş Yap"** butonu üzerinden iki farklı şekilde oturum açabilir:

1. **Google ile Hızlı Giriş:**
   * Tek tıkla Google OAuth penceresi açılır.
   * Giriş tamamlandığında kullanıcı profili, avatarı ve ELO puanı bulutla senkronize edilir.
2. **E-Posta & Şifre ile Kayıt/Giriş:**
   * Supabase Auth API üzerinden güvenli JWT oturumu oluşturulur.
   * Başarılı girişte sistem otomatik olarak anasayfaya yönlendirir.
3. **Hesap & Ayarlar Merkezi:**
   * Oturum açıldıktan sonra sağ üstteki profil kartına tıklanarak açılır:
   * **4 Ana Sekme:** Profilim, Uygulama Ayarları (Kāri seçimi, ses seviyesi, otomatik tilâvet), Güvenlik & Tercihlerim ve Oturumu Kapat.

---

## 5. 🛠️ Sorun Giderme (FAQ)

* **Soru: `baslat.bat` açılıp hemen kapanıyor?**
  * *Cevap:* Güncel `baslat.bat` içinde port çakışmasını engelleyen `taskkill` koruması bulunmaktadır. Python 3.11'in kurulu olduğundan emin olun.
* **Soru: Sesler çalmıyor?**
  * *Cevap:* Tarayıcılarda ses çalma izni "kullanıcı etkileşimi" gerektirir. Sayfaya bir kez tıkladığınızda veya "Dinle" butonuna bastığınızda sesler kesintisiz çalacaktır.
* **Soru: Hatalı cevaplarım nerede saklanıyor?**
  * *Cevap:* Tüm oyunlarda yapılan yanlışlar `hafizlik_mistakes_log` tablosunda ve tarayıcı yerel belleğinde saklanır. Sağ üstteki "Hatalı Cevaplarım" butonundan veya `/karne` sayfasından incelenebilir.
