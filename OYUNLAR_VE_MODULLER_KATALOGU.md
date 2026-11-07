# 🏆 ZÂKİRÛN KUR'AN PLATFORMU // OYUNLAR VE MODÜLLER KATALOĞU (2026)

Bu katalog, **Zâkirûn Platformu** bünyesinde yer alan 11 ana oyun, eğitim ve şampiyona modülünün kurallarını, mekaniklerini, puanlama sistemini ve erişim adreslerini kapsamaktadır.

---

## 📌 Hızlı URL ve Modül Haritası

| No | Modül Adı | Doğrudan URL | Temel Mekanik |
| :---: | :--- | :--- | :--- |
| **1** | **11 Basamaklı Bilgi Yarışması** | [`/oyun/bilgi-yarismasi`](http://127.0.0.1:8000/oyun/bilgi-yarismasi) | Kim Milyoner Olmak İster TV formatı, 3 joker, 2 baraj |
| **2** | **Okunan Kelimeyi Bul** | [`/oyun/okunan-kelimeyi-bul`](http://127.0.0.1:8000/oyun/okunan-kelimeyi-bul) | Otantik ses dinleme, 4 çerçeve, kelime tespiti |
| **3** | **Sûre Ezberleme Oyunu** | [`/oyun/sure-ezberleme`](http://127.0.0.1:8000/oyun/sure-ezberleme) | Kolay/Zor mod, âyet zinciri, kesintisiz tilâvet |
| **4** | **Âyet Tamamlama Oyunu** | [`/oyun/ayet-tamamlama`](http://127.0.0.1:8000/oyun/ayet-tamamlama) | 3sn geri sayım, daktilo tamamlama, yatay ekolayzır |
| **5** | **Âyet Blokları Oyunu** | [`/oyun/ayet-bloklari`](http://127.0.0.1:8000/oyun/ayet-bloklari) | Blok eşleştirme, kelime kuleleri, 5 seviye |
| **6** | **Kur'an Bulmaca / Kelime Oyunu** | [`/oyun/kelime-oyunu`](http://127.0.0.1:8000/oyun/kelime-oyunu) | Ali İhsan Varol stüdyo formatı, harf alma |
| **7** | **Kur'an Öğrenme Portalı** | [`/ogren`](http://127.0.0.1:8000/ogren) | 87 Diyanet dersi, kilitli ders zinciri, sesli sınav |
| **8** | **20 Hâfız Bot Arenası & Lobi** | [`/`](http://127.0.0.1:8000/) | Yatay masalar, 20 bot, canlı maç simülasyonu |
| **9** | **Turnuvalar & Şampiyonalar** | [`/turnuvalar`](http://127.0.0.1:8000/turnuvalar) | 16'lı eleme ağacı, kupa ligi, ELO ödülleri |
| **10**| **Hıfz Karnesi & Zayıf Âyetler** | [`/karne`](http://127.0.0.1:8000/karne) | Cüz yetkinlik grafiği, aralıklı tekrar kuyruğu |
| **11**| **Giriş & Hesap Merkezi** | [`/giris`](http://127.0.0.1:8000/giris) | Google OAuth, Supabase JWT, ses/kāri ayarları |

---

## 🎯 Modül Detayları ve Oyun Kuralları

### 1. 👑 11 Basamaklı Kur'an Bilgi Yarışması
* **Amaç:** 11 basamağı tırmanarak 100 zirve motivasyon puanına ulaşmak.
* **Baraj Noktaları:** 
  * 4. Soru (25 Puan) -> 1. Garanti Barajı
  * 7. Soru (65 Puan) -> 2. Garanti Barajı
* **3 Hayat Kurtaran Joker:**
  * `%50 Yarı Yarıya`: 2 yanlış şıkkı siler.
  * `Seyirci Oylaması`: Yüzdelik dağılım grafiği sunar.
  * `Soruyu Pas Geç`: Mevcut soruyu puan kaybetmeden değiştirir.
* **Özel Garantiler:** Sıfır mükerrer şık algoritması (`set()` ve `dict.fromkeys`) ve vakıf/secavend işaret temizliği ile doğru cevap daima 4 şıktan birinde bulunur.
* **Sûre Havuzu:** 30. Cüz Amme, İlk 10 Sûre, Yâsîn-Mülk-Vâkıa ve 114 Sûre seçeneği.

---

### 2. 🎧 Okunan Kelimeyi Bul Oyunu
* **Format:** Word-by-Word (kelime kelime) ses dinleme ve 4 çerçeve içinden doğru kelimeyi seçme.
* **Özel Filtre:** Başında harekesiz harf olan kelimeler kesinlikle soru havuzuna alınmaz; mutlaka 1. karakter üzerinde fetha (üstün), esre veya damme (ötre) bulunur.
* **Düello Desteği:** 20 Hâfız bottan biriyle 1v1 canlı eşleşme, eş zamanlı harf seçimi.

---

### 3. 📖 Sûre Ezberleme Oyunu
* **Format:** Dinlenen âyetten sonra gelen âyeti doğru tespit etme.
* **İki Farklı Mod:**
  * `Kolay Mod`: Çeldirici seçenekler başka sûrelerden seçilir.
  * `Zor Mod (Hâfızlık Sınavı)`: Çeldirici seçenekler aynı sûrenin diğer âyetlerinden seçilir.
* **114 Sûre Kilidi:** Bir sûrenin 1v1 düellosu açılabilmesi için önce tek kişilik modda %100 başarıyla tamamlanması şarttır.
* **Tilâvet:** Mahmûd Halîl el-Husarî (Muallim) kesintisiz akışı.

---

### 4. ✍️ Âyet Tamamlama Oyunu
* **Format:** Âyet içindeki kaybolan kelimeyi bulup daktilo tamamlama.
* **Geri Sayım:** 3 saniyelik heyecanlı geri sayım biter bitmez kelime kaybolur ve boş hücre açılır.
* **Yatay Ses Paneli:** Ses çalarken çıkan efekt paneli dikey bozulmadan arındırılmış; stüdyo tipi yatay `🔊 TİLÂVET` ses dalgası kapsülü olarak çalışır.

---

### 5. 🧱 Âyet Blokları Oyunu
* **Format:** Âyet içindeki kelimeleri sıralayarak blok kuleleri inşa etme.
* **5 Kademe:** Kolaydan zora doğru Uthmânî 2 hattıyla kelime blokları dizilir.

---

### 6. 💡 Kur'an Bulmaca / Kelime Oyunu
* **Format:** Ali İhsan Varol stüdyo yarışması formatı.
* **Mekanik:** 5 tur x 20 puan = 100 puan. Her harf alışta tur puanından 1 eksilir; kelimeyi en az harfle tahmin eden en yüksek puanı alır.

---

### 7. 🏫 1. Baş Oda: Kur'an Öğrenme Portalı
* **Müfredat:** Diyanet İşleri Başkanlığı Kur'an Portalı ile %100 senkronize 87 ders.
* **Kilit Kuralı:** Bir dersin tüm hücreleri dinlenmeden sonraki derse asla geçilemez. 1. bölüm açıktır, diğer bölümler dersler tamamlandıkça açılır.
* **Otomatik Soru:** Kullanıcı son dersin son hücresini (örneğin Ye harfini) okuduğunda alttaki soru kutucuğuna otomatik odaklanır ve soru sesi çalar.

---

### 8. 🤖 20 Hâfız Bot Arenası
* Arka planda özerk olarak yarışan, puan kazanan ve liderlik tablosunu güncelleyen 20 bot hâfız (Zeynep K., Hüseyin R., Ahmet Hâfız, Meryem S., Salih E., vb.).
* ELO eşleşme motoruyla kullanıcının seviyesine en yakın rakip bot seçilir.

---

### 9. 🏆 Turnuvalar & Şampiyonalar
* Son 16, Çeyrek Final, Yarı Final ve Büyük Final podyumlarından oluşan 4 turlu kupa mücadeleleri.

---

### 10. 📊 Hıfz Karnesi & Zayıf Âyetler
* 30 Cüz yetkinlik analizi, zayıf kalınan âyetlerin aralıklı tekrar algoritmasıyla (`Spaced Repetition`) tekrar kuyruğuna alınması.

---

### 11. 🔴 Merkezi Hata Takip Sistemi
* 6 oyunda yapılan tüm yanlışlar tek bir veritabanında (`hafizlik_mistakes_log`) toplanır. Kullanıcı "Hatalı Cevaplarım" butonundan yanlışlarını tek tek inceleyip tekrar çalışabilir.
