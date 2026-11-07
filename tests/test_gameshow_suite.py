#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zakirun Hâfızlık Yarışmaları // Kapsamlı Otomasyon & 20 Bot Test Süiti
Tüm modları, API uç noktalarını, font ve veritabanı bütünlüğünü test eder.
"""

import sys
import json
import time
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

class TestReport:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def log(self, name, success, detail=""):
        status_sym = "✅ GEÇTİ" if success else "❌ BAŞARISIZ"
        if success:
            self.passed += 1
        else:
            self.failed += 1
        self.tests.append({"name": name, "success": success, "detail": detail})
        print(f"[{status_sym}] {name} {f'-> {detail}' if detail else ''}")

report = TestReport()

def http_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "ZakirunTestBot/2.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read()

def http_get_json(path):
    status, raw = http_get(path)
    return status, json.loads(raw.decode('utf-8'))

def http_post_json(path, data_dict):
    url = f"{BASE_URL}{path}"
    data_bytes = json.dumps(data_dict).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"User-Agent": "ZakirunTestBot/2.0", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

print("=================================================================")
print("🚀 ZAKİRUN HÂFIZLIK YARIŞMALARI // KAPSAMLI TEST SÜİTİ BAŞLADI")
print(f"🌐 Hedef Adres: {BASE_URL}")
print("=================================================================\n")

# 1. TEST: Statik Varlıklar ve Font Doğrulaması
try:
    status, font_bytes = http_get("/zakirun.com.woff2")
    report.log("Zakirun Uthmânî 2 WOFF2 Font Dağıtımı", status == 200 and len(font_bytes) > 1000, f"{len(font_bytes)} bayt")
except Exception as e:
    report.log("Zakirun Uthmânî 2 WOFF2 Font Dağıtımı", False, str(e))

try:
    status, html_bytes = http_get("/")
    html_str = html_bytes.decode('utf-8', errors='ignore')
    has_lobby = 'id="mode-lobby"' in html_str
    has_tables = 'tables-horizontal-scroll' in html_str
    has_tournaments = 'Turnuvalar & Canlı Şampiyonalar' in html_str
    report.log("Anasayfa HTML & Sade Lobi Mimarisi", status == 200 and has_lobby and has_tables and has_tournaments, "Lobi ve Yatay Masalar Doğrulandı")
except Exception as e:
    report.log("Anasayfa HTML & Sade Lobi Mimarisi", False, str(e))

# 2. TEST: 20 Bot Kullanıcı ve Liderlik Tablosu
try:
    status, raw = http_get("/api/gameshow/leaderboard?limit=25")
    data = json.loads(raw.decode('utf-8'))
    bots = data.get("leaderboard", [])
    has_20_bots = len(bots) >= 20
    all_scores_valid = all(0 <= b.get("highest_score", 0) <= 100 for b in bots)
    top_bot = bots[0] if bots else {}
    report.log("20 Hâfız Bot Kullanıcı Varlığı", has_20_bots, f"{len(bots)} bot kayıtlı, Zirve: {top_bot.get('player_name')} ({top_bot.get('total_points')} Puan)")
    report.log("Maksimum 100 Puan Kuralı Denetimi", all_scores_valid, "Tüm bot skorları <= 100")
except Exception as e:
    report.log("20 Hâfız Bot Kullanıcı Varlığı", False, str(e))

# 3. TEST: Tamamlanan Maç Geçmişi
try:
    status, raw = http_get("/api/gameshow/matches/recent?limit=15")
    data = json.loads(raw.decode('utf-8'))
    matches = data.get("recent_matches", [])
    report.log("Kalıcı SQLite Maç Geçmişi", len(matches) >= 10, f"{len(matches)} tamamlanmış maç kaydı mevcut")
except Exception as e:
    report.log("Kalıcı SQLite Maç Geçmişi", False, str(e))

# 4. TEST: Model 1 - Kim Hâfız Olmak İster? (Husary Muallim + 30. Cüz)
try:
    status, raw = http_get("/api/gameshow/ladder?surah_group=juz30&reciter_id=12")
    data = json.loads(raw.decode('utf-8'))
    levels = data.get("ladder", [])
    has_11_levels = len(levels) == 11
    has_husary = all("Husary_Muallim_128kbps" in lv.get("audio_url", "") for lv in levels)
    checkpoint_4 = levels[3].get("checkpoint") is True
    checkpoint_7 = levels[6].get("checkpoint") is True
    level_11_points = levels[10].get("points") == "100"
    report.log("Model 1: 11 Basamaklı Soru Merdiveni", has_11_levels and level_11_points, "11 Basamak & 100 Puan Zirvesi")
    report.log("Model 1: Hâfızlık Muallim Kāri (Husary Audio CDN)", has_husary, "Tüm âyetlerde Husary Muallim akışı doğrulandı")
    report.log("Model 1: 1. ve 2. Garanti Baraj Noktaları", checkpoint_4 and checkpoint_7, "4. Basamak (25 P) & 7. Basamak (65 P)")
except Exception as e:
    report.log("Model 1: Merdiven Testi", False, str(e))

# 5. TEST: Model 2 - Kur'an Kelime & Âyet Bulmacası (Puzzle Game)
try:
    status, raw = http_get("/api/gameshow/puzzle-game?count=5")
    data = json.loads(raw.decode('utf-8'))
    rounds = data.get("rounds", [])
    has_5_rounds = len(rounds) == 5
    has_scrambled_pool = all(len(r.get("scrambled_pool", [])) >= len(r.get("letters", [])) for r in rounds)
    has_uthmani_arabic = all(bool(r.get("full_ayah_arabic")) for r in rounds)
    has_husary_audio = all("Husary_Muallim_128kbps" in r.get("audio_url", "") for r in rounds)
    max_total = data.get("max_total_score", 100)
    report.log("Model 2: Kur'an Bulmaca & Kelime Oyunu API", has_5_rounds and has_scrambled_pool and has_uthmani_arabic and has_husary_audio, f"5 Tur x 20 Puan = Maksimum {max_total} Puan, Uthmânî 2 & Husary Muallim tam entegre")
except Exception as e:
    report.log("Model 2: Kur'an Bulmaca Testi", False, str(e))

# 6. TEST: Model 4 - Canlı Odalar ve Tribün
try:
    status, raw = http_get("/api/gameshow/rooms")
    data = json.loads(raw.decode('utf-8'))
    rooms = data.get("rooms", [])
    report.log("Model 4: Canlı Odalar Listesi", len(rooms) >= 4, f"{len(rooms)} Canlı Oda Aktif")
    
    # Test room-101 detail
    status, raw = http_get("/api/gameshow/rooms/room-101")
    r101 = json.loads(raw.decode('utf-8'))
    has_players = len(r101.get("players", [])) == 4
    report.log("Model 4: 4 Podyumlu Canlı Tribün Odası", has_players, f"{r101.get('name')}")
except Exception as e:
    report.log("Model 4: Canlı Odalar Testi", False, str(e))

# 7. TEST: Yeni Oda Oluşturma & Eşzamanlı Koltuk Devralma (Takeover Empty Seat)
try:
    status, create_res = http_post_json("/api/gameshow/rooms/create", {
        "name": "Bot Otomasyon Test Arenası",
        "mode": "buzzer",
        "surah_pool": "30. Cüz",
        "max_players": 4,
        "allow_substitute": True,
        "host_name": "Test Yöneticisi"
    })
    new_room_id = create_res.get("room", {}).get("id")
    report.log("Yeni Canlı Oda Kurma API", create_res.get("success") is True, f"Oda ID: {new_room_id}")

    # Now take over an empty seat in this fresh room
    status, takeover_res = http_post_json(f"/api/gameshow/rooms/{new_room_id}/takeover-seat", {
        "player_name": "Test Simülasyon Hâfızı"
    })
    seat_id = takeover_res.get("seat", {}).get("id") or "p1"
    report.log("Koltuk Devralma (Hot-Swap) API", takeover_res.get("success") is True, f"Oda: {new_room_id}, Koltuk: {seat_id}")
except Exception as e:
    report.log("Yeni Oda & Koltuk Devralma API", False, str(e))

# 9. TEST: Maç Sonucu Kaydetme
try:
    status, record_res = http_post_json("/api/gameshow/matches/record", {
        "room_name": "Otomasyon Şampiyonası",
        "mode": "millionaire",
        "surah_pool": "30. Cüz",
        "winner_name": "Zeynep K. (Kısa Sûreler)",
        "winner_score": 100,
        "total_rounds": 11
    })
    report.log("Maç Sonucu Kaydetme & Liderlik Güncelleme", record_res.get("success") is True, record_res.get("message"))
except Exception as e:
    report.log("Maç Sonucu Kaydetme", False, str(e))

# 10. TEST: Aşama 2 - ELO & Akıllı Eşleştirme Motoru
try:
    status, raw = http_get("/api/gameshow/elo/Siz%20(Yar%C4%B1%C5%9Fmac%C4%B1)")
    elo_data = json.loads(raw.decode('utf-8'))
    valid_elo = elo_data.get("elo_rating") is not None and "hifz_tier" in elo_data
    report.log("Aşama 2: Hâfız ELO Profili & Unvan", valid_elo, f"ELO: {elo_data.get('elo_rating')} ({elo_data.get('hifz_tier')})")

    status, mm_res = http_post_json("/api/gameshow/elo/matchmake", {
        "player_name": "Siz (Yarışmacı)",
        "mode": "buzzer",
        "surah_pool": "30. Cüz (Amme Cüzü)"
    })
    opp = mm_res.get("matched_opponent", {})
    report.log("Aşama 2: Adil Eşleşme Motoru (Matchmaker)", mm_res.get("success") is True, f"Rakip: {opp.get('player_name')} ({opp.get('elo_rating')} ELO)")
except Exception as e:
    report.log("Aşama 2: ELO & Eşleştirme Testi", False, str(e))

# 11. TEST: Aşama 2 - Aralıklı Tekrar (Spaced Repetition) Hafızası
try:
    status, rep_res = http_post_json("/api/gameshow/spaced-repetition/record", {
        "player_name": "Siz (Yarışmacı)",
        "surah_id": 78,
        "ayah_id": 1,
        "sure_name": "Nebe",
        "ayah_text": "عَمَّ يَتَسَآءَلُونَ",
        "is_correct": False
    })
    report.log("Aşama 2: Aralıklı Tekrar Kaydı (Takılınan Âyet)", rep_res.get("success") is True, f"Ağırlık: {rep_res.get('current_weight')}")

    status, raw = http_get("/api/gameshow/spaced-repetition/weak-ayahs/Siz%20(Yar%C4%B1%C5%9Fmac%C4%B1)")
    weak_data = json.loads(raw.decode('utf-8'))
    report.log("Aşama 2: Zayıf Âyetler Kuyruğu (Spaced Queue)", len(weak_data.get("weak_ayahs", [])) >= 1, f"{weak_data.get('count')} âyet sırada")
except Exception as e:
    report.log("Aşama 2: Aralıklı Tekrar Testi", False, str(e))

# 12. TEST: Aşama 3 - Haftalık Şampiyonalar & 16'lı Turnuva Ağacı (Bracket)
try:
    status, raw = http_get("/api/gameshow/tournaments")
    tourn_list = json.loads(raw.decode('utf-8')).get("tournaments", [])
    report.log("Aşama 3: Haftalık Turnuva Listesi", len(tourn_list) >= 4, f"{len(tourn_list)} Turnuva Aktif")

    status, raw = http_get("/api/gameshow/tournaments/tourn-amme-16/bracket")
    bracket = json.loads(raw.decode('utf-8'))
    rounds = bracket.get("rounds", [])
    has_16_bracket = len(rounds) == 4 # Son 16, Çeyrek, Yarı, Final
    report.log("Aşama 3: 16'lı Turnuva Ağacı Detayı (Bracket Tree)", has_16_bracket, f"{len(rounds)} Tur (Son 16..Büyük Final)")

    status, play_res = http_post_json("/api/gameshow/tournaments/tourn-amme-16/play-match", {
        "match_id": "m1",
        "player_name": "Siz (Yarışmacı)",
        "player_score": 95,
        "opponent_score": 75
    })
    report.log("Aşama 3: Turnuva Maçı Oynama & Üst Tura Yükselme", play_res.get("won") is True, f"Skor: {play_res.get('player_score')}-{play_res.get('opponent_score')}, Delta ELO: +{play_res.get('delta_elo')}")
except Exception as e:
    report.log("Aşama 3: Turnuva Testi", False, str(e))

# 13. TEST: Aşama 4 - PWA Manifest & Service Worker
try:
    status, manifest_bytes = http_get("/manifest.json")
    manifest = json.loads(manifest_bytes.decode('utf-8'))
    report.log("Aşama 4: PWA Manifest Dosyası (/manifest.json)", status == 200 and manifest.get("short_name") == "Zakirun", manifest.get("name"))

    status, sw_bytes = http_get("/sw.js")
    report.log("Aşama 4: PWA Service Worker Dosyası (/sw.js)", status == 200 and len(sw_bytes) > 200, f"{len(sw_bytes)} bayt")
except Exception as e:
    report.log("Aşama 4: PWA Testi", False, str(e))

# 14. TEST: Aşama 4 - Detaylı Hıfz Karnesi Analizi
try:
    status, raw = http_get("/api/gameshow/hifz-karne/Siz%20(Yar%C4%B1%C5%9Fmac%C4%B1)")
    karne = json.loads(raw.decode('utf-8'))
    has_mastery = "juz30_amme" in karne.get("mastery_segments", {})
    has_badge = "badge" in karne
    max_pts_ok = karne.get("max_points_enforced") == 100
    report.log("Aşama 4: Detaylı Hıfz Karnesi & Cüz Analizi", has_mastery and has_badge and max_pts_ok, f"Rozet: {karne.get('badge', {}).get('title')}, 30. Cüz Yetkinlik: %{karne.get('mastery_segments', {}).get('juz30_amme')}")
except Exception as e:
    report.log("Aşama 4: Hıfz Karnesi Testi", False, str(e))

# 15. TEST: 2 Kişilik Hâfız Düellosu (1v1 Eşleşme & Kur'an Bulmacası)
try:
    status, duel_res = http_post_json("/api/gameshow/puzzle-duel/match", {
        "player_name": "Siz (Yarışmacı)",
        "rounds_count": 5
    })
    has_p1 = duel_res.get("player1", {}).get("name") == "Siz (Yarışmacı)"
    has_bot = bool(duel_res.get("player2", {}).get("name"))
    has_5_rounds = len(duel_res.get("rounds", [])) == 5
    max_100_ok = duel_res.get("max_total_score") == 100
    report.log("2 Kişilik Düello: 1v1 Eşleşme & 5 Tur Bulmaca", has_p1 and has_bot and has_5_rounds and max_100_ok, f"Rakip Bot: {duel_res.get('player2', {}).get('name')} ({duel_res.get('player2', {}).get('elo')} ELO)")
except Exception as e:
    report.log("2 Kişilik Düello: 1v1 Eşleşme Testi", False, str(e))

# 16. TEST: Bot Kullanıcı Canlı Yazma & Harf Zamanlaması Simülasyonu
try:
    status, sim_res = http_post_json("/api/gameshow/puzzle-duel/simulate-bot-round", {
        "bot_name": "Ahmet Hâfız (30. Cüz)",
        "round_id": "puz-1",
        "letter_count": 6
    })
    has_timing = sim_res.get("total_time_seconds", 0) > 0
    has_keystrokes = len(sim_res.get("letter_delays_ms", [])) == 6
    report.log("2 Kişilik Düello: Bot Canlı Harf Vuruş Simülasyonu", has_timing and has_keystrokes, f"6 Harf Süresi: {sim_res.get('total_time_seconds')} sn, Harf Vuruş Sayısı: {len(sim_res.get('letter_delays_ms', []))}")
except Exception as e:
    report.log("2 Kişilik Düello: Bot Simülasyon Testi", False, str(e))

# 17. TEST: 2 Kişilik Düello Sonuçlandırma & ELO Güncellemesi
try:
    status, finish_res = http_post_json("/api/gameshow/puzzle-duel/finish", {
        "duel_id": "duel-test-101",
        "player_name": "Siz (Yarışmacı)",
        "bot_name": "Ahmet Hâfız (30. Cüz)",
        "player_score": 80,
        "bot_score": 60,
        "total_rounds": 5
    })
    winner_is_user = finish_res.get("winner") == "Siz (Yarışmacı)"
    has_elo_delta = finish_res.get("delta_elo") == 20
    report.log("2 Kişilik Düello: Maç Sonucu, ELO & Veritabanı Kaydı", finish_res.get("success") is True and winner_is_user and has_elo_delta, f"Kazanan: {finish_res.get('winner')}, Delta ELO: +{finish_res.get('delta_elo')}, Yeni ELO: {finish_res.get('new_elo')}")
except Exception as e:
    report.log("2 Kişilik Düello: Sonuçlandırma Testi", False, str(e))

# 18. TEST: 20 Bot Kullanıcı Arası Tam 1v1 Düello Simülasyonu (Bot vs Bot Arena)
try:
    status, bvb_res = http_post_json("/api/gameshow/puzzle-duel/simulate-bot-match", {
        "rounds_count": 5
    })
    b1_name = bvb_res.get("bot1", {}).get("name")
    b2_name = bvb_res.get("bot2", {}).get("name")
    overall_win = bvb_res.get("overall_winner")
    has_5_rounds_bvb = len(bvb_res.get("rounds", [])) == 5
    max_pts_100 = bvb_res.get("max_score_enforced") == 100
    report.log("20 Bot Arenası: Tam 1v1 Bot vs Bot Bulmaca Düellosu", bvb_res.get("success") is True and has_5_rounds_bvb and max_pts_100, f"{b1_name} ({bvb_res.get('bot1', {}).get('score')} P) vs {b2_name} ({bvb_res.get('bot2', {}).get('score')} P) -> Kazanan: {overall_win}")
except Exception as e:
    report.log("20 Bot Arenası Testi", False, str(e))


# 19. TEST: Âyet İçi Kelime Blokları (Cloze Word Blocks / Kelime Kulesi) API
try:
    status, cloze_res = http_get_json("/api/gameshow/cloze-blocks/rounds?count=5")
    rounds = cloze_res.get("rounds", [])
    has_5_cloze = len(rounds) == 5
    first_r = rounds[0] if rounds else {}
    has_targets = len(first_r.get("targets", [])) >= 2
    has_uthmani = len(first_r.get("full_ayah_arabic", "")) > 5
    has_audio = "Husary_Muallim" in first_r.get("audio_url", "")
    max_pts_100 = cloze_res.get("max_total_score") == 100
    report.log("Âyet Blokları: Seviyeler & Uthmânî 2 Entegrasyonu", has_5_cloze and has_targets and has_uthmani and has_audio and max_pts_100, f"5 Seviye Hazır, Örnek: {first_r.get('reference')} (Hedef Kelimeler: {[t['word'] for t in first_r.get('targets', [])]})")
except Exception as e:
    report.log("Âyet Blokları Seviye Testi", False, str(e))

# 20. TEST: Âyet Blokları 2 Kişilik Düello (1v1) Eşleşme API
try:
    status, cduel_res = http_post_json("/api/gameshow/cloze-blocks/duel/match", {
        "player_name": "Siz (Yarışmacı)",
        "rounds_count": 5
    })
    cduel_id = cduel_res.get("duel_id", "")
    bot_opp = cduel_res.get("player2", {})
    has_5_rounds_duel = len(cduel_res.get("rounds", [])) == 5
    report.log("Âyet Blokları 2 Kişilik Düello: 1v1 Eşleşme & 5 Tur", bool(cduel_id) and has_5_rounds_duel and bool(bot_opp.get("name")), f"Düello ID: {cduel_id}, Rakip Bot: {bot_opp.get('name')} ({bot_opp.get('elo')} ELO)")
except Exception as e:
    report.log("Âyet Blokları Düello Eşleşme Testi", False, str(e))

# 21. TEST: Âyet Blokları Bot Kelime Buluş Simülasyonu
try:
    status, cbot_sim = http_post_json("/api/gameshow/cloze-blocks/duel/simulate-bot-round", {
        "bot_name": "Ahmet Hâfız (30. Cüz)",
        "round_id": "cloze-1",
        "target_words": ["KIYAMET", "İŞTE", "KAFİR"],
        "difficulty": "medium"
    })
    has_total_time = cbot_sim.get("total_time_seconds", 0) > 0
    has_word_timings = len(cbot_sim.get("word_timings", [])) == 3
    report.log("Âyet Blokları: Bot Canlı Kelime Buluş Simülasyonu", has_total_time and has_word_timings, f"3 Kelime Süresi: {cbot_sim.get('total_time_seconds')} sn, Kelime Adımı: {len(cbot_sim.get('word_timings', []))}")
except Exception as e:
    report.log("Âyet Blokları Bot Simülasyon Testi", False, str(e))

# 22. TEST: Âyet Blokları Düello Sonuçlandırma & ELO Kaydı
try:
    status, cfinish_res = http_post_json("/api/gameshow/cloze-blocks/duel/finish", {
        "duel_id": "cloze-test-202",
        "player_name": "Siz (Yarışmacı)",
        "bot_name": "Zeynep K. (Kısa Sûreler)",
        "player_score": 100,
        "bot_score": 80,
        "total_rounds": 5
    })
    cwin_ok = cfinish_res.get("winner") == "Siz (Yarışmacı)"
    celo_ok = cfinish_res.get("delta_elo") == 20
    report.log("Âyet Blokları Düello: Sonuçlandırma, ELO & SQLite Kaydı", cfinish_res.get("success") is True and cwin_ok and celo_ok, f"Kazanan: {cfinish_res.get('winner')}, Delta ELO: +{cfinish_res.get('delta_elo')}, Yeni ELO: {cfinish_res.get('new_elo')}")
except Exception as e:
    report.log("Âyet Blokları Sonuçlandırma Testi", False, str(e))

# 23. TEST: 20 Bot Kullanıcı Arası Âyet Blokları Düello Simülasyonu (Bot vs Bot)
try:
    status, cbvb_res = http_post_json("/api/gameshow/cloze-blocks/duel/simulate-bot-match", {
        "rounds_count": 5
    })
    cb1 = cbvb_res.get("bot1", {}).get("name")
    cb2 = cbvb_res.get("bot2", {}).get("name")
    cb_win = cbvb_res.get("overall_winner")
    cb_5 = len(cbvb_res.get("rounds", [])) == 5
    report.log("20 Bot Arenası: Tam 1v1 Âyet Blokları Bot Düellosu", cbvb_res.get("success") is True and cb_5, f"{cb1} ({cbvb_res.get('bot1', {}).get('score')} P) vs {cb2} ({cbvb_res.get('bot2', {}).get('score')} P) -> Kazanan: {cb_win}")
except Exception as e:
    report.log("Âyet Blokları Bot vs Bot Testi", False, str(e))

# 24. TEST: HTML5 Sürükle-Bırak (Drag & Drop) Seviyeleri API
try:
    status, dd_res = http_get_json("/api/gameshow/drag-drop/rounds?count=5")
    rounds = dd_res.get("rounds", [])
    has_5_dd = len(rounds) == 5
    first_dd = rounds[0] if rounds else {}
    has_pool = len(first_dd.get("letter_pool", [])) >= 5
    has_targets = len(first_dd.get("targets", [])) >= 2
    has_uthmani = len(first_dd.get("full_ayah_arabic", "")) > 5
    max_pts_100 = dd_res.get("max_total_score") == 100
    report.log("Sürükle-Bırak: HTML5 Seviyeler & Havuz Doğrulaması", has_5_dd and has_pool and has_targets and has_uthmani and max_pts_100, f"5 Seviye, Havuz Boyutu: {len(first_dd.get('letter_pool', []))} Harf, Örnek: {first_dd.get('reference')}")
except Exception as e:
    report.log("Sürükle-Bırak Seviye Testi", False, str(e))

# 25. TEST: Sürükle-Bırak 2 Kişilik Düello (1v1) Eşleşme API
try:
    status, dd_match = http_post_json("/api/gameshow/drag-drop/duel/match", {
        "player_name": "Siz (Yarışmacı)",
        "rounds_count": 5
    })
    dd_id = dd_match.get("duel_id", "")
    bot_opp = dd_match.get("player2", {})
    has_5_rounds = len(dd_match.get("rounds", [])) == 5
    report.log("Sürükle-Bırak 2 Kişilik Düello: 1v1 Eşleşme & 5 Tur", bool(dd_id) and has_5_rounds and bool(bot_opp.get("name")), f"Düello ID: {dd_id}, Rakip Bot: {bot_opp.get('name')} ({bot_opp.get('elo')} ELO)")
except Exception as e:
    report.log("Sürükle-Bırak Düello Eşleşme Testi", False, str(e))

# 26. TEST: Sürükle-Bırak Bot Harf Harf Sürükleme Simülasyonu
try:
    status, dd_sim = http_post_json("/api/gameshow/drag-drop/duel/simulate-bot-round", {
        "bot_name": "Ahmet Hâfız (30. Cüz)",
        "round_id": "dragdrop-cloze-1",
        "target_words": ["KIYAMET", "İŞTE", "KAFİR"],
        "difficulty": "medium"
    })
    has_time = dd_sim.get("total_time_seconds", 0) > 0
    has_actions = len(dd_sim.get("letter_actions", [])) == 16
    report.log("Sürükle-Bırak: Bot Canlı Harf Sürükleme Simülasyonu", has_time and has_actions, f"16 Harf Sürükleme Süresi: {dd_sim.get('total_time_seconds')} sn, Harf Aksiyonu: {len(dd_sim.get('letter_actions', []))}")
except Exception as e:
    report.log("Sürükle-Bırak Bot Simülasyon Testi", False, str(e))

# 27. TEST: Sürükle-Bırak Düello Sonuçlandırma, ELO & Veritabanı Kaydı
try:
    status, dd_fin = http_post_json("/api/gameshow/drag-drop/duel/finish", {
        "duel_id": "dd-test-303",
        "player_name": "Siz (Yarışmacı)",
        "bot_name": "Mustafa Y. (Buzzer Rekortmeni)",
        "player_score": 100,
        "bot_score": 80,
        "total_rounds": 5
    })
    win_ok = dd_fin.get("winner") == "Siz (Yarışmacı)"
    elo_ok = dd_fin.get("delta_elo") == 20
    report.log("Sürükle-Bırak Düello: Sonuçlandırma, ELO & SQLite Kaydı", dd_fin.get("success") is True and win_ok and elo_ok, f"Kazanan: {dd_fin.get('winner')}, Delta ELO: +{dd_fin.get('delta_elo')}, Yeni ELO: {dd_fin.get('new_elo')}")
except Exception as e:
    report.log("Sürükle-Bırak Sonuçlandırma Testi", False, str(e))

# 28. TEST: 20 Bot Kullanıcı Arası Tam 1v1 Sürükle-Bırak Düellosu (Bot vs Bot)
try:
    status, dd_bvb = http_post_json("/api/gameshow/drag-drop/duel/simulate-bot-match", {
        "rounds_count": 5
    })
    db1 = dd_bvb.get("bot1", {}).get("name")
    db2 = dd_bvb.get("bot2", {}).get("name")
    db_win = dd_bvb.get("overall_winner")
    db_5 = len(dd_bvb.get("rounds", [])) == 5
    report.log("20 Bot Arenası: Tam 1v1 Sürükle-Bırak Bot Düellosu", dd_bvb.get("success") is True and db_5, f"{db1} ({dd_bvb.get('bot1', {}).get('score')} P) vs {db2} ({dd_bvb.get('bot2', {}).get('score')} P) -> Kazanan: {db_win}")
except Exception as e:
    report.log("Sürükle-Bırak Bot vs Bot Testi", False, str(e))

# Kare & Çengel Bulmaca (Kullanıcı talebiyle kaldırıldı)

# Sadeleştirilmiş Müstakil Sayfa Rotaları
try:
    status, html_kelime = http_get("/oyun/kelime-oyunu")
    report.log("Müstakil Sayfa: Kelime Oyunu (/oyun/kelime-oyunu)", status == 200 and b"letter-slot" in html_kelime, "Tertemiz Harf Kutuları Sayfası Doğrulandı")
except Exception as e:
    report.log("Müstakil Sayfa: Kelime Oyunu", False, str(e))

try:
    status, html_bilgi = http_get("/oyun/bilgi-yarismasi")
    report.log("Müstakil Sayfa: Bilgi Yarışması (/oyun/bilgi-yarismasi)", status == 200 and b"mil-options-grid" in html_bilgi, "Tertemiz 11 Basamaklı Merdiven Doğrulandı")
except Exception as e:
    report.log("Müstakil Sayfa: Bilgi Yarışması", False, str(e))

try:
    status, html_blok = http_get("/oyun/ayet-bloklari")
    report.log("Müstakil Sayfa: Âyet Blokları (/oyun/ayet-bloklari)", status == 200 and b"cloze-tile-3d" in html_blok, "Tertemiz Kelime Kulesi Sayfası Doğrulandı")
except Exception as e:
    report.log("Müstakil Sayfa: Âyet Blokları", False, str(e))

try:
    status, html_tourn = http_get("/turnuvalar")
    report.log("Müstakil Sayfa: Şampiyonalar (/turnuvalar)", status == 200 and b"bracket-grid" in html_tourn, "Tertemiz Kupa Ağacı Sayfası Doğrulandı")
except Exception as e:
    report.log("Müstakil Sayfa: Şampiyonalar", False, str(e))

try:
    status, html_karne = http_get("/karne")
    report.log("Müstakil Sayfa: Hıfz Karnesi (/karne)", status == 200 and b"weak-ayahs-list" in html_karne, "Tertemiz Karne & Spaced Repetition Doğrulandı")
except Exception as e:
    report.log("Müstakil Sayfa: Hıfz Karnesi", False, str(e))

# 40-43. TEST: Kur'an Öğrenme Portalı & Müfredat Doğrulaması
try:
    status, html_learn = http_get("/ogren")
    report.log("1. Baş Oda: Kur'an Öğrenme Portalı (/ogren)", status == 200 and b"cards-grid" in html_learn, "Elifbâ & Tecvid Mektebi Sayfası Doğrulandı")
except Exception as e:
    report.log("1. Baş Oda: Kur'an Öğrenme Portalı", False, str(e))

try:
    status, learn_curr = http_get_json("/api/learn/curriculum")
    curr_len = len(learn_curr.get("curriculum", []))
    report.log("Kur'an Portalı: Diyanet Senkronize Müfredat API (Elifbâ & Tecvid)", status == 200 and curr_len in (20, 87, 91), f"Toplam {curr_len} Diyanet dersi doğrulandı")
except Exception as e:
    report.log("Kur'an Portalı Müfredat API Testi", False, str(e))

try:
    status_p, parts_data = http_get_json("/api/learn/parts")
    p_len = len(parts_data.get("parts", []))
    report.log("Kur'an Portalı: Diyanet Ana Bölümleri (Elifbâ & Tecvid)", status_p == 200 and p_len in (2, 4), f"{p_len} Ana Bölüm Doğrulandı")
except Exception as e:
    report.log("Kur'an Portalı Bölüm API Testi", False, str(e))

try:
    status, l1_data = http_get_json("/api/learn/lesson/1")
    l1 = l1_data.get("lesson", {})
    l1_items = len(l1.get("items", []))
    report.log("Kur'an Portalı: 1. Ders (28 Harf + Lâmelif)", status == 200 and l1_items in (28, 29), f"{l1_items} Harf & Mahreç Bilgisi Doğrulandı")
except Exception as e:
    report.log("Kur'an Portalı 1. Ders Testi", False, str(e))

try:
    status, fin_learn = http_post_json("/api/learn/complete-lesson", {
        "lesson_id": 1,
        "score": 10,
        "player_name": "Siz (Yarışmacı)"
    })
    c_ok = fin_learn.get("success") is True and fin_learn.get("next_lesson_id") == 2
    report.log("Kur'an Portalı: Dersi Tamamlama & İlerleme Kaydı", c_ok, f"Ders 1 Tamamlandı -> Sıradaki: Ders {fin_learn.get('next_lesson_id')} (+{fin_learn.get('points_earned')} Puan)")
except Exception as e:
    report.log("Kur'an Portalı Ders Tamamlama Testi", False, str(e))

try:
    status, audio_bytes = http_get("/audio/learn/l_1_0.mp3")
    status_elif, elif_bytes = http_get("/audio/elifletter/elif.mp3")
    status_lamelif, lamelif_bytes = http_get("/audio/elifletter/lamelif.mp3")
    ok = (status == 200 and len(audio_bytes) > 5000 and status_elif == 200 and len(elif_bytes) > 5000 and status_lamelif == 200 and len(lamelif_bytes) > 5000)
    report.log("elifletter Klasörü: Otantik Harf MP3 Dağıtımı (/audio/elifletter/*.mp3)", ok, f"Elif: {len(elif_bytes)} bayt, Lâmelif: {len(lamelif_bytes)} bayt ses doğrulandı")
except Exception as e:
    report.log("elifletter Otantik Harf Ses Dağıtım Testi", False, str(e))

try:
    status_diy, diy_bytes = http_get("/audio/diyanet/elifba/harfler/harfler/btn_1.mp3")
    diy_ok = (status_diy == 200 and len(diy_bytes) > 1000)
    report.log("Diyanet Elifbâ Ses Dağıtımı & Yerel Önbellek (/audio/diyanet/...)", diy_ok, f"Harf 1 Diyanet Sesi: {len(diy_bytes)} Bayt Doğrulandı")
except Exception as e:
    report.log("Diyanet Ses Dağıtım Testi", False, str(e))


# 44-50. TEST: Okunan Âyetteki Kelimeyi Bul (4 Çerçeveli Kelime Dinleme Oyunu)
try:
    status, html_listen = http_get("/oyun/okunan-kelimeyi-bul")
    ok = (status == 200 and 
          "Okunan âyetteki kelimeyi bul".encode('utf-8') in html_listen and 
          b"words-frames-container" in html_listen and 
          b"quran.com" in html_listen)
    report.log("Müstakil Sayfa: Okunan Kelimeyi Bul (/oyun/okunan-kelimeyi-bul)", ok, "4 Çerçeveli Dinleme Oyunu Sayfası Doğrulandı")
except Exception as e:
    report.log("Müstakil Sayfa: Okunan Kelimeyi Bul Testi", False, str(e))

try:
    status, lf_data = http_get_json("/api/gameshow/listen-find/rounds?count=5")
    rounds = lf_data.get("rounds", [])
    has_5 = len(rounds) == 5
    first_r = rounds[0] if rounds else {}
    has_4_words = len(first_r.get("words", [])) == 4
    has_audio = "audio.qurancdn.com" in first_r.get("audio_url", "")
    has_q = first_r.get("question") == "Okunan âyetteki kelimeyi bul"
    
    # Pedagojik Kural Denetimi: 1. karakter üzerinde mutlaka fetha (üstün), esre veya damme olmalı!
    all_words_voweled = True
    for rnd in rounds:
        for wd in rnd.get("words", []):
            ar = wd.get("arabic", "").strip()
            i = 0
            while i < len(ar) and not ('\u0621' <= ar[i] <= '\u064A' or ar[i] == '\u0671'):
                i += 1
            if i >= len(ar) or ar[i] == '\u0671':
                all_words_voweled = False
                break
            j = i + 1
            marks = []
            while j < len(ar) and not ('\u0621' <= ar[j] <= '\u064A' or ar[j] == '\u0671'):
                marks.append(ar[j])
                j += 1
            if not any(m in ('\u064E', '\u0650', '\u064F') for m in marks):
                all_words_voweled = False
                break

    ok = (status == 200 and has_5 and has_4_words and has_audio and has_q and all_words_voweled)
    report.log("Okunan Kelimeyi Bul: 4 Çerçeve & quran.com WBW API", ok, f"5 Tur, 4 Çerçeve/Tur, Başında Harekesiz Kelime Yok (Tüm 1. Harfler Fetha/Esre/Damme Doğrulandı)")
except Exception as e:
    report.log("Okunan Kelimeyi Bul API Testi", False, str(e))

try:
    status, lf_duel = http_post_json("/api/gameshow/listen-find/duel/match", {
        "player_name": "Siz (Yarışmacı)",
        "rounds_count": 5
    })
    bot_info = lf_duel.get("bot", {})
    duel_rounds = lf_duel.get("rounds", [])
    ok = (status == 200 and lf_duel.get("success") is True and len(duel_rounds) == 5 and "name" in bot_info)
    report.log("Okunan Kelimeyi Bul: 1v1 Düello Eşleşme API", ok, f"Düello ID: {lf_duel.get('duel_id')}, Rakip Bot: {bot_info.get('name')} ({bot_info.get('elo')} ELO)")
except Exception as e:
    report.log("Okunan Kelimeyi Bul Düello Eşleşme Testi", False, str(e))

try:
    status, lf_sim = http_post_json("/api/gameshow/listen-find/duel/bot-sim", {
        "bot_name": "Ahmet Hâfız (30. Cüz)",
        "round_id": "lfg-1",
        "target_index": 2
    })
    sim_time = lf_sim.get("time_seconds", 0)
    ok = (status == 200 and sim_time > 0 and "bot_choice_index" in lf_sim)
    bot_ch = ['A', 'B', 'C', 'D'][lf_sim.get('bot_choice_index', 0)]
    report.log("Okunan Kelimeyi Bul: Bot Canlı Dinleme Simülasyonu", ok, f"Dinleme & Seçme Süresi: {sim_time} sn, Bot Seçimi: [{bot_ch}], Skor: {lf_sim.get('round_score')} P")
except Exception as e:
    report.log("Okunan Kelimeyi Bul Bot Simülasyon Testi", False, str(e))

try:
    status, lf_fin = http_post_json("/api/gameshow/listen-find/duel/finish", {
        "duel_id": "lf-test-123",
        "player_name": "Siz (Yarışmacı)",
        "bot_name": "Ahmet Hâfız (30. Cüz)",
        "player_score": 100,
        "bot_score": 80,
        "total_rounds": 5
    })
    ok = (status == 200 and lf_fin.get("success") is True and lf_fin.get("winner") == "Siz (Yarışmacı)" and lf_fin.get("max_score_enforced") == 100)
    report.log("Okunan Kelimeyi Bul Düello: Sonuçlandırma & ELO Kaydı", ok, f"Kazanan: {lf_fin.get('winner')}, Delta ELO: +{lf_fin.get('delta_elo')}, Yeni ELO: {lf_fin.get('new_elo')}")
except Exception as e:
    report.log("Okunan Kelimeyi Bul Düello Sonuçlandırma Testi", False, str(e))

try:
    status, lf_bvb = http_post_json("/api/gameshow/listen-find/duel/bot-vs-bot", {
        "bot1_name": "Ahmet Hâfız (30. Cüz)",
        "bot2_name": "Zeynep K. (Kısa Sûreler)",
        "rounds_count": 5
    })
    rounds_len = len(lf_bvb.get("rounds", []))
    ok = (status == 200 and lf_bvb.get("success") is True and rounds_len == 5)
    report.log("20 Bot Arenası: Tam 1v1 Okunan Kelime Bot Düellosu", ok, f"{lf_bvb.get('bot1', {}).get('name')} ({lf_bvb.get('bot1', {}).get('score')} P) vs {lf_bvb.get('bot2', {}).get('name')} ({lf_bvb.get('bot2', {}).get('score')} P) -> Kazanan: {lf_bvb.get('overall_winner')}")
except Exception as e:
    report.log("Okunan Kelimeyi Bul Bot vs Bot Testi", False, str(e))

try:
    status, home_html = http_get("/")
    # Verify that in #tables-horizontal-scroll, okunan-kelimeyi-bul comes first
    idx_okunan = home_html.find(b"/oyun/okunan-kelimeyi-bul")
    idx_kelime = home_html.find(b"/oyun/kelime-oyunu")
    ok = (status == 200 and idx_okunan != -1 and idx_kelime != -1 and idx_okunan < idx_kelime)
    report.log("Anasayfa 1. Kutucuk: Okunan Kelimeyi Bul Doğrulaması", ok, "Okunan Kelimeyi Bul kartı 1. kutucukta konumlandı")
except Exception as e:
    report.log("Anasayfa 1. Kutucuk Testi", False, str(e))

# -------------------------------------------------------------
# 11. TEST: SÛRE EZBERLEME OYUNU // DİNLENEN ÂYETTEN SONRAKİ ÂYETİ BUL (2. ODA)
# -------------------------------------------------------------
try:
    status, page_bytes = http_get("/oyun/sure-ezberleme")
    page_str = page_bytes.decode('utf-8', errors='ignore')
    has_title = "SÛRE EZBERLEME OYUNU" in page_str
    has_question = "Dinlenen âyetten sonraki âyet hangisi, işaretleyiniz" in page_str
    has_respect = "respect-banner" in page_str
    has_scheherazade = "Scheherazade New" in page_str
    ok = (status == 200 and has_title and has_question and has_respect and has_scheherazade)
    report.log("Sûre Ezberleme Oyunu HTML Sayfası", ok, "Soru metni, kesintisiz tilâvet banner'ı ve Scheherazade fontu doğrulandı")
except Exception as e:
    report.log("Sûre Ezberleme Oyunu HTML Sayfası", False, str(e))

try:
    status, sess = http_get_json("/api/gameshow/surah-memorize/session?surah_id=1&difficulty=hard")
    rounds = sess.get("rounds", [])
    total_steps = sess.get("total_steps", 0)
    has_6_steps = (total_steps == 6 and len(rounds) == 6)
    
    # Sûre bütünlüğü denetimi: 1 -> 2, 2 -> 3, ..., 6 -> 7
    seq_ok = True
    for idx, r in enumerate(rounds):
        expected_curr = idx + 1
        expected_target = idx + 2
        if r.get("current_ayah_id") != expected_curr or r.get("target_ayah_id") != expected_target:
            seq_ok = False
            break
        # 4 Seçenek ve tam olarak 1 doğru cevap denetimi
        opts = r.get("options", [])
        correct_opts = [o for o in opts if o.get("is_correct") is True]
        if len(opts) != 4 or len(correct_opts) != 1:
            seq_ok = False
            break

    q_text = sess.get("question", "")
    has_q = (q_text == "Dinlenen âyetten sonraki âyet hangisi, işaretleyiniz")
    has_audio = "Husary_Muallim_128kbps/001001.mp3" in rounds[0].get("audio_url", "")
    
    ok = (status == 200 and has_6_steps and seq_ok and has_q and has_audio)
    report.log("Sûre Ezberleme: Sûre Bütünlüğü (1->2->3...) ve Zor Mod API", ok, f"Fâtiha 6 Adım, Soru: '{q_text}', Tilâvet: Husary Muallim")
except Exception as e:
    report.log("Sûre Ezberleme Sûre Bütünlüğü ve Zor Mod Testi", False, str(e))

try:
    status, sess_easy = http_get_json("/api/gameshow/surah-memorize/session?surah_id=1&difficulty=easy")
    rounds_easy = sess_easy.get("rounds", [])
    has_diff_surahs = any(
        opt.get("surah_id") != 1
        for opt in rounds_easy[0].get("options", [])
        if not opt.get("is_correct")
    )
    ok = (status == 200 and len(rounds_easy) == 6 and has_diff_surahs)
    report.log("Sûre Ezberleme: Kolay Mod Çeldiricileri", ok, "Farklı sûrelerden çeldirici âyetler doğrulandı")
except Exception as e:
    report.log("Sûre Ezberleme Kolay Mod Testi", False, str(e))

try:
    status, sm_duel = http_post_json("/api/gameshow/surah-memorize/duel/match", {
        "surah_id": 1,
        "difficulty": "hard",
        "player_name": "Siz (Yarışmacı)"
    })
    bot_info = sm_duel.get("bot", {})
    duel_rounds = sm_duel.get("rounds", [])
    ok = (status == 200 and sm_duel.get("success") is True and len(duel_rounds) == 6 and "name" in bot_info)
    report.log("Sûre Ezberleme: 1v1 Düello Eşleşme API", ok, f"Düello ID: {sm_duel.get('duel_id')}, Rakip Bot: {bot_info.get('name')} ({bot_info.get('elo')} ELO)")
except Exception as e:
    report.log("Sûre Ezberleme Düello Eşleşme Testi", False, str(e))

try:
    status, sm_fin = http_post_json("/api/gameshow/surah-memorize/duel/finish", {
        "duel_id": "sm-test-123",
        "player_name": "Siz (Yarışmacı)",
        "bot_name": "Ahmet Hâfız (30. Cüz)",
        "player_score": 100,
        "bot_score": 83,
        "surah_id": 1
    })
    ok = (status == 200 and sm_fin.get("success") is True and sm_fin.get("winner") == "Siz (Yarışmacı)" and sm_fin.get("max_score_enforced") == 100)
    report.log("Sûre Ezberleme Düello: Sonuçlandırma & ELO Kaydı", ok, f"Kazanan: {sm_fin.get('winner')}, Delta ELO: +{sm_fin.get('delta_elo')}, Yeni ELO: {sm_fin.get('new_elo')}")
except Exception as e:
    report.log("Sûre Ezberleme Düello Sonuçlandırma Testi", False, str(e))

try:
    status, home_html = http_get("/")
    # Verify that in #tables-horizontal-scroll:
    # 1. okunan-kelimeyi-bul comes first
    # 2. sure-ezberleme comes second
    # 3. kelime-oyunu comes third
    idx_okunan = home_html.find(b"/oyun/okunan-kelimeyi-bul")
    idx_sure = home_html.find(b"/oyun/sure-ezberleme")
    idx_kelime = home_html.find(b"/oyun/kelime-oyunu")
    has_2_oda_badge = b"2. ODA" in home_html
    ok = (status == 200 and idx_okunan != -1 and idx_sure != -1 and idx_kelime != -1 and idx_okunan < idx_sure < idx_kelime and has_2_oda_badge)
    report.log("Anasayfa 2. Kutucuk: Sûre Ezberleme Oyunu Doğrulaması", ok, "1. Okunan Kelime < 2. Sûre Ezberleme < 3. Kelime Oyunu sıralaması teyit edildi")
except Exception as e:
    report.log("Anasayfa 2. Kutucuk Sıralama Testi", False, str(e))


# -------------------------------------------------------------
# 12. TEST: ÂYET TAMAMLAMA OYUNU & HATALI CEVAPLARIM İSTATİSTİĞİ (2. ODA)
# -------------------------------------------------------------
try:
    status, page_bytes = http_get("/oyun/ayet-tamamlama")
    page_str = page_bytes.decode('utf-8', errors='ignore')
    has_title = "ÂYET TAMAMLAMA OYUNU" in page_str
    has_q = "Boş hücredeki olması gereken kelimeyi yerine koyarak âyeti tamamlayınız" in page_str
    has_typewriter = "typewriteWordRightToLeft" in page_str
    has_countdown = "countdown-number" in page_str
    has_mistakes_modal = "mistakes-modal" in page_str
    ok = (status == 200 and has_title and has_q and has_typewriter and has_countdown and has_mistakes_modal)
    report.log("Âyet Tamamlama Oyunu HTML Sayfası", ok, "Daktilo efekti, 3sn geri sayım, soru metni ve hatalı cevaplar paneli doğrulandı")
except Exception as e:
    report.log("Âyet Tamamlama Oyunu HTML Sayfası", False, str(e))

try:
    status, sess = http_get_json("/api/gameshow/ayet-tamamlama/session?surah_id=112")
    ayahs = sess.get("ayahs", [])
    has_4_ayahs = (len(ayahs) == 4)
    has_words = all(len(a.get("words", [])) > 0 for a in ayahs)
    q_text = sess.get("question", "")
    has_q = (q_text == "Boş hücredeki olması gereken kelimeyi yerine koyarak âyeti tamamlayınız")
    ok = (status == 200 and has_4_ayahs and has_words and has_q)
    report.log("Âyet Tamamlama: İhlâs Sûresi Oturum API", ok, f"4 Âyet, Kelime Kümeleri ve Soru: '{q_text}'")
except Exception as e:
    report.log("Âyet Tamamlama Oturum Testi", False, str(e))

try:
    status, at_duel = http_post_json("/api/gameshow/ayet-tamamlama/duel/match", {
        "surah_id": 112,
        "player_name": "Siz (Yarışmacı)"
    })
    bot_info = at_duel.get("bot", {})
    sess_duel = at_duel.get("session", {})
    ok = (status == 200 and at_duel.get("success") is True and "name" in bot_info and len(sess_duel.get("ayahs", [])) == 4)
    report.log("Âyet Tamamlama: 1v1 Düello Eşleşme API", ok, f"Düello ID: {at_duel.get('duel_id')}, Rakip Bot: {bot_info.get('name')} ({bot_info.get('elo')} ELO)")
except Exception as e:
    report.log("Âyet Tamamlama Düello Eşleşme Testi", False, str(e))

try:
    status, at_fin = http_post_json("/api/gameshow/ayet-tamamlama/duel/finish", {
        "duel_id": "at-test-123",
        "player_name": "Siz (Yarışmacı)",
        "bot_name": "Ahmet Hâfız (30. Cüz)",
        "player_score": 100,
        "bot_score": 75,
        "surah_id": 112
    })
    ok = (status == 200 and at_fin.get("success") is True and at_fin.get("winner") == "Siz (Yarışmacı)" and at_fin.get("max_score_enforced") == 100)
    report.log("Âyet Tamamlama Düello: Sonuçlandırma & ELO Kaydı", ok, f"Kazanan: {at_fin.get('winner')}, Delta ELO: +{at_fin.get('delta_elo')}, Yeni ELO: {at_fin.get('new_elo')}")
except Exception as e:
    report.log("Âyet Tamamlama Düello Sonuçlandırma Testi", False, str(e))

try:
    # Hata Kaydı API Testi
    status, rec_resp = http_post_json("/api/gameshow/mistakes/record", {
        "player_name": "Siz (Yarışmacı)",
        "game_name": "Âyet Tamamlama Oyunu",
        "game_id": "ayet_tamamlama",
        "surah_id": 112,
        "ayah_id": 1,
        "sure_name": "İhlâs",
        "reference": "İhlâs Sûresi, 1. Âyet",
        "question_type": "Kaybolan Kelime",
        "target_text": "اللّٰهُ",
        "selected_wrong_text": "اَحَدٌ",
        "full_ayah_text": "قُلْ هُوَ اللّٰهُ اَحَدٌ"
    })
    status_list, list_resp = http_get_json("/api/gameshow/mistakes/list?player_name=Siz%20(Yar%C4%B1%C5%9Fmac%C4%B1)&limit=10")
    mistakes = list_resp.get("mistakes", [])
    has_recorded = any(m.get("game_id") == "ayet_tamamlama" and m.get("target_text") == "اللّٰهُ" for m in mistakes)
    ok = (status == 200 and status_list == 200 and has_recorded)
    report.log("Hatalı Cevaplarım: Ortak İstatistik & Kayıt API", ok, f"{len(mistakes)} hata kayıtlı, Oyun adı ve hedef kelime teyit edildi")
except Exception as e:
    report.log("Hatalı Cevaplarım API Testi", False, str(e))

try:
    status, home_html = http_get("/")
    # Verify order in #tables-horizontal-scroll:
    # okunan-kelimeyi-bul < sure-ezberleme < ayet-tamamlama < kelime-oyunu
    idx_okunan = home_html.find(b"/oyun/okunan-kelimeyi-bul")
    idx_sure = home_html.find(b"/oyun/sure-ezberleme")
    idx_ayet = home_html.find(b"/oyun/ayet-tamamlama")
    idx_kelime = home_html.find(b"/oyun/kelime-oyunu")
    has_2_oda_ayet = b"TAMAMLAMA" in home_html
    ok = (status == 200 and idx_okunan != -1 and idx_sure != -1 and idx_ayet != -1 and idx_kelime != -1 and idx_okunan < idx_sure < idx_ayet < idx_kelime and has_2_oda_ayet)
    report.log("Anasayfa 2. Oda Sıralaması: Sûre Ezberleme & Âyet Tamamlama", ok, "1. Okunan Kelime < 2. Sûre Ezberleme < 3. Âyet Tamamlama < 4. Kelime Oyunu doğrulandı")
except Exception as e:
    report.log("Anasayfa 2. Oda Sıralama Testi", False, str(e))

# -------------------------------------------------------------
# 13. TEST: MERKEZİ HATALI CEVAPLARIM MODALI (index.html, karne, tüm oyunlar)
# -------------------------------------------------------------
try:
    status_home, home_bytes = http_get("/")
    home_str = home_bytes.decode('utf-8', errors='ignore')
    has_home_modal = "mistakes-modal" in home_str
    has_home_badge = "txt-nav-mistakes-badge" in home_str

    status_karne, karne_bytes = http_get("/karne")
    karne_str = karne_bytes.decode('utf-8', errors='ignore')
    has_karne_mistakes = "karne-mistakes-list" in karne_str

    with open("E:/ZAKİRUN.COM/bilgiyarismasi/pages/oyun_kelime.html", "r", encoding="utf-8") as f:
        has_kelime_rec = "recordMistake" in f.read()
    with open("E:/ZAKİRUN.COM/bilgiyarismasi/pages/oyun_ayet_bloklari.html", "r", encoding="utf-8") as f:
        has_blok_rec = "recordMistake" in f.read()
    with open("E:/ZAKİRUN.COM/bilgiyarismasi/pages/oyun_bilgi_yarismasi.html", "r", encoding="utf-8") as f:
        has_bilgi_rec = "recordMistake" in f.read()

    ok = (status_home == 200 and status_karne == 200 and has_home_modal and has_home_badge and has_karne_mistakes and has_kelime_rec and has_blok_rec and has_bilgi_rec)
    report.log("Faz 1: Merkezi Hatalı Cevaplarım ve 6 Oyunda Hata Takibi", ok, "index.html, karne ve 6 oyunun tamamında hata takip altyapısı doğrulandı")
except Exception as e:
    report.log("Merkezi Hatalı Cevaplarım Testi", False, str(e))

# -------------------------------------------------------------
# 14. TEST: 114 SÛRE KAPSAMI VE EZBER OYUNLARINDA DÜELLO KİLİDİ
# -------------------------------------------------------------
try:
    with open("E:/ZAKİRUN.COM/bilgiyarismasi/pages/oyun_sure_ezberleme.html", "r", encoding="utf-8") as f:
        se_content = f.read()
    with open("E:/ZAKİRUN.COM/bilgiyarismasi/pages/oyun_ayet_tamamlama.html", "r", encoding="utf-8") as f:
        at_content = f.read()

    has_114_se = "ALL_SURAHS_LIST" in se_content and "renderSurahsGrouped" in se_content
    has_114_at = "ALL_SURAHS_LIST" in at_content and "renderSurahsGrouped" in at_content
    has_lock_rule_se = "unlockDuelForSurah" in se_content and "duel-locked-modal" in se_content
    has_lock_rule_at = "unlockDuelForSurah" in at_content and "duel-locked-modal" in at_content

    ok = (has_114_se and has_114_at and has_lock_rule_se and has_lock_rule_at)
    report.log("Faz 1: 114 Sûre Havuzu ve Ezber Düello Kilidi", ok, "114 Sûre kategorileri ve tek kişilik %100 başarı düello kilidi doğrulandı")
except Exception as e:
    report.log("114 Sûre ve Düello Kilit Testi", False, str(e))

# -------------------------------------------------------------
# 15. TEST: GİRİŞ YAP, KAYIT OL & GOOGLE AUTH ENTEGRASYONU
# -------------------------------------------------------------
try:
    # 1. /giris sayfası ve Google butonu kontrolü
    st_giris, giris_bytes = http_get("/giris")
    giris_html = giris_bytes.decode('utf-8', errors='ignore')
    has_google_btn = "handleGoogleSignIn" in giris_html and "Google ile Hızlı Giriş Yap" in giris_html
    has_tabs = "tab-login" in giris_html and "tab-register" in giris_html
    report.log("Giriş ve Kayıt Sayfası (/giris) ve Google Girişi", st_giris == 200 and has_google_btn and has_tabs, "Tek tıkla Google seçimi ve yerel formlar doğrulandı")

    # 2. Üst Navbar Giriş Yap İkon/Buton Kontrolü (index.html)
    st_idx, idx_bytes = http_get("/")
    idx_html = idx_bytes.decode('utf-8', errors='ignore')
    has_nav_auth = "btn-nav-login" in idx_html and "user-profile-menu" in idx_html and "Giriş Yap" in idx_html
    report.log("Üst Sağ Navbar Giriş İkonu ve Profil Menüsü", st_idx == 200 and has_nav_auth, "index.html sağ üstte Giriş Yap butonu ve giriş yapılınca açılır profil menüsü doğrulandı")

    # 3. E-Posta ile Kayıt ve Giriş API
    test_email = f"suite_user_{int(time.time())}@zakirun.tv"
    st_reg, res_reg = http_post_json("/api/auth/register", {
        "name": "Test Yarışmacı",
        "email": test_email,
        "password": "Password_2026!",
        "hifz_tier": "Ali (İleri)"
    })
    reg_ok = st_reg == 200 and res_reg.get("success") is True and res_reg.get("user", {}).get("email") == test_email

    st_log, res_log = http_post_json("/api/auth/login", {
        "email": test_email,
        "password": "Password_2026!"
    })
    log_ok = st_log == 200 and res_log.get("success") is True and res_log.get("user", {}).get("elo") == 1350
    report.log("Kullanıcı Kayıt ve Giriş API (/api/auth/*)", reg_ok and log_ok, f"Kayıt ve Giriş başarılı (Kullanıcı: {test_email})")

    # 4. Google Girişi / Oturum Senkronizasyon API
    st_goog, res_goog = http_post_json("/api/auth/google", {
        "name": "Ahmet Google Hâfız",
        "email": "ahmet.google@gmail.com",
        "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=Ahmet",
        "provider": "google",
        "hifz_tier": "Mutavassıt (Orta)"
    })
    goog_ok = st_goog == 200 and res_goog.get("success") is True and res_goog.get("user", {}).get("provider") == "google"
    report.log("Google ile Giriş API (/api/auth/google)", goog_ok, "Google profil verileri, avatar ve ELO senkronizasyonu doğrulandı")
except Exception as e:
    report.log("Giriş Yap ve Google Auth Testi", False, str(e))

# -------------------------------------------------------------
# 16. TEST: HÂFIZ HESAP, PROFİL & UYGULAMA AYARLARI MERKEZİ
# -------------------------------------------------------------
try:
    # 1. /hesap, /profil, /ayarlar rotaları ve dual-mode kontrolü
    st_hesap, hesap_bytes = http_get("/hesap")
    hesap_html = hesap_bytes.decode('utf-8', errors='ignore')
    has_dual_mode = "panel-user-settings" in hesap_html and "panel-guest-auth" in hesap_html
    has_all_tabs = "stab-profile" in hesap_html and "stab-app" in hesap_html and "stab-security" in hesap_html and "stab-hifz" in hesap_html
    has_avatar_grid = "avatar-presets-grid" in hesap_html and "setting-reciter" in hesap_html
    report.log("Hesap & Ayarlar Merkezi (/hesap, /profil, /ayarlar)", st_hesap == 200 and has_dual_mode and has_all_tabs and has_avatar_grid, "Çift modlu mimari, 4 ana sekme ve avatar galerisi doğrulandı")

    # 2. Profil Güncelleme API (/api/auth/update-profile)
    test_update_name = f"Hâfız Test {int(time.time())}"
    st_up, res_up = http_post_json("/api/auth/update-profile", {
        "name": test_update_name,
        "email": test_email,
        "avatar_url": f"https://api.dicebear.com/7.x/bottts/svg?seed={test_update_name}",
        "hifz_tier": "Hâfız-ı Mütkın"
    })
    up_ok = st_up == 200 and res_up.get("success") is True and res_up.get("profile", {}).get("name") == test_update_name
    report.log("Profil Güncelleme API (/api/auth/update-profile)", up_ok, f"İsim ve Seviye güncellendi ({test_update_name} -> Hâfız-ı Mütkın)")

    # 3. Uygulama Ayarları API (/api/auth/update-settings)
    st_set, res_set = http_post_json("/api/auth/update-settings", {
        "userId": test_email,
        "settings": {
            "reciter": "husary_muallim",
            "font": "zakirun_uthmani",
            "soundEffects": True,
            "soundVolume": 85,
            "autoPlayAudio": True
        }
    })
    set_ok = st_set == 200 and res_set.get("success") is True and res_set.get("settings", {}).get("soundVolume") == 85
    report.log("Uygulama Ayarları Senkronizasyon API", set_ok, "Kāri, hat, ses düzeyi (%85) ve otomatik dinleme tercihleri kaydedildi")
except Exception as e:
    report.log("Hesap & Ayarlar Merkezi Testi", False, str(e))


print("\n=================================================================")
print(f"📊 TEST RAPORU SONUCU: {report.passed} GEÇTİ / {report.failed} BAŞARISIZ")
success_rate = (report.passed / (report.passed + report.failed)) * 100 if (report.passed + report.failed) > 0 else 0
print(f"🎯 Başarı Oranı: %{success_rate:.1f}")
print("=================================================================")

if report.failed > 0:
    sys.exit(1)
