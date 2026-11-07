# 👑 Zakirun Kur'an Bilgi Yarışması (Dedicated Edition)

Bu klasör, **Zakirun Kur'an Bilgi Yarışması**'nın tüm gereksiz dosyalardan arındırılmış, hafif ve müstakil olarak çalışan tam paketidir.

---

## 📁 Klasör İçeriği (Yalnızca Gerekli Dosyalar)
- `index.html`: Modern, duyarlı ve hatasız yarışma arayüzü (11 Basamaklı Soru Merdiveni, 3 Joker, Meâl & Tilâvet Paneli).
- `server.py`: Dedicated FastAPI/Uvicorn backend sunucusu (%100 benzersiz şık garantisi ve vakıf temizleme motoru).
- `bilgi_yarismasi.db`: Yalnızca yarışma için gereken 114 Sûre, 6.236 Âyet ve Diyanet Meâllerini içeren 2.98 MB ultra-hızlı SQLite veritabanı.
- `zakirun.com.woff2`: Orijinal Medine Mushafı Uthmânî 2 yazı tipi.
- `LOGO.png`: Zakirun Kur'an TV resmi amblemi.
- `baslat.bat`: Tek tıkla sunucuyu başlatan ve tarayıcıyı açan başlatıcı betik.

---

## 🚀 Çalıştırma
1. **`baslat.bat`** dosyasına çift tıklayarak yarışmayı anında başlatabilirsiniz.
2. Veya komut satırından:
   ```cmd
   python server.py 8000
   ```
3. Tarayıcınızda açın: **`http://127.0.0.1:8000/`**

---

## ✨ Özellikler & Çözülen Hatalar
- **Sıfır Mükerrer Şık:** Seçeneklerde asla aynı kelime iki defa çıkmaz (`set()` ve `dict.fromkeys` garantisi).
- **Kesin Doğru Cevap:** Doğru cevap her zaman 4 şıktan biridir ve doğru indekse işaret eder.
- **Temiz Metinler:** Kelime sonuna yapışan secavend/vakıf işaretleri (`ۙ`, `ۚ`, `ۖ`, `ۜ`, `ۗ`, `ۘ`, `ؕ`) otomatik temizlenir.
- **4 Sûre Havuzu:** 30. Cüz (Amme), İlk 10 Sûre, Yâsîn-Mülk-Vâkıa ve Tüm Kur'an.
- **4 Muallim Kāri:** Mahmûd Halîl el-Husarî, Muhammed Sıddîk el-Minşâvî, Abdülbâsit Abdüssamed, Mişâri el-Afâsî.
- **Hata Takibi:** Takılınan sorular yerel ve veritabanı belleğinde saklanır, "Hatalı Cevaplarım" modalından incelenebilir.
