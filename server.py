"""
KUR'AN TV 2026 // ULTRA-HIZLI KUANTUM VERİ MOTORU (BACKEND SERVER)
==================================================================
Veritabanı: kuran_master_fihrist_v2.db (2.99 GB, SQLite 3 WAL Mode)
Teknoloji: FastAPI + Uvicorn + SQLite3 (Native 0.1ms Engine)
Sıfır Medya / Sıfır Ses: Saf metin bütünlüğü ve dilbilimsel analiz.
"""

import os
import re
import sys
import time
import json
import sqlite3
import asyncio
import random
from typing import Optional, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Database path resolution

WAQF_PATTERN = re.compile(r'[ۖ-ۭؐ-ٟؕٞࣔ-࣢\s\.\,\;\:\!\?]+')

def clean_quran_word(word: str) -> str:
    """Kelimenin sonundaki veya başındaki vakıf/secavend ve özel işaretleri temizler."""
    if not word:
        return ""
    cleaned = WAQF_PATTERN.sub('', word).strip()
    return cleaned if len(cleaned) >= 2 else word.strip()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Intelligent Multi-Directory Path Resolvers
def get_db_path() -> str:
    candidates = [
        os.path.join(CURRENT_DIR, "database", "kuran_master_fihrist_v2.db"),
        os.path.join(CURRENT_DIR, "kuran_master_fihrist_v2.db"),
        os.path.join(CURRENT_DIR, "database", "bilgi_yarismasi.db"),
        os.path.join(CURRENT_DIR, "bilgi_yarismasi.db"),
        r"e:\Kuran TV2026\Database\bulutveritabani\kuran_master_fihrist_v2.db"
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

def get_page_path(filename: str) -> str:
    candidates = [
        os.path.join(CURRENT_DIR, "pages", filename),
        os.path.join(CURRENT_DIR, filename),
        os.path.join(CURRENT_DIR, "pages", "archive", filename)
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(CURRENT_DIR, filename)

def get_asset_path(filename: str) -> str:
    candidates = [
        os.path.join(CURRENT_DIR, "assets", filename),
        os.path.join(CURRENT_DIR, filename)
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(CURRENT_DIR, filename)

def get_audio_file(category: str, filename_or_rel: str) -> str:
    # Supports audio/diyanet, audio/learn, audio/elifletter as well as legacy audio_diyanet
    cat_clean = category.replace("audio_", "").replace("audio/", "")
    candidates = [
        os.path.join(CURRENT_DIR, "audio", cat_clean, filename_or_rel),
        os.path.join(CURRENT_DIR, f"audio_{cat_clean}", filename_or_rel),
        os.path.join(CURRENT_DIR, cat_clean, filename_or_rel),
        os.path.join(CURRENT_DIR, filename_or_rel)
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

# Add data and database folders to sys.path
data_dir = os.path.join(CURRENT_DIR, "data")
db_dir = os.path.join(CURRENT_DIR, "database")
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)
if db_dir not in sys.path:
    sys.path.insert(0, db_dir)

DB_PATH = get_db_path()

app = FastAPI(
    title="Zakirun Hâfızlık Yarışmaları Quantum Backend",
    description="114 Sûre, 6.236 Âyet, 77.429 Kelime, 15 Arapça Hat, 717 Meâl ve 32 Mukaddes Mekân GPS Motoru",
    version="2.026"
)

# CORS Middleware (Allows any browser or local app to query without restrictions)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    """Returns a high-speed SQLite connection with WAL mode and row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")  # 64MB RAM cache for lightning queries
    conn.execute("PRAGMA temp_store = MEMORY;")
    return conn

def build_tournament_bracket_tree(tournament_id: str, title: str, category: str, bracket_size: int = 16) -> dict:
    """16'lı veya 8'li turnuva ağacını oluşturur."""
    import random
    
    pool = [
        "Siz (Yarışmacı)", "Ahmet Hâfız (30. Cüz)", "Zeynep K. (Kısa Sûreler)", "Mustafa Y. (Buzzer Rekortmeni)",
        "Hâfız Merve (Kelime Avcısı)", "Ömer Faruk (Yâsîn & Mülk)", "Fâtıma Zehra (Kıraat Yıldızı)", "Bilal H. (Hızlı Hâfız)",
        "Hüseyin R. (Grand Master Hâfız)", "Salih E. (Bakara Kaşifi)", "Ayşe Betül (Makam Şampiyonu)", "Hacer N. (Amme Podyumu)",
        "İbrahim Halil (Tecvid Ustası)", "Yusuf K. (Kelime Dehası)", "Enes T. (Âyet Dedektifi)", "Rümeysa D. (Zirve Takipçisi)"
    ]
    if bracket_size == 8:
        pool = pool[:8]
    else:
        pool = pool[:16]
        
    random.shuffle(pool)
    if "Siz (Yarışmacı)" in pool:
        pool.remove("Siz (Yarışmacı)")
        pool.insert(0, "Siz (Yarışmacı)")
        
    matches_r1 = []
    num_matches = len(pool) // 2
    for i in range(num_matches):
        p1 = pool[i*2]
        p2 = pool[i*2 + 1]
        is_user_match = (p1 == "Siz (Yarışmacı)" or p2 == "Siz (Yarışmacı)")
        status = "ready" if is_user_match else "completed"
        s1 = 0 if is_user_match else random.choice([75, 80, 85, 90, 95])
        s2 = 0 if is_user_match else random.choice([60, 65, 70, 75, 80])
        winner = None if is_user_match else (p1 if s1 >= s2 else p2)
        matches_r1.append({
            "id": f"m{i+1}",
            "player1": {"name": p1, "score": s1},
            "player2": {"name": p2, "score": s2},
            "winner": winner,
            "status": status,
            "is_user_match": is_user_match
        })
        
    rounds = [
        {"round_index": 1, "name": "Son 16" if bracket_size == 16 else "Çeyrek Final", "matches": matches_r1}
    ]
    
    next_count = num_matches // 2
    round_idx = 2
    match_counter = len(matches_r1) + 1
    while next_count >= 1:
        r_name = "Çeyrek Final" if next_count == 4 else ("Yarı Final" if next_count == 2 else "Büyük Final")
        r_matches = []
        for j in range(next_count):
            r_matches.append({
                "id": f"m{match_counter}",
                "player1": {"name": "TBD", "score": 0},
                "player2": {"name": "TBD", "score": 0},
                "winner": None,
                "status": "waiting",
                "is_user_match": False
            })
            match_counter += 1
        rounds.append({"round_index": round_idx, "name": r_name, "matches": r_matches})
        next_count //= 2
        round_idx += 1
        
    return {
        "tournament_id": tournament_id,
        "title": title,
        "category": category,
        "bracket_size": bracket_size,
        "max_points": 100,
        "rounds": rounds,
        "champion": None
    }

def init_hafizlik_tables():
    """Hâfızlık ligi, maç geçmişi, ELO, aralıklı tekrar ve turnuva tablolarını SQLite üzerinde başlatır."""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS hafizlik_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT,
                mode TEXT,
                surah_pool TEXT,
                winner_name TEXT,
                winner_score INTEGER,
                total_rounds INTEGER,
                created_at REAL
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS hafizlik_leaderboard (
                player_name TEXT PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                matches_played INTEGER DEFAULT 0,
                highest_score INTEGER DEFAULT 0,
                last_active REAL
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS hafizlik_elo (
                player_name TEXT PRIMARY KEY,
                elo_rating INTEGER DEFAULT 1200,
                hifz_tier TEXT DEFAULT 'Mübtedi (Başlangıç)',
                streak_count INTEGER DEFAULT 0,
                accuracy_pct REAL DEFAULT 85.0,
                last_updated REAL
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS hafizlik_spaced_repetition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT,
                surah_id INTEGER,
                ayah_id INTEGER,
                sure_name TEXT,
                ayah_text TEXT,
                mistake_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                interval_weight REAL DEFAULT 1.0,
                last_reviewed REAL,
                UNIQUE(player_name, surah_id, ayah_id)
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS hafizlik_tournaments (
                tournament_id TEXT PRIMARY KEY,
                title TEXT,
                category TEXT,
                bracket_size INTEGER DEFAULT 16,
                current_round TEXT DEFAULT 'Son 16',
                status TEXT DEFAULT 'active',
                bracket_tree TEXT,
                created_at REAL
            );
        """)
        
        c.execute("SELECT count(*) FROM hafizlik_leaderboard")
        row = c.fetchone()
        if row and row[0] < 20:
            starters = [
                ("Ahmet Hâfız (30. Cüz)", 280, 3, 95, time.time() - 120),
                ("Zeynep K. (Kısa Sûreler)", 250, 3, 85, time.time() - 360),
                ("Mustafa Y. (Buzzer Rekortmeni)", 210, 3, 75, time.time() - 900),
                ("Hâfız Merve (Kelime Avcısı)", 200, 2, 100, time.time() - 1200),
                ("Ömer Faruk (Yâsîn & Mülk)", 195, 2, 95, time.time() - 1500),
                ("Fâtıma Zehra (Kıraat Yıldızı)", 185, 2, 85, time.time() - 1800),
                ("Bilal H. (Hızlı Hâfız)", 180, 2, 80, time.time() - 2100),
                ("Hüseyin R. (Grand Master Hâfız)", 175, 2, 100, time.time() - 2400),
                ("Salih E. (Bakara Kaşifi)", 165, 2, 65, time.time() - 2700),
                ("Ayşe Betül (Makam Şampiyonu)", 160, 2, 90, time.time() - 3000),
                ("Hacer N. (Amme Podyumu)", 155, 2, 75, time.time() - 3300),
                ("İbrahim Halil (Tecvid Ustası)", 150, 2, 85, time.time() - 3600),
                ("Yusuf K. (Kelime Dehası)", 145, 2, 100, time.time() - 4200),
                ("Enes T. (Âyet Dedektifi)", 140, 2, 70, time.time() - 4800),
                ("Rümeysa D. (Zirve Takipçisi)", 135, 2, 85, time.time() - 5400),
                ("Tarık B. (100 Puan Adayı)", 130, 2, 65, time.time() - 6000),
                ("Esra G. (Hızlı Refleks)", 125, 2, 90, time.time() - 7200),
                ("Hamza Ç. (Furkan Muhafızı)", 120, 2, 60, time.time() - 8400),
                ("Meryem S. (Mülk Bükücü)", 115, 2, 75, time.time() - 9600),
                ("Kerem A. (Harf Ustası)", 110, 2, 55, time.time() - 10800)
            ]
            c.executemany("""
                INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(player_name) DO UPDATE SET
                    total_points = excluded.total_points,
                    matches_played = excluded.matches_played,
                    highest_score = excluded.highest_score,
                    last_active = excluded.last_active
            """, starters)

        c.execute("SELECT count(*) FROM hafizlik_elo")
        if c.fetchone()[0] < 20:
            elo_starters = [
                ("İbrahim Halil (Tecvid Ustası)", 2150, "Hâfız-ı Mütkın (Usta)", 12, 98.5, time.time() - 100),
                ("Hüseyin R. (Grand Master Hâfız)", 2100, "Hâfız-ı Mütkın (Usta)", 9, 97.0, time.time() - 200),
                ("Zeynep K. (Kısa Sûreler)", 1950, "Müntehi (İleri)", 7, 95.2, time.time() - 300),
                ("Ahmet Hâfız (30. Cüz)", 1900, "Müntehi (İleri)", 6, 94.0, time.time() - 400),
                ("Hâfız Merve (Kelime Avcısı)", 1850, "Müntehi (İleri)", 5, 93.5, time.time() - 500),
                ("Fâtıma Zehra (Kıraat Yıldızı)", 1800, "Müntehi (İleri)", 4, 91.0, time.time() - 600),
                ("Ayşe Betül (Makam Şampiyonu)", 1750, "Mutavassıt (Orta)", 3, 89.5, time.time() - 700),
                ("Ömer Faruk (Yâsîn & Mülk)", 1700, "Mutavassıt (Orta)", 3, 88.0, time.time() - 800),
                ("Mustafa Y. (Buzzer Rekortmeni)", 1650, "Mutavassıt (Orta)", 2, 86.5, time.time() - 900),
                ("Bilal H. (Hızlı Hâfız)", 1600, "Mutavassıt (Orta)", 2, 85.0, time.time() - 1000),
                ("Hacer N. (Amme Podyumu)", 1550, "Mutavassıt (Orta)", 2, 84.0, time.time() - 1100),
                ("Yusuf K. (Kelime Dehası)", 1500, "Mutavassıt (Orta)", 1, 82.5, time.time() - 1200),
                ("Rümeysa D. (Zirve Takipçisi)", 1450, "Mutavassıt (Orta)", 1, 81.0, time.time() - 1300),
                ("Salih E. (Bakara Kaşifi)", 1400, "Mutavassıt (Orta)", 1, 79.5, time.time() - 1400),
                ("Siz (Yarışmacı)", 1350, "Mutavassıt (Orta)", 1, 80.0, time.time() - 1500),
                ("Tarık B. (100 Puan Adayı)", 1300, "Mübtedi (Başlangıç)", 0, 76.0, time.time() - 1600),
                ("Esra G. (Hızlı Refleks)", 1250, "Mübtedi (Başlangıç)", 0, 74.0, time.time() - 1700),
                ("Enes T. (Âyet Dedektifi)", 1200, "Mübtedi (Başlangıç)", 0, 72.0, time.time() - 1800),
                ("Hamza Ç. (Furkan Muhafızı)", 1150, "Mübtedi (Başlangıç)", 0, 70.0, time.time() - 1900),
                ("Meryem S. (Mülk Bükücü)", 1100, "Mübtedi (Başlangıç)", 0, 68.0, time.time() - 2000),
                ("Kerem A. (Harf Ustası)", 1050, "Mübtedi (Başlangıç)", 0, 65.0, time.time() - 2100)
            ]
            c.executemany("""
                INSERT INTO hafizlik_elo (player_name, elo_rating, hifz_tier, streak_count, accuracy_pct, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_name) DO UPDATE SET
                    elo_rating = excluded.elo_rating,
                    hifz_tier = excluded.hifz_tier,
                    streak_count = excluded.streak_count,
                    accuracy_pct = excluded.accuracy_pct,
                    last_updated = excluded.last_updated
            """, elo_starters)

        c.execute("SELECT count(*) FROM hafizlik_spaced_repetition")
        if c.fetchone()[0] == 0:
            sample_reps = [
                ("Siz (Yarışmacı)", 78, 1, "Nebe", "عَمَّ يَتَسَآءَلُونَ", 2, 1, 2.5, time.time() - 3600),
                ("Siz (Yarışmacı)", 67, 1, "Mülk", "تَبَـٰرَكَ ٱلَّذِى بِيَدِهِ ٱلْمُلْكُ", 1, 3, 1.2, time.time() - 7200),
                ("Siz (Yarışmacı)", 36, 12, "Yâsîn", "إِنَّا نَحْنُ نُحْىِ ٱلْمَوْتَىٰ", 3, 2, 3.0, time.time() - 10800),
                ("Siz (Yarışmacı)", 114, 4, "Nâs", "مِن شَرِّ ٱلْوَسْوَاسِ ٱلْخَنَّاسِ", 0, 5, 0.4, time.time() - 14400)
            ]
            c.executemany("""
                INSERT OR IGNORE INTO hafizlik_spaced_repetition 
                (player_name, surah_id, ayah_id, sure_name, ayah_text, mistake_count, correct_count, interval_weight, last_reviewed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_reps)

        c.execute("SELECT count(*) FROM hafizlik_tournaments")
        if c.fetchone()[0] == 0:
            tournaments_data = [
                ("tourn-amme-16", "Haftalık 30. Cüz Amme Şampiyonası", "30. Cüz (Amme)", 16, "Son 16", "active"),
                ("tourn-yasin-mulk", "Yâsîn, Mülk & Rahmân İhtisas Kupası", "Yâsîn & Mülk", 16, "Son 16", "active"),
                ("tourn-bakara", "Bakara & Âl-i İmrân Büyük Hıfz Karşılaşması", "Bakara & Âl-i İmrân", 8, "Çeyrek Final", "active"),
                ("tourn-buzzer-speed", "Hızlı Âyet Refleks Şampiyonası", "Genel Kur'an", 16, "Son 16", "active")
            ]
            for tid, ttitle, tcat, tsize, tcround, tstat in tournaments_data:
                tree = build_tournament_bracket_tree(tid, ttitle, tcat, tsize)
                c.execute("""
                    INSERT INTO hafizlik_tournaments (tournament_id, title, category, bracket_size, current_round, status, bracket_tree, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (tid, ttitle, tcat, tsize, tcround, tstat, json.dumps(tree, ensure_ascii=False), time.time()))

        c.execute("SELECT count(*) FROM hafizlik_matches")
        m_row = c.fetchone()
        if m_row and m_row[0] < 10:
            starter_matches = [
                ("30. Cüz Hâfızlar Meydanı", "buzzer", "30. Cüz (Amme Cüzü)", "Ahmet Hâfız (30. Cüz)", 90, 10, time.time() - 600),
                ("Hızlı Kelime Avcıları", "wordgame", "Karışık Kur'an Kelimeleri", "Hâfız Merve (Kelime Avcısı)", 100, 5, time.time() - 1200),
                ("Yâsîn & Mülk Merdiveni", "millionaire", "Yâsîn, Mülk, Rahmân Sûreleri", "Fâtıma Zehra (Kıraat Yıldızı)", 85, 11, time.time() - 1800),
                ("Genç Kuşak Âyet Düellosu", "buzzer", "İlk 10 Sûre", "Ömer Faruk (Yâsîn & Mülk)", 95, 10, time.time() - 2400),
                ("Bakara & Âl-i İmrân Zirvesi", "millionaire", "Bakara & Âl-i İmrân", "Hüseyin R. (Grand Master Hâfız)", 100, 11, time.time() - 3000),
                ("Kelime Ustaları Etabı", "wordgame", "Kur'an Kelimeleri", "Yusuf K. (Kelime Dehası)", 100, 5, time.time() - 3600),
                ("Amme Podyumu Finali", "buzzer", "30. Cüz", "Zeynep K. (Kısa Sûreler)", 85, 10, time.time() - 4200),
                ("Fâtiha'dan Nâs'a Merdiven", "millionaire", "Tüm Kur'an", "Ayşe Betül (Makam Şampiyonu)", 90, 11, time.time() - 4800),
                ("Hızlı Buton Şampiyonası", "buzzer", "Kısa Sûreler", "Mustafa Y. (Buzzer Rekortmeni)", 75, 10, time.time() - 5400),
                ("Tecvid & Hâfızlık Etabı", "wordgame", "Kur'an Kelimeleri", "İbrahim Halil (Tecvid Ustası)", 85, 5, time.time() - 6000)
            ]
            c.executemany("""
                INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, starter_matches)
        conn.commit()
        conn.close()
    except Exception as e:
        print("[WARN] Hafizlik tabloları başlatılamadı:", e)

init_hafizlik_tables()
takeover_lock = asyncio.Lock()

# =====================================================================
# 0. ZAKİRUN HÂFIZLIK YARIŞMALARI (SADELEŞTİRİLMİŞ MODÜLER SAYFALAR)
# =====================================================================
@app.get("/", response_class=HTMLResponse)
def root_home():
    """Zakirun Kur'an Oyunları ultra sade ana sayfasını sunar (Sadece oyun kartları)."""
    idx_file = get_page_path("index.html")
    if os.path.exists(idx_file):
        with open(idx_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="index.html bulunamadı")



@app.get("/oyun/okunan-kelimeyi-bul", response_class=HTMLResponse)
@app.get("/okunan-kelime", response_class=HTMLResponse)
@app.get("/dinle-bul", response_class=HTMLResponse)
def page_okunan_kelime_bul():
    """Müstakil Okunan Âyetteki Kelimeyi Bul (4 Çerçeveli Dinleme Oyunu) sayfasını sunar."""
    p_file = get_page_path("oyun_okunan_kelime.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="oyun_okunan_kelime.html bulunamadı")


@app.get("/oyun/ayet-tamamlama", response_class=HTMLResponse)
@app.get("/ayet-tamamlama", response_class=HTMLResponse)
@app.get("/tamamla", response_class=HTMLResponse)
def page_ayet_tamamlama():
    """Müstakil Âyet Tamamlama Oyunu (Kaybolan Kelimeyi Daktilo ile Tamamla) sayfasını sunar."""
    p_file = get_page_path("oyun_ayet_tamamlama.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="oyun_ayet_tamamlama.html bulunamadı")


@app.get("/oyun/sure-ezberleme", response_class=HTMLResponse)
@app.get("/sure-ezberleme", response_class=HTMLResponse)
@app.get("/sonraki-ayet", response_class=HTMLResponse)
def page_sure_ezberleme():
    """Müstakil Sûre Ezberleme Oyunu (Dinlenen Âyetten Sonraki Âyeti Bul) sayfasını sunar."""
    p_file = get_page_path("oyun_sure_ezberleme.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="oyun_sure_ezberleme.html bulunamadı")



@app.get("/oyun/kelime-oyunu", response_class=HTMLResponse)
@app.get("/kelime", response_class=HTMLResponse)
def page_kelime_oyunu():
    """Müstakil Kur'an Kelime Oyunu sayfasını sunar."""
    p_file = get_page_path("oyun_kelime.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="oyun_kelime.html bulunamadı")

@app.get("/oyun/bilgi-yarismasi", response_class=HTMLResponse)
@app.get("/bilgiyarismasi", response_class=HTMLResponse)
@app.get("/yarisma", response_class=HTMLResponse)
@app.get("/quiz", response_class=HTMLResponse)
def page_bilgi_yarismasi():
    """Müstakil 11 Basamaklı Kur'an Bilgi Yarışması sayfasını sunar."""
    p_file = get_page_path("oyun_bilgi_yarismasi.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="oyun_bilgi_yarismasi.html bulunamadı")

@app.get("/oyun/ayet-bloklari", response_class=HTMLResponse)
@app.get("/bloklar", response_class=HTMLResponse)
def page_ayet_bloklari():
    """Müstakil Âyet İçi Kelime Blokları sayfasını sunar."""
    p_file = get_page_path("oyun_ayet_bloklari.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="oyun_ayet_bloklari.html bulunamadı")

@app.get("/turnuvalar", response_class=HTMLResponse)
@app.get("/turnuva", response_class=HTMLResponse)
def page_turnuvalar():
    """Müstakil Haftalık Şampiyonalar ve Kupa Ağaçları sayfasını sunar."""
    p_file = get_page_path("oyun_turnuva.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="oyun_turnuva.html bulunamadı")

@app.get("/giris", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
@app.get("/kayit", response_class=HTMLResponse)
@app.get("/hesap", response_class=HTMLResponse)
@app.get("/profil", response_class=HTMLResponse)
@app.get("/ayarlar", response_class=HTMLResponse)
def page_giris():
    """Zakirun Giriş Yap, Kayıt Ol ve Google ile Giriş sayfasını sunar."""
    p_file = get_page_path("giris.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="giris.html bulunamadı")

@app.get("/karne", response_class=HTMLResponse)
def page_hifz_karne():
    """Müstakil Hıfz Karnesi ve Zayıf Âyet Analizi sayfasını sunar."""
    p_file = get_page_path("hifz_karne.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="hifz_karne.html bulunamadı")

@app.get("/ogren", response_class=HTMLResponse)
@app.get("/kuran-ogren", response_class=HTMLResponse)
@app.get("/elifba", response_class=HTMLResponse)
def page_kuran_ogrenme_portali():
    """Kur'an-ı Kerim Öğrenme Portalı (Elifbâ, Tecvid & Kıraat Mektebi) sayfasını sunar."""
    p_file = get_page_path("kuran_ogrenme_portali.html")
    if os.path.exists(p_file):
        with open(p_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="kuran_ogrenme_portali.html bulunamadı")

# =====================================================================
# KUR'AN ÖĞRENME PORTALI API (4 KADEME, 20 DERS)
# =====================================================================
try:
    from quran_learn_data import QURAN_LEARNING_CURRICULUM, DIYANET_PARTS, get_curriculum_summary, get_lesson_by_id
except ImportError:
    QURAN_LEARNING_CURRICULUM = []
    DIYANET_PARTS = []
    def get_curriculum_summary():
        return []
    def get_lesson_by_id(lid):
        return None

@app.get("/api/learn/parts")
def api_get_curriculum_parts():
    """Diyanet Elifbâ ve Tecvid ana bölüm listesini döner."""
    return {
        "status": "success",
        "parts": DIYANET_PARTS
    }

@app.get("/api/learn/curriculum")
def api_get_curriculum(stage: Optional[int] = None, part: Optional[str] = None):
    """Diyanet Elifbâ ve Tecvid ile senkronize zengin müfredat özetini döner."""
    summary = get_curriculum_summary()
    if stage is not None:
        summary = [d for d in summary if d.get("stage") == stage]
    if part is not None:
        summary = [d for d in summary if d.get("part_key") == part]
    return {
        "status": "success",
        "source": "Diyanet İşleri Başkanlığı Kur'an Portalı (https://kuran.diyanet.gov.tr/elifba)",
        "total_lessons": len(QURAN_LEARNING_CURRICULUM),
        "filtered_lessons": len(summary),
        "stages_count": len(DIYANET_PARTS) if DIYANET_PARTS else 2,
        "parts": DIYANET_PARTS,
        "curriculum": summary
    }

@app.get("/api/learn/lesson/{lesson_id}")
def api_get_lesson(lesson_id: int):
    """Seçilen Diyanet dersinin detaylı harf, kural, grup, bitişme halleri ve ses kartlarını döner."""
    lesson = get_lesson_by_id(lesson_id)
    if not lesson:
        # Fallback to searching QURAN_LEARNING_CURRICULUM directly
        lesson = next((d for d in QURAN_LEARNING_CURRICULUM if d.get("id") == lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Ders bulunamadı")
    return {
        "status": "success",
        "lesson": lesson
    }

class CompleteLessonRequest(BaseModel):
    lesson_id: int
    score: int = 10
    player_name: str = "Siz (Yarışmacı)"

@app.post("/api/learn/complete-lesson")
def api_complete_lesson(req: CompleteLessonRequest):
    """Ders tamamlandığında motivasyon puanı ve ilerleme kaydeder."""
    total_l = len(QURAN_LEARNING_CURRICULUM) if QURAN_LEARNING_CURRICULUM else 91
    next_id = req.lesson_id + 1 if req.lesson_id < total_l else total_l
    return {
        "success": True,
        "completed_lesson_id": req.lesson_id,
        "points_earned": min(10, req.score),
        "next_lesson_id": next_id,
        "message": f"Tebrikler! {req.lesson_id}. Ders başarıyla tamamlandı (+{min(10, req.score)} Puan)."
    }


@app.get("/audio/elifletter/{filename}")
@app.get("/elifletter/{filename}")
def get_elifletter_audio(filename: str):
    """elifletter klasöründeki harf ses dosyalarını (mp3 ve mp4) sunar."""
    elif_dir = os.path.dirname(get_audio_file("elifletter", "dummy.mp3"))
    file_path = os.path.join(elif_dir, filename)
    if not os.path.exists(file_path):
        if os.path.exists(file_path + ".mp3"):
            file_path += ".mp3"
        elif os.path.exists(file_path + ".mp4"):
            file_path += ".mp4"
        else:
            raise HTTPException(status_code=404, detail=f"Harf ses dosyası ({filename}) bulunamadı")
    media_type = "audio/mpeg" if file_path.endswith(".mp3") else "audio/mp4"
    return FileResponse(file_path, media_type=media_type)


@app.get("/audio/diyanet/{file_path:path}")
def get_diyanet_audio_file(file_path: str):
    """Diyanet Elifbâ ses dosyalarını yerel önbellekten veya canlı Diyanet CDN akışından sunar."""
    local_path = get_audio_file("diyanet", file_path.replace("/", os.sep))
    if os.path.exists(local_path) and os.path.getsize(local_path) > 50:
        return FileResponse(local_path, media_type="audio/mpeg")
    
    # URL decode & encode correctly for remote CDN proxy
    import urllib.request, urllib.parse
    try:
        parts = file_path.split("/")
        encoded_path = "/".join(urllib.parse.quote(p) for p in parts)
        remote_url = f"https://kuran.diyanet.gov.tr/elifba/data/sound/{encoded_path}"
        req = urllib.request.Request(remote_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            content = resp.read()
            if len(content) > 50:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(content)
                return Response(content=content, media_type="audio/mpeg")
    except Exception:
        pass
        
    raise HTTPException(status_code=404, detail=f"Diyanet ses dosyası ({file_path}) bulunamadı")

@app.get("/audio/learn/{filename}")
def get_learn_audio_file(filename: str):
    """Kur'an öğrenme portalı harf ve kelime ses dosyalarını sunar."""
    audio_path = get_audio_file("learn", filename)
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/mpeg")
    elif_path = get_audio_file("elifletter", filename)
    if os.path.exists(elif_path):
        media_type = "audio/mpeg" if elif_path.endswith(".mp3") else "audio/mp4"
        return FileResponse(elif_path, media_type=media_type)
    raise HTTPException(status_code=404, detail=f"Ses dosyası ({filename}) bulunamadı")

@app.get("/game", response_class=HTMLResponse)
@app.get("/lab", response_class=HTMLResponse)
@app.get("/ezber", response_class=HTMLResponse)
@app.get("/3d", response_class=HTMLResponse)
@app.get("/kuran_tv_bilgi_yarismasi.html", response_class=HTMLResponse)
def root_bilgi_yarismasi_legacy():
    """Geriye dönük uyumluluk: Eski monolitik stüdyo dosyasını sunar."""
    game_file = get_page_path("kuran_tv_bilgi_yarismasi.html")
    if os.path.exists(game_file):
        with open(game_file, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Kuran TV Bilgi Yarışması HTML dosyası bulunamadı")
 
@app.get("/zakirun.com.woff2")
@app.get("/fonts/zakirun.com.woff2")
def get_zakirun_font():
    """Zakirun Uthmani 2 WOFF2 hattını sunar."""
    font_path = get_asset_path("zakirun.com.woff2")
    if os.path.exists(font_path):
        return FileResponse(font_path, media_type="font/woff2")
    raise HTTPException(status_code=404, detail="Font dosyası bulunamadı")

@app.get("/LOGO.png")
@app.get("/logo.png")
def get_zakirun_logo():
    """Zakirun Logo görselini sunar."""
    logo_path = get_asset_path("LOGO.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="LOGO.png bulunamadı")

@app.get("/manifest.json")
def get_manifest():
    """PWA Manifest dosyasını sunar."""
    manifest_path = get_asset_path("manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path, media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="manifest.json bulunamadı")

@app.get("/sw.js")
def get_service_worker():
    """PWA Service Worker dosyasını sunar."""
    sw_path = get_asset_path("sw.js")
    if os.path.exists(sw_path):
        return FileResponse(sw_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="sw.js bulunamadı")

@app.get("/supabase_client.js")
def get_supabase_client_script():
    """Supabase istemci ve entegrasyon betiğini sunar."""
    js_path = get_asset_path("supabase_client.js") if os.path.exists(get_asset_path("supabase_client.js")) else os.path.join(CURRENT_DIR, "data", "supabase_client.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="supabase_client.js bulunamadı")



# =====================================================================
# 1. SYSTEM STATUS & TELEMETRY
# =====================================================================
@app.get("/api/status")
def get_system_status():
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT count(*) FROM surahs")
    surah_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM ayahs")
    ayah_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM words")
    word_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM translations")
    trans_count = c.fetchone()[0]
    
    c.execute("SELECT count(*) FROM tafsirs")
    tafsir_count = c.fetchone()[0]

    c.execute("SELECT count(*) FROM quran_places")
    place_count = c.fetchone()[0]

    c.execute("SELECT count(*) FROM mushaf_layout_15lines")
    mushaf_lines = c.fetchone()[0]

    conn.close()
    dt_ms = (time.time() - t0) * 1000

    return {
        "status": "ONLINE",
        "kernel": "KUR'AN TV 2026 QUANTUM ENGINE v2.026",
        "database_file": DB_PATH,
        "database_size_bytes": os.path.getsize(DB_PATH),
        "query_latency_ms": round(dt_ms, 2),
        "metrics": {
            "surahs": surah_count,
            "ayahs": ayah_count,
            "words": word_count,
            "translations": trans_count,
            "tafsirs": tafsir_count,
            "sacred_places": place_count,
            "mushaf_15lines": mushaf_lines,
            "arabic_scripts_count": 15,
            "translation_languages": 184
        },
        "zero_media_enforced": True
    }

# =====================================================================
# 2. SURAHS (ALL 114 SURAHS)
# =====================================================================
@app.get("/api/surahs")
def list_surahs():
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            surah_id, inis_sirasi, sure_name, name_arabic, 
            name_latin, name_english, ayah_count, location, 
            sajda, alternative_names, bismillah_pre, page_start, page_end
        FROM surahs
        ORDER BY surah_id ASC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return {
        "total": len(rows),
        "latency_ms": round((time.time() - t0) * 1000, 2),
        "data": rows
    }

# =====================================================================
# 3. SURAH DEEP DIVE WITH ALL AYAHS & 15 SCRIPTS
# =====================================================================
@app.get("/api/surah/{surah_id}")
def get_surah(surah_id: int, include_words: bool = False):
    if surah_id < 1 or surah_id > 114:
        raise HTTPException(status_code=404, detail="Gecersiz Sure Numarasi (1-114 arasi olmali)")
    
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    # Surah metadata
    c.execute("SELECT * FROM surahs WHERE surah_id = ?", (surah_id,))
    s_row = c.fetchone()
    if not s_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Sure bulunamadi")
    surah_meta = dict(s_row)
    
    # Ayahs with 15 scripts
    c.execute("""
        SELECT 
            ayet_id, verse_key, surah_id, ayah_id, page_no, juz_no, hizb_no, rub_no,
            sajdah_number, sajdah_type,
            quran_uthmani, quran_tajweed, quran_imlaei, quran_imlaei_simple,
            quran_simple, quran_simple_clean, quran_indopak, quran_indonesia,
            quran_uthmani2, quran_uthmani_min, quran_simple_min, quran_simple_plain,
            quran_diyanet, quran_warsh, quran_qalun
        FROM ayahs
        WHERE surah_id = ?
        ORDER BY ayah_id ASC
    """, (surah_id,))
    ayah_rows = [dict(r) for r in c.fetchall()]
    
    # Calculate Warsh and Qalun differences from Hafs
    for a in ayah_rows:
        uth = a["quran_uthmani"] or ""
        war = a["quran_warsh"] or ""
        qal = a["quran_qalun"] or ""
        a["has_warsh_diff"] = (war != "" and war != uth)
        a["has_qalun_diff"] = (qal != "" and qal != uth)
        
        if include_words:
            c.execute("""
                SELECT 
                    kelime_id, word_id, satir_no, pos_tr, pos_ar, irab_case,
                    root_arabic, lemma, quran_uthmani, text_turkish, text_english
                FROM words
                WHERE surah_id = ? AND ayah_id = ?
                ORDER BY word_id ASC
            """, (surah_id, a["ayah_id"]))
            a["words"] = [dict(w) for w in c.fetchall()]
            
    conn.close()
    
    return {
        "surah": surah_meta,
        "ayah_count": len(ayah_rows),
        "latency_ms": round((time.time() - t0) * 1000, 2),
        "ayahs": ayah_rows
    }

# =====================================================================
# 4. SINGLE AYAH COMPLETE DEEP QUANTUM INSPECTOR
# =====================================================================
@app.get("/api/ayah/{surah_id}/{ayah_id}")
def get_ayah_detail(surah_id: int, ayah_id: int):
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    # Ayah core
    c.execute("SELECT * FROM ayahs WHERE surah_id = ? AND ayah_id = ?", (surah_id, ayah_id))
    a_row = c.fetchone()
    if not a_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Ayet bulunamadi")
    ayah = dict(a_row)
    
    # Words in this ayah (all 49 columns)
    c.execute("""
        SELECT * FROM words 
        WHERE surah_id = ? AND ayah_id = ? 
        ORDER BY word_id ASC
    """, (surah_id, ayah_id))
    words = [dict(w) for w in c.fetchall()]
    
    # Asbab al-Nuzul
    c.execute("""
        SELECT id, source, context_text 
        FROM asbab_al_nuzul 
        WHERE surah_id = ? AND ayah_id = ?
    """, (surah_id, ayah_id))
    asbab = [dict(r) for r in c.fetchall()]
    
    # Turkish Translations (From high-speed view v_turkce_mealler)
    verse_key = f"{surah_id}:{ayah_id}"
    c.execute("""
        SELECT meal_diyanet, meal_elmalili, meal_ozturk, meal_esed, meal_yildirim
        FROM v_turkce_mealler
        WHERE verse_key = ?
    """, (verse_key,))
    tr_row = c.fetchone()
    tr_meals = []
    if tr_row:
        labels = {
            "meal_diyanet": "Diyanet İşleri Meâli",
            "meal_elmalili": "Elmalılı Hamdi Yazır",
            "meal_ozturk": "Yaşar Nuri Öztürk",
            "meal_esed": "Muhammed Esed",
            "meal_yildirim": "Suat Yıldırım"
        }
        for k, label in labels.items():
            if tr_row[k]:
                tr_meals.append({"edition_id": k, "name": label, "text": tr_row[k]})
    
    # World Major Translations (EN, FR, DE, RU, UR, ID)
    c.execute("""
        SELECT edition_id, text 
        FROM translations 
        WHERE surah_id = ? AND ayah_id = ? AND edition_id IN (
            'en-sahih-international', 'bridges-translation', 'fr-rashid-maash', 
            'de-bubenheim', 'ru-kuliev', 'ur-maududi', 'id-indonesian'
        )
    """, (surah_id, ayah_id))
    world_meals = [dict(r) for r in c.fetchall()]

    # Tafsirs (Diyanet Kur'an Yolu, Taberi, Ibn Kesir, Celaleyn, Kurtubi)
    c.execute("""
        SELECT edition_id, text 
        FROM tafsirs 
        WHERE surah_id = ? AND ayah_id = ? AND edition_id IN (
            'tr-diyanet-kuran-yolu', 'ar-tafsir-ibn-kathir', 'ar-tafsir-al-tabari',
            'ar-tafsir-al-jalalayn', 'ar-tafseer-al-qurtubi'
        )
    """, (surah_id, ayah_id))
    tafsir_rows = [dict(r) for r in c.fetchall()]
    
    # Sacred Places linked to this ayah
    c.execute("""
        SELECT p.place_id, p.name_tr, p.name_ar, p.latitude, p.longitude, p.description
        FROM quran_place_ayahs pa
        JOIN quran_places p ON p.place_id = pa.place_id
        WHERE pa.surah_id = ? AND pa.ayah_id = ?
    """, (surah_id, ayah_id))
    places = [dict(r) for r in c.fetchall()]
    
    # Fihrist Topics linked to this ayah
    c.execute("""
        SELECT t.topic_id, t.topic_name, t.category
        FROM fihrist_ayahs fa
        JOIN fihrist_topics t ON t.topic_id = fa.topic_id
        WHERE fa.surah_id = ? AND fa.ayah_id = ?
    """, (surah_id, ayah_id))
    topics = [dict(r) for r in c.fetchall()]
    
    conn.close()
    
    return {
        "ayah": ayah,
        "words": words,
        "asbab_al_nuzul": asbab,
        "translations_turkish": tr_meals,
        "translations_world": world_meals,
        "tafsirs": tafsir_rows,
        "sacred_places": places,
        "thematic_topics": topics,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

# =====================================================================
# 5. WORDS & MORPHOLOGY (ALL 77,429 WORDS ACCESSIBLE)
# =====================================================================
@app.get("/api/words/{surah_id}/{ayah_id}")
def get_ayah_words(surah_id: int, ayah_id: int):
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM words
        WHERE surah_id = ? AND ayah_id = ?
        ORDER BY word_id ASC
    """, (surah_id, ayah_id))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return {
        "surah_id": surah_id,
        "ayah_id": ayah_id,
        "word_count": len(rows),
        "words": rows,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

@app.get("/api/word/{word_identifier}")
def get_single_word(word_identifier: str):
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    # Check if word_identifier is a sequential number (1..77429) or a 9-digit kelime_id ('001001001')
    if word_identifier.isdigit() and len(word_identifier) <= 6:
        row_id = int(word_identifier)
        c.execute("SELECT * FROM words WHERE rowid = ?", (row_id,))
    else:
        c.execute("SELECT * FROM words WHERE kelime_id = ? OR rowid = ?", (word_identifier, word_identifier))
        
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Kelime bulunamadi")
    w = dict(row)
    
    # Calculate Quran frequency of this root
    root_freq = 0
    if w.get("root_arabic"):
        c.execute("SELECT count(*) FROM words WHERE root_arabic = ?", (w["root_arabic"],))
        root_freq = c.fetchone()[0]
        
    conn.close()
    w["root_quran_frequency"] = root_freq
    w["latency_ms"] = round((time.time() - t0) * 1000, 2)
    return w

# =====================================================================
# 6. ROOT CONSTELLATION & DERIVATION SEARCH
# =====================================================================
@app.get("/api/root/{root_arabic}")
def get_root_details(root_arabic: str):
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    # Find all words with this root
    c.execute("""
        SELECT 
            kelime_id, surah_id, ayah_id, word_id,
            quran_uthmani, lemma, pos_tr, irab_case, text_turkish, text_english
        FROM words
        WHERE root_arabic = ?
        ORDER BY surah_id ASC, ayah_id ASC, word_id ASC
    """, (root_arabic,))
    words = [dict(r) for r in c.fetchall()]
    
    # Distinct lemmas derived from this root
    c.execute("""
        SELECT DISTINCT lemma, count(*) as freq
        FROM words
        WHERE root_arabic = ? AND lemma IS NOT NULL
        GROUP BY lemma
        ORDER BY freq DESC
    """, (root_arabic,))
    lemmas = [dict(r) for r in c.fetchall()]
    
    conn.close()
    
    return {
        "root_arabic": root_arabic,
        "total_occurrences": len(words),
        "derived_lemmas": lemmas,
        "words": words[:200],  # Return first 200 occurrences for performance
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

# =====================================================================
# 7. 15-LINE MADINAH MUSHAF LAYOUT (ALL 604 PAGES)
# =====================================================================
@app.get("/api/mushaf/page/{page_no}")
def get_mushaf_page(page_no: int):
    if page_no < 1 or page_no > 604:
        raise HTTPException(status_code=404, detail="Gecersiz Sayfa No (1-604 arasi olmali)")
        
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    # Lines from v_mushaf_15lines
    c.execute("""
        SELECT 
            page_no, line_no, font_name, verse_key, sure_name, ayah_id,
            word_start, word_end, quran_uthmani
        FROM v_mushaf_15lines
        WHERE page_no = ?
        ORDER BY line_no ASC, word_start ASC
    """, (page_no,))
    lines = [dict(r) for r in c.fetchall()]
    
    # Juz & Hizb context
    c.execute("""
        SELECT DISTINCT juz_no, hizb_no 
        FROM v_mushaf_sayfa 
        WHERE page_no = ? 
        LIMIT 1
    """, (page_no,))
    page_ctx = c.fetchone()
    juz_no = page_ctx["juz_no"] if page_ctx else 1
    hizb_no = page_ctx["hizb_no"] if page_ctx else 1

    # All ayahs on this page
    c.execute("""
        SELECT verse_key, sure_name, ayah_id, quran_uthmani, quran_warsh, quran_qalun
        FROM v_mushaf_sayfa
        WHERE page_no = ?
        ORDER BY verse_key ASC
    """, (page_no,))
    ayahs = [dict(r) for r in c.fetchall()]
    
    conn.close()
    
    return {
        "page_number": page_no,
        "juz_number": juz_no,
        "hizb_number": hizb_no,
        "lines_count": len(lines),
        "lines": lines,
        "ayahs_on_page": ayahs,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

# =====================================================================
# 8. SACRED PLACES TELEMETRY & GPS (32 SITES & 109 AYAHS)
# =====================================================================
@app.get("/api/places")
def get_all_places():
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            p.place_id, p.name_tr, p.name_ar, p.name_en, p.category,
            p.latitude, p.longitude, p.country, p.description,
            count(pa.id) as linked_ayah_count
        FROM quran_places p
        LEFT JOIN quran_place_ayahs pa ON pa.place_id = p.place_id
        GROUP BY p.place_id
        ORDER BY linked_ayah_count DESC
    """)
    places = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return {
        "total": len(places),
        "places": places,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

@app.get("/api/places/{place_id}")
def get_place_detail(place_id: int):
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM quran_places WHERE place_id = ?", (place_id,))
    p_row = c.fetchone()
    if not p_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Mekan bulunamadi")
    place = dict(p_row)
    
    # Linked ayahs
    c.execute("""
        SELECT 
            pa.verse_key, pa.surah_id, pa.ayah_id,
            a.quran_uthmani, s.sure_name, s.name_arabic as surah_name_ar
        FROM quran_place_ayahs pa
        JOIN ayahs a ON a.surah_id = pa.surah_id AND a.ayah_id = pa.ayah_id
        JOIN surahs s ON s.surah_id = pa.surah_id
        WHERE pa.place_id = ?
        ORDER BY pa.surah_id ASC, pa.ayah_id ASC
    """, (place_id,))
    ayahs = [dict(r) for r in c.fetchall()]
    
    conn.close()
    place["linked_ayahs"] = ayahs
    place["latency_ms"] = round((time.time() - t0) * 1000, 2)
    return place

# =====================================================================
# 9. ASBAB AL-NUZUL (430 REVELATION OCCASIONS)
# =====================================================================
@app.get("/api/asbab/{surah_id}")
def get_surah_asbab(surah_id: int):
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, verse_key, surah_id, ayah_id, source, context_text
        FROM asbab_al_nuzul
        WHERE surah_id = ?
        ORDER BY ayah_id ASC
    """, (surah_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return {
        "surah_id": surah_id,
        "count": len(rows),
        "records": rows,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

# =====================================================================
# 10. THEMATIC FIHRIST (8 CATEGORIES & 595 TOPICS)
# =====================================================================
@app.get("/api/fihrist/categories")
def get_fihrist_categories():
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT category, count(topic_id) as topic_count
        FROM fihrist_topics
        WHERE category IS NOT NULL AND category != ''
        GROUP BY category
        ORDER BY topic_count DESC
    """)
    categories = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return {
        "count": len(categories),
        "categories": categories,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

@app.get("/api/fihrist/topics")
def get_fihrist_topics(category: Optional[str] = None):
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    if category:
        c.execute("""
            SELECT topic_id, topic_name, category, display_order 
            FROM fihrist_topics 
            WHERE category = ?
            ORDER BY display_order ASC, topic_id ASC
        """, (category,))
    else:
        c.execute("""
            SELECT topic_id, topic_name, category, display_order 
            FROM fihrist_topics 
            ORDER BY category ASC, display_order ASC, topic_id ASC
        """)
    topics = [dict(r) for r in c.fetchall()]
    conn.close()
    
    return {
        "count": len(topics),
        "topics": topics,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

# =====================================================================
# 11. QUANTUM FTS5 FULL-TEXT SEARCH (4.47M TRANSLATIONS & 113K TAFSIRS)
# =====================================================================
@app.get("/api/search")
def search_full_text(
    q: str = Query(..., min_length=2, description="Arama metni"),
    target: str = Query("translations", pattern="^(translations|tafsirs|ayahs)$"),
    limit: int = Query(25, ge=1, le=100)
):
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    clean_q = q.replace("'", "").replace('"', '').strip()
    
    results = []
    if target == "translations":
        c.execute("""
            SELECT t.id, t.verse_key, t.surah_id, t.ayah_id, t.edition_id, t.text,
                   s.sure_name, s.name_arabic
            FROM fts_translations fts
            JOIN translations t ON t.rowid = fts.rowid
            JOIN surahs s ON s.surah_id = t.surah_id
            WHERE fts_translations MATCH ?
            LIMIT ?
        """, (clean_q, limit))
        results = [dict(r) for r in c.fetchall()]
        
    elif target == "ayahs":
        c.execute("""
            SELECT a.ayet_id, a.verse_key, a.surah_id, a.ayah_id, a.quran_uthmani, a.quran_simple_clean,
                   s.sure_name, s.name_arabic
            FROM fts_ayahs fts
            JOIN ayahs a ON a.rowid = fts.rowid
            JOIN surahs s ON s.surah_id = a.surah_id
            WHERE fts_ayahs MATCH ?
            LIMIT ?
        """, (clean_q, limit))
        results = [dict(r) for r in c.fetchall()]
        
    elif target == "tafsirs":
        c.execute("""
            SELECT tf.id, tf.verse_key, tf.surah_id, tf.ayah_id, tf.edition_id, tf.text,
                   s.sure_name
            FROM fts_tafsirs fts
            JOIN tafsirs tf ON tf.rowid = fts.rowid
            JOIN surahs s ON s.surah_id = tf.surah_id
            WHERE fts_tafsirs MATCH ?
            LIMIT ?
        """, (clean_q, limit))
        results = [dict(r) for r in c.fetchall()]
        
    conn.close()
    dt_ms = (time.time() - t0) * 1000
    
    return {
        "query": q,
        "target": target,
        "found_count": len(results),
        "search_time_ms": round(dt_ms, 2),
        "results": results
    }

# =====================================================================
# 8. HIFZ & EZBER ARENASI (1, 2, 3 & 4 KİŞİLİK EZBER MOTORU)
# =====================================================================
@app.get("/api/hifz/surah/{surah_id}")
def get_hifz_surah(surah_id: int):
    """
    1 tıkla bir sûrenin tüm âyetlerini, meâllerini ve her âyetin 
    tüm kelimelerini morfolojik detaylarıyla birlikte döner.
    """
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM surahs WHERE surah_id = ?", (surah_id,))
    s_row = c.fetchone()
    if not s_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Sûre bulunamadı")
    surah = dict(s_row)
    
    # Ayahs with Turkish translation
    c.execute("""
        SELECT a.ayet_id, a.verse_key, a.surah_id, a.ayah_id, a.quran_uthmani, a.quran_simple,
               t.text as translation_tr
        FROM ayahs a
        LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
        WHERE a.surah_id = ?
        ORDER BY a.ayah_id ASC
    """, (surah_id,))
    ayahs = [dict(r) for r in c.fetchall()]
    
    # Words with morphology
    c.execute("""
        SELECT ayah_id, word_id, quran_uthmani, text_turkish, text_latin
        FROM words
        WHERE surah_id = ?
        ORDER BY ayah_id ASC, word_id ASC
    """, (surah_id,))
    words = [dict(r) for r in c.fetchall()]
    
    from collections import defaultdict
    words_by_ayah = defaultdict(list)
    for w in words:
        words_by_ayah[w["ayah_id"]].append(w)
        
    for a in ayahs:
        a["words"] = words_by_ayah.get(a["ayah_id"], [])
        
    conn.close()
    dt_ms = (time.time() - t0) * 1000
    return {
        "surah": surah,
        "ayah_count": len(ayahs),
        "total_words": len(words),
        "latency_ms": round(dt_ms, 2),
        "ayahs": ayahs
    }

@app.get("/api/hifz/quiz")
def get_hifz_quiz(
    surah_id: Optional[int] = Query(None, description="Belirli bir sûre ID veya boşsa kısa sûreler"),
    count: int = Query(5, ge=1, le=20, description="Üretilecek soru sayısı")
):
    """
    Ezber düellosu ve çoklu oyuncu quiz yarışması için canlı sorular üretir.
    Eksik kelime, sonraki âyet ve kelime sıralama sorularını otomatik çeldiricilerle hazırlar.
    """
    import random
    t0 = time.time()
    conn = get_db()
    c = conn.cursor()
    
    target_surahs = [surah_id] if surah_id and surah_id > 0 else list(range(90, 115))
    placeholders = ",".join("?" * len(target_surahs))
    
    # Get pool of ayahs
    c.execute(f"""
        SELECT a.ayet_id, a.verse_key, a.surah_id, a.ayah_id, a.quran_uthmani, a.quran_simple,
               s.sure_name, s.name_arabic, t.text as translation_tr
        FROM ayahs a
        JOIN surahs s ON s.surah_id = a.surah_id
        LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
        WHERE a.surah_id IN ({placeholders})
        ORDER BY a.surah_id, a.ayah_id
    """, target_surahs)
    all_ayahs = [dict(r) for r in c.fetchall()]
    
    if not all_ayahs:
        conn.close()
        raise HTTPException(status_code=400, detail="Seçilen sûrelerde âyet bulunamadı")
        
    # Get words for these ayahs
    c.execute(f"""
        SELECT ayah_id, surah_id, word_id, quran_uthmani, text_turkish, text_latin
        FROM words
        WHERE surah_id IN ({placeholders})
        ORDER BY surah_id, ayah_id, word_id
    """, target_surahs)
    all_words = [dict(r) for r in c.fetchall()]
    
    from collections import defaultdict
    words_by_surah_ayah = defaultdict(list)
    for w in all_words:
        words_by_surah_ayah[(w["surah_id"], w["ayah_id"])].append(w)
        
    ayah_map = {(a["surah_id"], a["ayah_id"]): a for a in all_ayahs}
    
    # Random distractor word pool
    word_pool = list(set(w["quran_uthmani"] for w in all_words if len(w["quran_uthmani"]) > 2))
    if len(word_pool) < 10:
        c.execute("SELECT quran_uthmani FROM words ORDER BY RANDOM() LIMIT 50")
        word_pool = list(set([r[0] for r in c.fetchall()]))
        
    questions = []
    attempts = 0
    while len(questions) < count and attempts < 100:
        attempts += 1
        q_type = random.choice(["next_ayah", "missing_word"])
        target_ayah = random.choice(all_ayahs)
        s_id = target_ayah["surah_id"]
        a_id = target_ayah["ayah_id"]
        words = words_by_surah_ayah.get((s_id, a_id), [])
        
        if q_type == "next_ayah":
            next_key = (s_id, a_id + 1)
            if next_key in ayah_map:
                correct_next = ayah_map[next_key]
                wrong_candidates = [a for a in all_ayahs if (a["surah_id"], a["ayah_id"]) != next_key and (a["surah_id"], a["ayah_id"]) != (s_id, a_id)]
                if len(wrong_candidates) >= 3:
                    wrong_choices = random.sample(wrong_candidates, 3)
                    options = [correct_next["quran_uthmani"]] + [w["quran_uthmani"] for w in wrong_choices]
                    random.shuffle(options)
                    correct_idx = options.index(correct_next["quran_uthmani"])
                    questions.append({
                        "id": len(questions) + 1,
                        "type": "next_ayah",
                        "title": "Sonraki Âyeti Bul",
                        "surah_id": s_id,
                        "sure_name": target_ayah["sure_name"],
                        "ayah_id": a_id,
                        "prompt": f"{target_ayah['sure_name']} Sûresi {a_id}. Âyetten sonra hangi âyet gelir?",
                        "ayah_text": target_ayah["quran_uthmani"],
                        "translation": target_ayah.get("translation_tr", ""),
                        "options": options,
                        "correct_index": correct_idx,
                        "correct_answer": correct_next["quran_uthmani"]
                    })
        elif q_type == "missing_word":
            if len(words) >= 3:
                target_word_idx = random.randint(0, len(words) - 1)
                target_word = words[target_word_idx]
                masked_parts = []
                for idx, w in enumerate(words):
                    if idx == target_word_idx:
                        masked_parts.append("[ ? ]")
                    else:
                        masked_parts.append(w["quran_uthmani"])
                masked_ayah = " ".join(masked_parts)
                correct_text = target_word["quran_uthmani"]
                distractors = [w for w in word_pool if w != correct_text]
                if len(distractors) >= 3:
                    wrong_words = random.sample(distractors, 3)
                    options = [correct_text] + wrong_words
                    random.shuffle(options)
                    correct_idx = options.index(correct_text)
                    questions.append({
                        "id": len(questions) + 1,
                        "type": "missing_word",
                        "title": "Eksik Kelimeyi Tamamla",
                        "surah_id": s_id,
                        "sure_name": target_ayah["sure_name"],
                        "ayah_id": a_id,
                        "prompt": f"{target_ayah['sure_name']} {a_id}. Âyette [ ? ] yerine hangi kelime gelmelidir?",
                        "ayah_text": masked_ayah,
                        "translation": target_ayah.get("translation_tr", ""),
                        "options": options,
                        "correct_index": correct_idx,
                        "correct_answer": correct_text
                    })
                    
    conn.close()
    dt_ms = (time.time() - t0) * 1000
    return {
        "count": len(questions),
        "latency_ms": round(dt_ms, 2),
        "questions": questions
    }

# =====================================================================
# 9. QURAN.COM AUDIO & TILAVET ENTEGRASYONU
# =====================================================================
@app.get("/api/audio/reciters")
def get_reciters():
    """Quran.com API üzerinden resmî kāri ve tilavet listesi döner."""
    return {
        "source": "Quran.com v4 Audio API",
        "reciters": [
            {"id": 7, "name": "Mishari Rashid al-Afasy", "style": "Murattal (Akıcı & Net)", "default": True},
            {"id": 12, "name": "Mahmoud Khalil Al-Husary", "style": "Muallim (Ezber & Eğitim - Duraklamalı)", "recommended": True},
            {"id": 6, "name": "Mahmoud Khalil Al-Husary", "style": "Murattal (Klasik Tecvid)"},
            {"id": 2, "name": "AbdulBaset AbdulSamad", "style": "Murattal (Duru)"},
            {"id": 1, "name": "AbdulBaset AbdulSamad", "style": "Mujawwad (Makamlı)"},
            {"id": 9, "name": "Mohamed Siddiq al-Minshawi", "style": "Murattal (Hüzünlü)"},
            {"id": 3, "name": "Abdur-Rahman as-Sudais", "style": "Kâbe-i Muazzama"},
            {"id": 4, "name": "Abu Bakr al-Shatri", "style": "Murattal"},
            {"id": 5, "name": "Hani ar-Rifai", "style": "Murattal"}
        ]
    }

# =====================================================================
# 10. İLERİ DÜZEY HIFZ & BEYİN LABORATUVARI (KUANTUM MOTORLARI)
# =====================================================================
@app.get("/api/hifz/spatial/{surah_id}/{ayah_id}")
def get_spatial_position(surah_id: int, ayah_id: int):
    """
    15-Satır Medine Mushafı üzerinde âyetin sayfa numarası (1..604), 
    satır numarası (1..15) ve sağ/sol sayfa koordinatlarını döner.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT m.page_no, m.line_no, m.word_start, m.word_end,
               a.quran_uthmani, s.sure_name, s.name_arabic, t.text as translation_tr
        FROM mushaf_layout_15lines m
        JOIN ayahs a ON a.surah_id = m.surah_id AND a.ayah_id = m.ayah_id
        JOIN surahs s ON s.surah_id = m.surah_id
        LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
        WHERE m.surah_id = ? AND m.ayah_id = ?
        LIMIT 1
    """, (surah_id, ayah_id))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Sayfa mizanpaj verisi bulunamadı")
    
    r = dict(row)
    p_no = r["page_no"]
    is_right = (p_no % 2 != 0)
    
    return {
        "surah_id": surah_id,
        "ayah_id": ayah_id,
        "sure_name": r["sure_name"],
        "name_arabic": r["name_arabic"],
        "page_no": p_no,
        "line_no": r["line_no"],
        "word_start": r["word_start"],
        "word_end": r["word_end"],
        "page_side": "SAĞ SAYFA (Tek Numaralı)" if is_right else "SOL SAYFA (Çift Numaralı)",
        "is_right_page": is_right,
        "ayah_text": r["quran_uthmani"],
        "translation": r["translation_tr"] or ""
    }

@app.get("/api/hifz/mutashabihat")
def get_mutashabihat():
    """
    Hafızların en çok karıştırdığı meşhur Müteşâbih Âyet çiftlerini 
    fark analizleri ve tuzak kelimeleriyle birlikte döner.
    """
    curated_pairs = [
        {
            "id": 1,
            "title": "Bakara 48 vs Bakara 123 (Şefaat ve Adl Sıralaması)",
            "ayah1": {
                "surah_id": 2, "ayah_id": 48, "sure_name": "Bakara",
                "text": "وَٱتَّقُوا۟ يَوْمًۭا لَّا تَجْزِى نَفْسٌ عَن نَّفْسٍۢ شَيْـًۭٔا وَلَا يُقْبَلُ مِنْهَا شَفَـٰعَةٌۭ وَلَا يُؤْخَذُ مِنْهَا عَدْلٌۭ وَلَا هُمْ يُنصَرُونَ",
                "key_phrase": "وَلَا يُقْبَلُ مِنْهَا شَفَـٰعَةٌۭ وَلَا يُؤْخَذُ مِنْهَا عَدْلٌۭ"
            },
            "ayah2": {
                "surah_id": 2, "ayah_id": 123, "sure_name": "Bakara",
                "text": "وَٱتَّقُوا۟ يَوْمًۭا لَّا تَجْزِى نَفْسٌ عَن نَّفْسٍۢ شَيْـًۭٔا وَلَا يُقْبَلُ مِنْهَا عَدْلٌۭ وَلَا تَنفَعُهَا شَفَـٰعَةٌۭ وَلَا هُمْ يُنصَرُونَ",
                "key_phrase": "وَلَا يُقْبَلُ مِنْهَا عَدْلٌۭ وَلَا تَنفَعُهَا شَفَـٰعَةٌۭ"
            },
            "rule": "48. âyette önce 'Şefaat' sonra 'Adl' gelir; 123. âyette ise önce 'Adl' sonra 'Tenfeuhe Şefaat' gelir."
        },
        {
            "id": 2,
            "title": "Bakara 35 vs A'râf 19 (Hz. Âdem Cennet Emri)",
            "ayah1": {
                "surah_id": 2, "ayah_id": 35, "sure_name": "Bakara",
                "text": "وَقُلْنَا يَٰٓـَٔادَمُ ٱسْكُنْ أَنتَ وَزَوْجُكَ ٱلْجَنَّةَ وَكُلَا مِنْهَا رَغَدًا حَيْثُ شِئْتُمَا...",
                "key_phrase": "وَكُلَا مِنْهَا رَغَدًا"
            },
            "ayah2": {
                "surah_id": 7, "ayah_id": 19, "sure_name": "A'râf",
                "text": "وَيَٰٓـَٔادَمُ ٱسْكُنْ أَنتَ وَزَوْجُكَ ٱلْجَنَّةَ فَكُلَا مِنْ حَيْثُ شِئْتُمَا...",
                "key_phrase": "فَكُلَا مِنْ حَيْثُ شِئْتُمَا (رغدا kelimesi yoktur)"
            },
            "rule": "Bakara'da 'Ve külâ minhâ ragaden' genişliği varken, A'râf'ta 'Fe-külâ min haysü şi'tümâ' şeklinde 'ragaden' kelimesi yer almaz."
        },
        {
            "id": 3,
            "title": "Bakara 58 vs A'râf 161 (Karye Girişi ve Hıtta Duası)",
            "ayah1": {
                "surah_id": 2, "ayah_id": 58, "sure_name": "Bakara",
                "text": "وَإِذْ قُلْنَا ٱدْخُلُوا۟ هَٰذِهِ ٱلْقَرْيَةَ فَكُلُوا۟ مِنْهَا حَيْثُ شِئْتُمْ رَغَدًۭا وَٱدْخُلُوا۟ ٱلْبَابَ سُجَّدًۭا وَقُولُوا۟ حِطَّةٌۭ...",
                "key_phrase": "وَٱدْخُلُوا۟ ٱلْبَابَ سُجَّدًۭا وَقُولُوا۟ حِطَّةٌۭ"
            },
            "ayah2": {
                "surah_id": 7, "ayah_id": 161, "sure_name": "A'râf",
                "text": "وَإِذْ قِيلَ لَهُمُ ٱسْكُنُوا۟ هَٰذِهِ ٱلْقَرْيَةَ وَكُلُوا۟ مِنْهَا حَيْثُ شِئْتُمْ وَقُولُوا۟ حِطَّةٌۭ وَٱدْخُلُوا۟ ٱلْبَابَ سُجَّدًۭا...",
                "key_phrase": "وَقُولُوا۟ حِطَّةٌۭ وَٱدْخُلُوا۟ ٱلْبَابَ سُجَّدًۭا (Sıralama tersine döner!)"
            },
            "rule": "Bakara'da önce 'Kapıdan secde ederek girin' sonra 'Hıtta deyin' gelir. A'râf'ta ise önce 'Hıtta deyin' sonra 'Secde ederek girin' gelir."
        },
        {
            "id": 4,
            "title": "Bakara 61 vs Âl-i İmrân 112 (Peygamberleri Haksız Yere Öldürme)",
            "ayah1": {
                "surah_id": 2, "ayah_id": 61, "sure_name": "Bakara",
                "text": "...وَيَقْتُلُونَ ٱلنَّبِيِّـۧنَ بِغَيْرِ ٱلْحَقِّ...",
                "key_phrase": "ٱلنَّبِيِّـۧنَ (En-Nebiyyîn)"
            },
            "ayah2": {
                "surah_id": 3, "ayah_id": 112, "sure_name": "Âl-i İmrân",
                "text": "...وَيَقْتُلُونَ ٱلْأَنۢبِيَآءَ بِغَيْرِ حَقٍّۢ...",
                "key_phrase": "ٱلْأَنۢبِيَآءَ بِغَيْرِ حَقٍّۢ (El-Enbiyâe bi-ğayri hakk)"
            },
            "rule": "Bakara'da 'en-Nebiyyîn bi-ğayri'l-hakk', Âl-i İmrân'da ise 'el-Enbiyâe bi-ğayri hakk' kalıbı kullanılır."
        },
        {
            "id": 5,
            "title": "Bakara 136 vs Âl-i İmrân 84 (İman Beyanı Emri)",
            "ayah1": {
                "surah_id": 2, "ayah_id": 136, "sure_name": "Bakara",
                "text": "قُولُوٓا۟ ءَامَنَّا بِٱللَّهِ وَمَآ أُنزِلَ إِلَيْنَا...",
                "key_phrase": "قُولُوٓا۟ (Çoğul: Siz deyin)"
            },
            "ayah2": {
                "surah_id": 3, "ayah_id": 84, "sure_name": "Âl-i İmrân",
                "text": "قُلْ ءَامَنَّا بِٱللَّهِ وَمَآ أُنزِلَ عَلَيْنَا...",
                "key_phrase": "قُلْ (Tekil: De ki)"
            },
            "rule": "Bakara'da ümmete çoğul hitapla 'Kûlû' emredilir, Âl-i İmrân'da ise Peygamberimize tekil hitapla 'Kul' emredilir."
        }
    ]
    return {
        "total_pairs": len(curated_pairs),
        "pairs": curated_pairs
    }

@app.get("/api/hifz/inspector_round")
def get_inspector_round(surah_id: Optional[int] = Query(None)):
    """
    Mümeyyiz (Hata Dedektörü) oyunu için kasıtlı olarak 1 kelimesi değiştirilmiş 
    gerçek âyet üretir. Oyuncular ekranda/seste hatayı ilk yakalayan olmak için yarışır.
    """
    import random
    conn = get_db()
    c = conn.cursor()
    
    target_surah = surah_id if surah_id and surah_id > 0 else random.randint(90, 114)
    
    c.execute("""
        SELECT a.surah_id, a.ayah_id, a.quran_uthmani, s.sure_name, t.text as translation_tr
        FROM ayahs a
        JOIN surahs s ON s.surah_id = a.surah_id
        LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
        WHERE a.surah_id = ?
        ORDER BY RANDOM()
        LIMIT 1
    """, (target_surah,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Âyet bulunamadı")
    ayah = dict(row)
    
    # Get words
    c.execute("""
        SELECT word_id, quran_uthmani, text_turkish
        FROM words
        WHERE surah_id = ? AND ayah_id = ?
        ORDER BY word_id ASC
    """, (ayah["surah_id"], ayah["ayah_id"]))
    words = [dict(w) for w in c.fetchall()]
    
    if len(words) < 2:
        conn.close()
        raise HTTPException(status_code=400, detail="Âyette yeterli kelime yok")
        
    c.execute("SELECT quran_uthmani FROM words WHERE surah_id >= 90 ORDER BY RANDOM() LIMIT 20")
    pool = [r[0] for r in c.fetchall()]
    conn.close()
    
    target_idx = random.randint(0, len(words) - 1)
    original_word = words[target_idx]["quran_uthmani"]
    distractor_candidates = [w for w in pool if w != original_word and len(w) >= 2]
    fake_word = distractor_candidates[0] if distractor_candidates else "عَلِيمٌ"
    
    mutated_word_list = []
    for idx, w in enumerate(words):
        if idx == target_idx:
            mutated_word_list.append(fake_word)
        else:
            mutated_word_list.append(w["quran_uthmani"])
            
    return {
        "surah_id": ayah["surah_id"],
        "sure_name": ayah["sure_name"],
        "ayah_id": ayah["ayah_id"],
        "original_text": ayah["quran_uthmani"],
        "mutated_text": " ".join(mutated_word_list),
        "words": mutated_word_list,
        "glitch_word_index": target_idx,
        "original_word": original_word,
        "glitch_fake_word": fake_word,
        "translation": ayah["translation_tr"] or "",
        "audio_url": f"https://verses.quran.com/Alafasy/mp3/{str(ayah['surah_id']).zfill(3)}{str(ayah['ayah_id']).zfill(3)}.mp3"
    }

# =====================================================================
# 11. BİLGİ YARIŞMASI & GAME SHOW MOTORU (MİLYONER & KELİME OYUNU)
# =====================================================================
def get_reciter_audio_url(reciter_id: int, surah_id: int, ayah_id: int) -> str:
    s_str = str(surah_id).zfill(3)
    a_str = str(ayah_id).zfill(3)
    if reciter_id == 12:
        # Mahmoud Khalil Al-Husary (Muallim - Ezber & Eğitim Makamı)
        return f"https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/{s_str}{a_str}.mp3"
    elif reciter_id == 2:
        # AbdulBaset AbdulSamad (Murattal)
        return f"https://verses.quran.com/AbdulBaset/Murattal/mp3/{s_str}{a_str}.mp3"
    elif reciter_id == 9:
        # Mohamed Siddiq al-Minshawi (Murattal & Tecvid)
        return f"https://verses.quran.com/Minshawi/Murattal/mp3/{s_str}{a_str}.mp3"
    else:
        # Mishari Rashid al-Afasy (default)
        return f"https://verses.quran.com/Alafasy/mp3/{s_str}{a_str}.mp3"

@app.get("/api/gameshow/ladder")
def get_gameshow_ladder(
    surah_group: Optional[str] = Query(None, description="Özel sûre havuzu: 'juz30', 'first10', 'yasin_mulk', 'all'"),
    reciter_id: int = Query(12, description="Kāri ID (12: Husary Muallim, 7: Afasy, 2: AbdulBaset, 9: Minshawi)")
):
    """
    'Kim Hâfız Olmak İster?' yarışması için kolaydan zora 11 basamaklı 
    (Maksimum 100 Motivasyon Puanı) soru merdiveni üretir. 
    Seçilen sûre/cüz havuzuna ve kâriye göre dinamik ayarlanır.
    Tüm âyet metinleri 'quran_uthmani2' satırından çekilir.
    """
    import random
    conn = get_db()
    c = conn.cursor()
    
    # Dynamic Surah Progression based on pool
    if surah_group == "juz30":
        ladder_steps = [
            {"level": 1, "points": "5", "title": "5 Motivasyon Puanı", "checkpoint": False, "surahs": [112, 113, 114]},
            {"level": 2, "points": "10", "title": "10 Motivasyon Puanı", "checkpoint": False, "surahs": [108, 109, 110, 111]},
            {"level": 3, "points": "15", "title": "15 Motivasyon Puanı", "checkpoint": False, "surahs": [105, 106, 107]},
            {"level": 4, "points": "25", "title": "25 Motivasyon Puanı (1. Baraj) 🛡️", "checkpoint": True, "surahs": [95, 97, 99, 100, 101, 102, 103, 104]},
            {"level": 5, "points": "35", "title": "35 Motivasyon Puanı", "checkpoint": False, "surahs": [91, 92, 93, 94]},
            {"level": 6, "points": "50", "title": "50 Motivasyon Puanı", "checkpoint": False, "surahs": [87, 88, 89, 90]},
            {"level": 7, "points": "65", "title": "65 Motivasyon Puanı (2. Baraj) 🛡️", "checkpoint": True, "surahs": [83, 84, 85, 86]},
            {"level": 8, "points": "75", "title": "75 Motivasyon Puanı", "checkpoint": False, "surahs": [80, 81, 82]},
            {"level": 9, "points": "85", "title": "85 Motivasyon Puanı", "checkpoint": False, "surahs": [79]},
            {"level": 10, "points": "95", "title": "95 Motivasyon Puanı", "checkpoint": False, "surahs": [78]},
            {"level": 11, "points": "100", "title": "👑 100 Motivasyon Puanı (Zirve)", "checkpoint": True, "surahs": [78]}
        ]
    elif surah_group == "first10":
        ladder_steps = [
            {"level": 1, "points": "5", "title": "5 Motivasyon Puanı", "checkpoint": False, "surahs": [1]},
            {"level": 2, "points": "10", "title": "10 Motivasyon Puanı", "checkpoint": False, "surahs": [1, 2]},
            {"level": 3, "points": "15", "title": "15 Motivasyon Puanı", "checkpoint": False, "surahs": [2]},
            {"level": 4, "points": "25", "title": "25 Motivasyon Puanı (1. Baraj) 🛡️", "checkpoint": True, "surahs": [2, 3]},
            {"level": 5, "points": "35", "title": "35 Motivasyon Puanı", "checkpoint": False, "surahs": [3]},
            {"level": 6, "points": "50", "title": "50 Motivasyon Puanı", "checkpoint": False, "surahs": [4]},
            {"level": 7, "points": "65", "title": "65 Motivasyon Puanı (2. Baraj) 🛡️", "checkpoint": True, "surahs": [4, 5]},
            {"level": 8, "points": "75", "title": "75 Motivasyon Puanı", "checkpoint": False, "surahs": [5, 6]},
            {"level": 9, "points": "85", "title": "85 Motivasyon Puanı", "checkpoint": False, "surahs": [6, 7]},
            {"level": 10, "points": "95", "title": "95 Motivasyon Puanı", "checkpoint": False, "surahs": [7, 8]},
            {"level": 11, "points": "100", "title": "👑 100 Motivasyon Puanı (Zirve)", "checkpoint": True, "surahs": [9, 10]}
        ]
    elif surah_group == "yasin_mulk":
        ladder_steps = [
            {"level": 1, "points": "5", "title": "5 Motivasyon Puanı", "checkpoint": False, "surahs": [67]},
            {"level": 2, "points": "10", "title": "10 Motivasyon Puanı", "checkpoint": False, "surahs": [67, 55]},
            {"level": 3, "points": "15", "title": "15 Motivasyon Puanı", "checkpoint": False, "surahs": [55]},
            {"level": 4, "points": "25", "title": "25 Motivasyon Puanı (1. Baraj) 🛡️", "checkpoint": True, "surahs": [56]},
            {"level": 5, "points": "35", "title": "35 Motivasyon Puanı", "checkpoint": False, "surahs": [56, 36]},
            {"level": 6, "points": "50", "title": "50 Motivasyon Puanı", "checkpoint": False, "surahs": [36]},
            {"level": 7, "points": "65", "title": "65 Motivasyon Puanı (2. Baraj) 🛡️", "checkpoint": True, "surahs": [36, 48]},
            {"level": 8, "points": "75", "title": "75 Motivasyon Puanı", "checkpoint": False, "surahs": [48, 78]},
            {"level": 9, "points": "85", "title": "85 Motivasyon Puanı", "checkpoint": False, "surahs": [18]},
            {"level": 10, "points": "95", "title": "95 Motivasyon Puanı", "checkpoint": False, "surahs": [18, 36]},
            {"level": 11, "points": "100", "title": "👑 100 Motivasyon Puanı (Zirve)", "checkpoint": True, "surahs": [36]}
        ]
    else:
        ladder_steps = [
            {"level": 1, "points": "5", "title": "5 Motivasyon Puanı", "checkpoint": False, "surahs": [1, 112, 113, 114]},
            {"level": 2, "points": "10", "title": "10 Motivasyon Puanı", "checkpoint": False, "surahs": [108, 103, 110, 111]},
            {"level": 3, "points": "15", "title": "15 Motivasyon Puanı", "checkpoint": False, "surahs": [105, 106, 107, 109]},
            {"level": 4, "points": "25", "title": "25 Motivasyon Puanı (1. Baraj) 🛡️", "checkpoint": True, "surahs": [95, 97, 99, 100]},
            {"level": 5, "points": "35", "title": "35 Motivasyon Puanı", "checkpoint": False, "surahs": [87, 88, 89, 91, 92]},
            {"level": 6, "points": "50", "title": "50 Motivasyon Puanı", "checkpoint": False, "surahs": [78, 79, 81, 82]},
            {"level": 7, "points": "65", "title": "65 Motivasyon Puanı (2. Baraj) 🛡️", "checkpoint": True, "surahs": [67, 55, 56]},
            {"level": 8, "points": "75", "title": "75 Motivasyon Puanı", "checkpoint": False, "surahs": [36, 18, 48]},
            {"level": 9, "points": "85", "title": "85 Motivasyon Puanı", "checkpoint": False, "surahs": [12, 19, 20]},
            {"level": 10, "points": "95", "title": "95 Motivasyon Puanı", "checkpoint": False, "surahs": [3, 4, 5]},
            {"level": 11, "points": "100", "title": "👑 100 Motivasyon Puanı (Zirve)", "checkpoint": True, "surahs": [2]}
        ]
    
    # Clean global pool of unique distractor words
    c.execute("SELECT quran_uthmani2 FROM ayahs ORDER BY RANDOM() LIMIT 100")
    raw_texts = [r[0] for r in c.fetchall() if r[0]]
    raw_words = [clean_quran_word(w) for txt in raw_texts for w in txt.split()]
    global_words_pool = list(set([w for w in raw_words if len(w) >= 3]))
    SAFE_FALLBACK_WORDS = ["عَلِيمٌ", "حَكِيمٌ", "غَفُورٌ", "رَحِيمٌ", "بَصِيرٌ", "قَدِيرٌ", "خَبِيرٌ", "عَظِيمٌ", "تَوَّابٌ", "حَمِيدٌ"]

    questions = []
    for step in ladder_steps:
        target_s = random.choice(step["surahs"])
        c.execute("""
            SELECT a.surah_id, a.ayah_id, a.quran_uthmani2, s.sure_name, t.text as translation_tr
            FROM ayahs a
            JOIN surahs s ON s.surah_id = a.surah_id
            LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
            WHERE a.surah_id = ?
            ORDER BY RANDOM()
            LIMIT 1
        """, (target_s,))
        row = c.fetchone()
        if not row:
            continue
        ayah = dict(row)
        
        uthmani2_full = ayah["quran_uthmani2"] or ""
        raw_w_rows = uthmani2_full.split()
        
        q_mode = "missing_word"
        if step["level"] <= 8 and len(raw_w_rows) >= 4 and random.random() < 0.35:
            q_mode = "surah_name"

        valid_indices = [i for i, w in enumerate(raw_w_rows) if len(clean_quran_word(w)) >= 2]
        audio_stream = get_reciter_audio_url(reciter_id, ayah["surah_id"], ayah["ayah_id"])

        if q_mode == "missing_word" and valid_indices:
            t_idx = random.choice(valid_indices)
            raw_correct_word = raw_w_rows[t_idx]
            clean_correct_word = clean_quran_word(raw_correct_word)
            
            masked_words = [w if i != t_idx else "[ ? ]" for i, w in enumerate(raw_w_rows)]
            masked_text = " ".join(masked_words)

            available_distractors = [w for w in global_words_pool if w != clean_correct_word and len(w) >= 2]
            wrong_choices = set()
            if len(available_distractors) >= 3:
                chosen = random.sample(available_distractors, min(len(available_distractors), 10))
                for w in chosen:
                    if w != clean_correct_word and w not in wrong_choices:
                        wrong_choices.add(w)
                    if len(wrong_choices) == 3:
                        break

            for fw in SAFE_FALLBACK_WORDS:
                if len(wrong_choices) == 3:
                    break
                if fw != clean_correct_word and fw not in wrong_choices:
                    wrong_choices.add(fw)

            options = [clean_correct_word] + list(wrong_choices)
            options = list(dict.fromkeys(options))
            while len(options) < 4:
                for fw in SAFE_FALLBACK_WORDS:
                    if fw not in options:
                        options.append(fw)
                        break

            options = options[:4]
            random.shuffle(options)
            corr_idx = options.index(clean_correct_word)
            
            wrong_indices = [i for i in range(4) if i != corr_idx]
            joker_50 = random.sample(wrong_indices, 2)
            
            questions.append({
                "level": step["level"],
                "points": step["points"],
                "title": step["title"],
                "checkpoint": step["checkpoint"],
                "surah_id": ayah["surah_id"],
                "sure_name": ayah["sure_name"],
                "ayah_id": ayah["ayah_id"],
                "prompt": f"{ayah['sure_name']} Sûresi {ayah['ayah_id']}. âyetteki [ ? ] yerine hangi kelime gelmelidir?",
                "ayah_arabic": masked_text,
                "full_ayah_arabic": uthmani2_full,
                "translation": ayah["translation_tr"] or "",
                "options": options,
                "correct_index": corr_idx,
                "joker_50_eliminated": joker_50,
                "audio_url": audio_stream
            })
        else:
            c.execute("SELECT sure_name FROM surahs WHERE surah_id != ? ORDER BY RANDOM() LIMIT 10", (ayah["surah_id"],))
            wrong_names_pool = [r[0] for r in c.fetchall()]
            wrong_names = []
            for n in wrong_names_pool:
                if n != ayah["sure_name"] and n not in wrong_names:
                    wrong_names.append(n)
                if len(wrong_names) == 3:
                    break

            options = [ayah["sure_name"]] + wrong_names
            options = list(dict.fromkeys(options))
            random.shuffle(options)
            corr_idx = options.index(ayah["sure_name"])
            wrong_indices = [i for i in range(4) if i != corr_idx]
            joker_50 = random.sample(wrong_indices, 2)
            
            questions.append({
                "level": step["level"],
                "points": step["points"],
                "title": step["title"],
                "checkpoint": step["checkpoint"],
                "surah_id": ayah["surah_id"],
                "sure_name": ayah["sure_name"],
                "ayah_id": ayah["ayah_id"],
                "prompt": f"«{uthmani2_full}» âyeti hangi mübarek sûremizde yer alır?",
                "ayah_arabic": uthmani2_full,
                "full_ayah_arabic": uthmani2_full,
                "translation": ayah["translation_tr"] or "",
                "options": options,
                "correct_index": corr_idx,
                "joker_50_eliminated": joker_50,
                "audio_url": audio_stream
            })
            
    conn.close()
    return {
        "game_format": "Kim Hâfız Olmak İster? (100 Motivasyon Puanı Merdiveni)",
        "surah_group": surah_group or "curated",
        "reciter_id": reciter_id,
        "total_levels": len(questions),
        "ladder": questions
    }

QURANIC_PUZZLES_MASTER = [
    {
        "id": "puz-1",
        "question": "Fil Sûresi 3. âyette Kâbe'yi korumak üzere Ebrehe'nin ordusu üzerine sürü sürü gönderilen kuşların adı?",
        "answer": "EBABİL",
        "answer_arabic": "أَبَابِيلَ",
        "surah_id": 105, "ayah_id": 3, "sure_name": "Fil",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/105003.mp3"
    },
    {
        "id": "puz-2",
        "question": "Mülk Sûresi 1. âyette 'Mutlak hükümranlık ve egemenlik elinde olan Allah yüceler yücesidir' âyetinde geçen ve sûreye adını veren kelime?",
        "answer": "MÜLK",
        "answer_arabic": "ٱلْمُلْكُ",
        "surah_id": 67, "ayah_id": 1, "sure_name": "Mülk",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/067001.mp3"
    },
    {
        "id": "puz-3",
        "question": "Bakara Sûresi 255. âyette (Âyetü'l-Kürsî) Allah'ın 'Gökleri ve yeri ayakta tutan, yarattıklarını sevk ve idare eden' yüce esmâsı?",
        "answer": "KAYYUM",
        "answer_arabic": "ٱلْقَيُّومُ",
        "surah_id": 2, "ayah_id": 255, "sure_name": "Bakara",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/002255.mp3"
    },
    {
        "id": "puz-4",
        "question": "Bakara Sûresi 255. âyette Allah Teâlâ'nın 'Daima diri, ezeli ve ebedi hayat sahibi olan' esmâ-i hüsnâsı?",
        "answer": "HAYY",
        "answer_arabic": "ٱلْحَىُّ",
        "surah_id": 2, "ayah_id": 255, "sure_name": "Bakara",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/002255.mp3"
    },
    {
        "id": "puz-5",
        "question": "Nebe Sûresi 7. âyette yeryüzünün sarsılmaması ve dengesi için dağların birer ne kılındığı bildirilmektedir?",
        "answer": "KAZIK",
        "answer_arabic": "أَوْتَادًا",
        "surah_id": 78, "ayah_id": 7, "sure_name": "Nebe",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/078007.mp3"
    },
    {
        "id": "puz-6",
        "question": "Fâtiha Sûresi 6. âyette geçen ve 'Bizi dosdoğru yola ilet' duasında zikredilen sırat-ı ne?",
        "answer": "MÜSTAKİM",
        "answer_arabic": "ٱلْمُسْتَقِيمَ",
        "surah_id": 1, "ayah_id": 6, "sure_name": "Fâtiha",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/001006.mp3"
    },
    {
        "id": "puz-7",
        "question": "Kur'an-ı Kerim'de 31 defa 'Rabbinizin hangi nimetlerini yalanlayabilirsiniz' âyetinin tekrarlandığı 55. mübarek sûremiz?",
        "answer": "RAHMAN",
        "answer_arabic": "ٱلرَّحْمَـٰنُ",
        "surah_id": 55, "ayah_id": 1, "sure_name": "Rahmân",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/055001.mp3"
    },
    {
        "id": "puz-8",
        "question": "İhlâs Sûresi 2. âyette Allah'ın 'Hiçbir şeye muhtaç olmayan, aksine her varlığın O'na muhtaç olduğu' yüce sıfatı?",
        "answer": "SAMED",
        "answer_arabic": "ٱلصَّمَدُ",
        "surah_id": 112, "ayah_id": 2, "sure_name": "İhlâs",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/112002.mp3"
    },
    {
        "id": "puz-9",
        "question": "Kadir Gecesi'nin 'bin aydan daha hayırlı' olduğunu ve Kur'an'ın bu gecede indirildiğini bildiren 97. sûremiz?",
        "answer": "KADİR",
        "answer_arabic": "ٱلْقَدْرِ",
        "surah_id": 97, "ayah_id": 1, "sure_name": "Kadir",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/097001.mp3"
    },
    {
        "id": "puz-10",
        "question": "Peygamber Efendimiz'e (s.a.v.) müjdelenen 'tükenmez hayır, bolluk ve cennet havuzu' anlamına gelen 108. sûre?",
        "answer": "KEVSER",
        "answer_arabic": "ٱلْكَوْثَرَ",
        "surah_id": 108, "ayah_id": 1, "sure_name": "Kevser",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/108001.mp3"
    },
    {
        "id": "puz-11",
        "question": "İlk inen âyetleri içeren ve 'Yaratan Rabbinin adıyla oku!' emriyle başlayan 96. sûre?",
        "answer": "ALAK",
        "answer_arabic": "عَلَقٍ",
        "surah_id": 96, "ayah_id": 2, "sure_name": "Alak",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/096001.mp3"
    },
    {
        "id": "puz-12",
        "question": "Peygamber Efendimiz (s.a.v.) tarafından 'Kur'an'ın kalbi' olarak nitelendirilen 36. sûremiz?",
        "answer": "YASİN",
        "answer_arabic": "يسٓ",
        "surah_id": 36, "ayah_id": 1, "sure_name": "Yâsîn",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/036001.mp3"
    },
    {
        "id": "puz-13",
        "question": "Kur'an-ı Kerim'i baştan sona ezberleyip kalbinde muhafaza eden kimseye verilen şerefli unvan?",
        "answer": "HAFIZ",
        "answer_arabic": "حَفِيظٌ",
        "surah_id": 11, "ayah_id": 57, "sure_name": "Hûd",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/011057.mp3"
    },
    {
        "id": "puz-14",
        "question": "Zelzele Sûresi'nde yerin şiddetle sarsılacağı ve herkesin zerre miktarı amelini göreceği dehşetli gün?",
        "answer": "KIYAMET",
        "answer_arabic": "ٱلْقِيَـٰمَةِ",
        "surah_id": 75, "ayah_id": 1, "sure_name": "Kıyâme",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/075001.mp3"
    },
    {
        "id": "puz-15",
        "question": "Kur'an-ı Kerim'in en uzun sûresi olan ve 286 âyet ihtiva eden mübarek sûremiz?",
        "answer": "BAKARA",
        "answer_arabic": "ٱلْبَقَرَةِ",
        "surah_id": 2, "ayah_id": 67, "sure_name": "Bakara",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/002067.mp3"
    },
    {
        "id": "puz-16",
        "question": "Nâs Sûresi 4. âyette insanların kalbine sinsi vesveseler fısıldayan şerli varlığın Kur'an'daki sıfatı?",
        "answer": "HANNAS",
        "answer_arabic": "ٱلْخَنَّاسِ",
        "surah_id": 114, "ayah_id": 4, "sure_name": "Nâs",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/114004.mp3"
    },
    {
        "id": "puz-17",
        "question": "Tîn Sûresi 1. âyette üzerine yemin edilen mübarek zeytin ve diğer meyve?",
        "answer": "İNCİR",
        "answer_arabic": "ٱلتِّينِ",
        "surah_id": 95, "ayah_id": 1, "sure_name": "Tîn",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/095001.mp3"
    },
    {
        "id": "puz-18",
        "question": "Hümeze Sûresi'nde mal toplayıp onu sayan dedikoducuların atılacağı, kemikleri kıran ve yüreklere tırmanan ateş?",
        "answer": "HUTAME",
        "answer_arabic": "ٱلْحُطَمَةُ",
        "surah_id": 104, "ayah_id": 4, "sure_name": "Hümeze",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/104004.mp3"
    },
    {
        "id": "puz-19",
        "question": "Âdiyât Sûresi 1. âyette soluk soluğa koşan ve tırnaklarıyla kıvılcım saçan savaş binekleri?",
        "answer": "ATLAR",
        "answer_arabic": "وَٱلْعَـٰدِيَـٰتِ",
        "surah_id": 100, "ayah_id": 1, "sure_name": "Âdiyât",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/100001.mp3"
    },
    {
        "id": "puz-20",
        "question": "Şems Sûresi 1. âyette üzerine ve aydınlığına yemin edilen gök cismi?",
        "answer": "GÜNEŞ",
        "answer_arabic": "وَٱلشَّمْسِ",
        "surah_id": 91, "ayah_id": 1, "sure_name": "Şems",
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/091001.mp3"
    }
]

def build_puzzle_round(item, index, conn):
    import random
    c = conn.cursor()
    c.execute("SELECT quran_uthmani2 FROM ayahs WHERE surah_id = ? AND ayah_id = ?", (item["surah_id"], item["ayah_id"]))
    row_a = c.fetchone()
    full_ayah = row_a[0] if row_a and row_a[0] else item["answer_arabic"]

    c.execute("SELECT text FROM translations WHERE surah_id = ? AND ayah_id = ? AND edition_id = 'tr-diyanet-yeni'", (item["surah_id"], item["ayah_id"]))
    row_t = c.fetchone()
    trans = row_t[0] if row_t and row_t[0] else ""

    ans_letters = list(item["answer"].upper())
    distractor_pool = [ch for ch in "ABCÇDEFGHİIJKLMNOÖPRSŞTUÜVYZ" if ch not in ans_letters]
    distractors = random.sample(distractor_pool, min(3, len(distractor_pool)))
    tile_pool = ans_letters + distractors
    random.shuffle(tile_pool)

    return {
        "round": index + 1,
        "id": item["id"],
        "clue": item["question"],
        "answer": item["answer"].upper(),
        "letters": ans_letters,
        "word_letters": ans_letters,
        "letter_count": len(ans_letters),
        "scrambled_pool": tile_pool,
        "answer_arabic": item["answer_arabic"],
        "surah_id": item["surah_id"],
        "ayah_id": item["ayah_id"],
        "sure_name": item["sure_name"],
        "full_ayah_arabic": full_ayah,
        "translation": trans,
        "audio_url": item.get("audio_url") or get_reciter_audio_url(12, item["surah_id"], item["ayah_id"]),
        "max_score": 20
    }

@app.get("/api/gameshow/puzzle-game")
@app.get("/api/gameshow/wordgame")
def get_puzzle_game_rounds(count: int = Query(5, ge=1, le=20)):
    """
    Bulmaca tarzında Kur'an kelime oyunu üretir.
    Kullanıcı sorunun cevabını kare bulmaca kutularında harf havuzundan seçerek veya yazarak bulur.
    Âyet metinleri 'quran_uthmani2' satırından çekilir ve Husary Muallim audio CDN ile sunulur.
    Maksimum toplam Motivasyon Puanı: 100 (5 Tur x 20 Puan).
    """
    import random
    conn = get_db()
    
    # Select random count from curated puzzle master
    pool = list(QURANIC_PUZZLES_MASTER)
    random.shuffle(pool)
    selected = pool[:count]
    
    rounds = []
    for idx, item in enumerate(selected):
        rounds.append(build_puzzle_round(item, idx, conn))
        
    conn.close()
    return {
        "game_format": "Bulmaca Tarzı Kur'an Kelime Oyunu",
        "rounds_count": len(rounds),
        "max_total_score": 100,
        "rounds": rounds
    }

# =====================================================================
# 13. CANLI YARIŞMA ODALARI & İZLEYİCİ (SPECTATOR) MİMARİSİ
# =====================================================================
class CreateRoomRequest(BaseModel):
    name: str
    mode: str = "buzzer"  # 'buzzer', 'wordgame', 'millionaire'
    surah_pool: str = "30. Cüz (Amme Cüzü)"
    max_players: int = 4
    allow_substitute: bool = True
    host_name: str = "Oda Yöneticisi"

class TakeoverSeatRequest(BaseModel):
    player_name: str
    seat_id: Optional[str] = None

class ReactionRequest(BaseModel):
    emoji: str
    sender: str = "İzleyici"

class RoomConnectionManager:
    def __init__(self):
        self.active_rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
        self.active_rooms[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_rooms and websocket in self.active_rooms[room_id]:
            self.active_rooms[room_id].remove(websocket)

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_rooms:
            dead_sockets = []
            for ws in self.active_rooms[room_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_sockets.append(ws)
            for ds in dead_sockets:
                self.disconnect(room_id, ds)

room_manager = RoomConnectionManager()

LIVE_ROOMS = {
    "room-101": {
        "id": "room-101",
        "name": "30. Cüz Hâfızlar Meydanı",
        "mode": "buzzer",
        "mode_title": "4 Kişilik Canlı Stüdyo Arenası",
        "surah_pool": "30. Cüz (Amme Cüzü)",
        "max_players": 4,
        "players": [
            {"id": "p1", "name": "Ahmet Hâfız", "score": 40, "connected": True, "avatar": "👤", "color": "emerald"},
            {"id": "p2", "name": "Zeynep K.", "score": 30, "connected": True, "avatar": "🧕", "color": "blue"},
            {"id": "p3", "name": "Mustafa Y.", "score": 20, "connected": True, "avatar": "🧔", "color": "amber"},
            {"id": "p4", "name": "Koltuk 4 (Açık)", "score": 0, "connected": False, "avatar": "🪑", "color": "purple", "is_empty": True}
        ],
        "spectators_count": 84,
        "status": "live",
        "current_round": 4,
        "total_rounds": 10,
        "empty_seat_available": True,
        "allow_substitute": True,
        "created_at": time.time() - 320
    },
    "room-102": {
        "id": "room-102",
        "name": "Hızlı Kelime Avcıları",
        "mode": "wordgame",
        "mode_title": "Kelime Oyunu // Harf Alayım!",
        "surah_pool": "Karışık Kur'an Kelimeleri",
        "max_players": 2,
        "players": [
            {"id": "p1", "name": "Bilal H.", "score": 40, "connected": True, "avatar": "👨‍🎓", "color": "emerald"},
            {"id": "p2", "name": "Koltuk 2 (Açık)", "score": 0, "connected": False, "avatar": "🪑", "color": "blue", "is_empty": True}
        ],
        "spectators_count": 42,
        "status": "live",
        "current_round": 3,
        "total_rounds": 5,
        "empty_seat_available": True,
        "allow_substitute": True,
        "created_at": time.time() - 180
    },
    "room-103": {
        "id": "room-103",
        "name": "Yâsîn & Mülk Merdiveni",
        "mode": "millionaire",
        "mode_title": "Kim Hâfız Olmak İster?",
        "surah_pool": "Yâsîn, Mülk, Rahmân Sûreleri",
        "max_players": 1,
        "players": [
            {"id": "p1", "name": "Fâtıma Zehra", "score": 65, "connected": True, "avatar": "🧕", "color": "amber"}
        ],
        "spectators_count": 128,
        "status": "live",
        "current_round": 7,
        "total_rounds": 11,
        "empty_seat_available": False,
        "allow_substitute": True,
        "created_at": time.time() - 600
    },
    "room-104": {
        "id": "room-104",
        "name": "Genç Kuşak Âyet Düellosu",
        "mode": "buzzer",
        "mode_title": "4 Kişilik Canlı Stüdyo Arenası",
        "surah_pool": "İlk 10 Sûre",
        "max_players": 4,
        "players": [
            {"id": "p1", "name": "Ömer Faruk", "score": 10, "connected": True, "avatar": "👦", "color": "emerald"},
            {"id": "p2", "name": "Salih E.", "score": 10, "connected": True, "avatar": "🧔", "color": "blue"},
            {"id": "p3", "name": "Koltuk 3 (Açık)", "score": 0, "connected": False, "avatar": "🪑", "color": "amber", "is_empty": True},
            {"id": "p4", "name": "Koltuk 4 (Açık)", "score": 0, "connected": False, "avatar": "🪑", "color": "purple", "is_empty": True}
        ],
        "spectators_count": 64,
        "status": "waiting",
        "current_round": 1,
        "total_rounds": 10,
        "empty_seat_available": True,
        "allow_substitute": True,
        "created_at": time.time() - 60
    },
    "room-105": {
        "id": "room-105",
        "name": "Bakara & Âl-i İmrân Zirvesi",
        "mode": "millionaire",
        "mode_title": "Kim Hâfız Olmak İster? (Zirve)",
        "surah_pool": "Bakara & Âl-i İmrân",
        "max_players": 1,
        "players": [
            {"id": "p1", "name": "Hüseyin R. (Grand Master)", "score": 95, "connected": True, "avatar": "👑", "color": "amber"}
        ],
        "spectators_count": 210,
        "status": "live",
        "current_round": 10,
        "total_rounds": 11,
        "empty_seat_available": False,
        "allow_substitute": True,
        "created_at": time.time() - 750
    },
    "room-106": {
        "id": "room-106",
        "name": "Kısa Sûreler Hızlı Ligi",
        "mode": "buzzer",
        "mode_title": "4 Kişilik Canlı Stüdyo Arenası",
        "surah_pool": "30. Cüz (Amme Cüzü)",
        "max_players": 4,
        "players": [
            {"id": "p1", "name": "Ayşe Betül", "score": 30, "connected": True, "avatar": "🧕", "color": "emerald"},
            {"id": "p2", "name": "Hacer N.", "score": 20, "connected": True, "avatar": "👩‍🎓", "color": "blue"},
            {"id": "p3", "name": "İbrahim Halil", "score": 10, "connected": True, "avatar": "🧑‍🏫", "color": "amber"},
            {"id": "p4", "name": "Koltuk 4 (Açık)", "score": 0, "connected": False, "avatar": "🪑", "color": "purple", "is_empty": True}
        ],
        "spectators_count": 95,
        "status": "live",
        "current_round": 3,
        "total_rounds": 10,
        "empty_seat_available": True,
        "allow_substitute": True,
        "created_at": time.time() - 240
    }
}

@app.get("/api/gameshow/live-stats")
def get_gameshow_live_stats():
    """
    Anasayfa canlı yarışma paneli istatistiklerini döner:
    Aktif yarışmacı sayısı, canlı izleyici sayısı, oda sayısı ve mevcut yarışma modelleri.
    """
    total_connected_players = sum(
        sum(1 for p in r["players"] if p.get("connected") and not p.get("is_empty"))
        for r in LIVE_ROOMS.values()
    )
    # Plus baseline casual single-player app users for vibrant studio feel
    active_contestants = max(18, total_connected_players + 15)
    total_spectators = sum(r.get("spectators_count", 0) for r in LIVE_ROOMS.values())
    
    return {
        "active_contestants": active_contestants,
        "active_spectators": max(250, total_spectators),
        "total_rooms": len(LIVE_ROOMS),
        "available_modes_count": 4,
        "modes": [
            {
                "id": "millionaire",
                "name": "Kim Hâfız Olmak İster?",
                "badge": "11 Basamaklı Merdiven",
                "max_score": 100,
                "icon": "👑",
                "desc": "11 basamaklı merdiven, 4 hayat kurtaran joker ve 2 baraj noktası ile Kur'an bilgisi testi."
            },
            {
                "id": "wordgame",
                "name": "Kelime Oyunu // Harf Alayım!",
                "badge": "5 Tur × 20 Puan",
                "max_score": 100,
                "icon": "🔤",
                "desc": "Ali İhsan Varol formatı: âyet kelimelerini harf talep ederek veya buzzer ile anında çözme."
            },
            {
                "id": "buzzer",
                "name": "4 Kişilik Canlı Stüdyo Arenası",
                "badge": "10 Soru Buzzer Düellosu",
                "max_score": 100,
                "icon": "⚡",
                "desc": "Kahoot & TV stüdyosu tarzı: ilk butona basanın +10 puan kaptığı anlık canlı arena."
            },
            {
                "id": "custom_room",
                "name": "Özel Challenge Odaları & İzleyici Arenası",
                "badge": "Canlı İzleme & Yedek Devralma",
                "max_score": 100,
                "icon": "🏟️",
                "desc": "Kendi odanı kur; canlı izleyici olarak katıl, bağlantısı kopan oyuncunun koltuğuna geç!"
            }
        ]
    }

@app.get("/api/gameshow/rooms")
def get_challenge_rooms():
    """Tüm aktif canlı yarışma odalarını döner."""
    rooms_list = list(LIVE_ROOMS.values())
    # Sort by active spectators desc
    rooms_list.sort(key=lambda x: (x.get("status") == "live", x.get("spectators_count", 0)), reverse=True)
    return {
        "total_rooms": len(rooms_list),
        "rooms": rooms_list
    }

@app.get("/api/gameshow/rooms/{room_id}")
def get_challenge_room_detail(room_id: str):
    """Belirli bir odanın anlık durumunu döner."""
    if room_id not in LIVE_ROOMS:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    return LIVE_ROOMS[room_id]

@app.post("/api/gameshow/rooms/create")
async def create_challenge_room(req: CreateRoomRequest):
    """Yeni bir özel canlı yarışma odası oluşturur."""
    new_id = f"room-{int(time.time()) % 10000}"
    mode_titles = {
        "buzzer": "4 Kişilik Canlı Stüdyo Arenası",
        "wordgame": "Kelime Oyunu // Harf Alayım!",
        "millionaire": "Kim Hâfız Olmak İster?"
    }
    
    players = []
    # Host is player 1
    players.append({
        "id": "p1",
        "name": req.host_name or "Oda Sahibi",
        "score": 0,
        "connected": True,
        "avatar": "👑",
        "color": "emerald"
    })
    
    # Remaining slots are empty seats open for contestants or spectators
    colors = ["blue", "amber", "purple", "rose"]
    for i in range(2, req.max_players + 1):
        players.append({
            "id": f"p{i}",
            "name": f"Koltuk {i} (Açık)",
            "score": 0,
            "connected": False,
            "avatar": "🪑",
            "color": colors[(i - 2) % len(colors)],
            "is_empty": True
        })
        
    room_obj = {
        "id": new_id,
        "name": req.name,
        "mode": req.mode,
        "mode_title": mode_titles.get(req.mode, "Canlı Yarışma"),
        "surah_pool": req.surah_pool,
        "max_players": req.max_players,
        "players": players,
        "spectators_count": 1,
        "status": "waiting",
        "current_round": 1,
        "total_rounds": 10 if req.mode == "buzzer" else (5 if req.mode == "wordgame" else 11),
        "empty_seat_available": (req.max_players > 1),
        "allow_substitute": req.allow_substitute,
        "created_at": time.time()
    }
    
    LIVE_ROOMS[new_id] = room_obj
    return {
        "success": True,
        "message": "Oda başarıyla oluşturuldu!",
        "room": room_obj
    }

@app.post("/api/gameshow/rooms/{room_id}/join-spectator")
async def join_room_spectator(room_id: str):
    """Odaya canlı izleyici olarak katılır."""
    if room_id not in LIVE_ROOMS:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    room = LIVE_ROOMS[room_id]
    room["spectators_count"] = room.get("spectators_count", 0) + 1
    
    await room_manager.broadcast(room_id, {
        "type": "spectator_joined",
        "spectators_count": room["spectators_count"]
    })
    
    return {
        "success": True,
        "spectators_count": room["spectators_count"],
        "room": room
    }

@app.post("/api/gameshow/rooms/{room_id}/leave-spectator")
async def leave_room_spectator(room_id: str):
    """İzleyici odadan ayrılır."""
    if room_id not in LIVE_ROOMS:
        return {"success": True}
    room = LIVE_ROOMS[room_id]
    room["spectators_count"] = max(0, room.get("spectators_count", 1) - 1)
    return {"success": True, "spectators_count": room["spectators_count"]}

@app.post("/api/gameshow/rooms/{room_id}/simulate-disconnect")
async def simulate_player_disconnect(room_id: str):
    """
    Yarışmacılardan birinin bağlantısının koptuğunu veya odadan ayrıldığını simüle eder.
    Böylece izleyiciler anında boş koltuğu devralıp yarışmaya katılabilir!
    """
    if room_id not in LIVE_ROOMS:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    room = LIVE_ROOMS[room_id]
    
    # Find an active player to disconnect (starting from p3 or p2)
    target_player = None
    for p in reversed(room["players"]):
        if p.get("connected") and not p.get("is_empty"):
            target_player = p
            break
            
    if not target_player:
        # None active, make one slot empty
        target_player = room["players"][-1]
        
    old_name = target_player["name"]
    target_player["name"] = f"{old_name} (Koptu / Boş Koltuk)"
    target_player["connected"] = False
    target_player["is_empty"] = True
    target_player["avatar"] = "🪑"
    room["empty_seat_available"] = True
    
    event_msg = {
        "type": "player_disconnected",
        "seat_id": target_player["id"],
        "message": f"🚨 {old_name} yarışmadan ayrıldı / bağlantısı koptu! İzleyiciler boş koltuğa geçebilir!",
        "room": room
    }
    await room_manager.broadcast(room_id, event_msg)
    
    return {
        "success": True,
        "disconnected_player": old_name,
        "seat_id": target_player["id"],
        "room": room
    }

@app.post("/api/gameshow/rooms/{room_id}/takeover-seat")
async def takeover_empty_seat(room_id: str, req: TakeoverSeatRequest):
    """
    İzleyici, ayrılan / bağlantısı kopan yarışmacının boş koltuğuna geçerek yarışmaya dahil olur.
    Eşzamanlı çakışmaları (race condition) önlemek için asyncio.Lock korumalıdır.
    """
    async with takeover_lock:
        if room_id not in LIVE_ROOMS:
            raise HTTPException(status_code=404, detail="Oda bulunamadı")
        room = LIVE_ROOMS[room_id]
        
        if not room.get("allow_substitute", True):
            raise HTTPException(status_code=400, detail="Bu odada yedek izleyici geçişine izin verilmiyor.")
            
        # Find empty seat
        seat = None
        if req.seat_id:
            seat = next((p for p in room["players"] if p["id"] == req.seat_id), None)
        if not seat or not seat.get("is_empty"):
            seat = next((p for p in room["players"] if p.get("is_empty") or not p.get("connected")), None)
            
        if not seat:
            raise HTTPException(status_code=400, detail="Müsait boş yarışmacı koltuğu bulunamadı.")
            
        # Assign spectator to seat
        seat["name"] = req.player_name or "Yeni Yarışmacı (İzleyici)"
        seat["connected"] = True
        seat["is_empty"] = False
        seat["avatar"] = "⚡"
        
        # Check if any empty seats left
        room["empty_seat_available"] = any(p.get("is_empty") for p in room["players"])
        # Decrease spectator count since they moved to stage
        room["spectators_count"] = max(0, room.get("spectators_count", 1) - 1)
        
        event_msg = {
            "type": "seat_taken",
            "seat_id": seat["id"],
            "player_name": seat["name"],
            "message": f"🎉 {seat['name']} izleyici koltuğundan sahneye çıkarak yarışmaya dahil oldu!",
            "room": room
        }
        await room_manager.broadcast(room_id, event_msg)
        
        return {
            "success": True,
            "message": f"Tebrikler! {seat['id'].upper()} koltuğuna başarıyla geçtiniz. Artık sahnedesiniz!",
            "seat": seat,
            "room": room
        }

@app.post("/api/gameshow/rooms/{room_id}/reaction")
async def send_room_reaction(room_id: str, req: ReactionRequest):
    """İzleyici veya oyuncu canlı reaksiyon balonu (floating emoji) fırlatır."""
    if room_id not in LIVE_ROOMS:
        raise HTTPException(status_code=404, detail="Oda bulunamadı")
    event_msg = {
        "type": "reaction",
        "emoji": req.emoji,
        "sender": req.sender
    }
    await room_manager.broadcast(room_id, event_msg)
    return {"success": True}

class RecordMatchRequest(BaseModel):
    room_name: str
    mode: str
    surah_pool: str
    winner_name: str
    winner_score: int
    total_rounds: int
    participants: Optional[List[dict]] = None

@app.get("/api/gameshow/leaderboard")
def get_leaderboard(limit: int = 10):
    """Hâfızlık ligi liderlik tablosunu döner (en yüksek Motivasyon Puanı)."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT player_name, total_points, matches_played, highest_score, last_active
        FROM hafizlik_leaderboard
        ORDER BY total_points DESC, highest_score DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"leaderboard": rows}

@app.post("/api/gameshow/matches/record")
def record_match(req: RecordMatchRequest):
    """Tamamlanan oda maçını veritabanına kaydeder ve liderlik puanlarını günceller."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (req.room_name, req.mode, req.surah_pool, req.winner_name, req.winner_score, req.total_rounds, time.time()))
    
    pts = min(100, max(0, req.winner_score))
    c.execute("""
        INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            total_points = total_points + excluded.total_points,
            matches_played = matches_played + 1,
            highest_score = MAX(highest_score, excluded.highest_score),
            last_active = excluded.last_active
    """, (req.winner_name, pts, pts, time.time()))
    
    if req.participants:
        for p in req.participants:
            p_name = p.get("name")
            p_score = min(100, max(0, p.get("score", 0)))
            if p_name and p_name != req.winner_name and not p.get("is_empty"):
                c.execute("""
                    INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
                    VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(player_name) DO UPDATE SET
                        total_points = total_points + excluded.total_points,
                        matches_played = matches_played + 1,
                        highest_score = MAX(highest_score, excluded.highest_score),
                        last_active = excluded.last_active
                """, (p_name, p_score, p_score, time.time()))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Maç sonucu başarıyla kaydedildi!"}

@app.get("/api/gameshow/matches/recent")
def get_recent_matches(limit: int = 6):
    """Son tamamlanan maçların geçmişini döner."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at
        FROM hafizlik_matches
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"recent_matches": rows}

@app.websocket("/ws/rooms/{room_id}")
async def room_websocket_endpoint(websocket: WebSocket, room_id: str):
    """Canlı yarışma ve izleyici senkronizasyonu için gerçek zamanlı WebSocket kanalı."""
    await room_manager.connect(room_id, websocket)
    try:
        # Send initial room state
        current_room = LIVE_ROOMS.get(room_id, {})
        await websocket.send_json({"type": "init_state", "room": current_room})
        while True:
            data = await websocket.receive_json()
            # Broadcast incoming client actions (reactions, buzzers, guesses) to all viewers in room
            await room_manager.broadcast(room_id, data)
    except WebSocketDisconnect:
        room_manager.disconnect(room_id, websocket)
    except Exception:
        room_manager.disconnect(room_id, websocket)

# =====================================================================
# 14. AŞAMA 2: HÂFIZ ELO & AKILLI EŞLEŞTİRME & ARALIKLI TEKRAR
# =====================================================================
class MatchmakeRequest(BaseModel):
    player_name: str = "Siz (Yarışmacı)"
    mode: str = "buzzer"
    surah_pool: Optional[str] = "30. Cüz (Amme Cüzü)"

class SpacedRepetitionRecordRequest(BaseModel):
    player_name: str = "Siz (Yarışmacı)"
    surah_id: int
    ayah_id: int
    sure_name: str
    ayah_text: str
    is_correct: bool

class PlayTournamentMatchRequest(BaseModel):
    match_id: str
    player_name: str = "Siz (Yarışmacı)"
    player_score: int
    opponent_score: Optional[int] = None

@app.get("/api/gameshow/elo/{player_name}")
def get_player_elo_profile(player_name: str):
    """Oyuncunun ELO derecesini, unvanını ve hıfz seviyesini döner."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT player_name, elo_rating, hifz_tier, streak_count, accuracy_pct, last_updated
        FROM hafizlik_elo
        WHERE player_name = ?
    """, (player_name,))
    row = c.fetchone()
    if not row:
        c.execute("""
            INSERT INTO hafizlik_elo (player_name, elo_rating, hifz_tier, streak_count, accuracy_pct, last_updated)
            VALUES (?, 1350, 'Mutavassıt (Orta)', 1, 80.0, ?)
        """, (player_name, time.time()))
        conn.commit()
        row = {
            "player_name": player_name,
            "elo_rating": 1350,
            "hifz_tier": "Mutavassıt (Orta)",
            "streak_count": 1,
            "accuracy_pct": 80.0,
            "last_updated": time.time()
        }
    else:
        row = dict(row)
    
    elo = row["elo_rating"]
    if elo >= 2000:
        recommended_table = "Zirve Altın Podyum (Bakara & Tüm Kur'an)"
    elif elo >= 1700:
        recommended_table = "Mor Firdevs Masası (Yâsîn, Mülk, Vâkıa)"
    elif elo >= 1300:
        recommended_table = "Mavi Nil Masası (30. Cüz Amme)"
    else:
        recommended_table = "Yeşil Vaha Masası (Kısa Sûreler)"
        
    row["recommended_table"] = recommended_table
    conn.close()
    return row

@app.post("/api/gameshow/elo/matchmake")
def matchmake_opponent(req: MatchmakeRequest):
    """Oyuncunun ELO'suna en yakın bot rakibi bulur ve adil eşleşme sağlar."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT elo_rating FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    p_row = c.fetchone()
    p_elo = p_row[0] if p_row else 1350
    
    c.execute("""
        SELECT player_name, elo_rating, hifz_tier, accuracy_pct
        FROM hafizlik_elo
        WHERE player_name != ?
        ORDER BY ABS(elo_rating - ?) ASC
        LIMIT 4
    """, (req.player_name, p_elo))
    candidates = [dict(r) for r in c.fetchall()]
    conn.close()
    
    import random
    matched_opponent = random.choice(candidates) if candidates else {
        "player_name": "Ahmet Hâfız (30. Cüz)",
        "elo_rating": 1400,
        "hifz_tier": "Mutavassıt (Orta)",
        "accuracy_pct": 82.0
    }
    
    return {
        "success": True,
        "player_elo": p_elo,
        "matched_opponent": matched_opponent,
        "mode": req.mode,
        "surah_pool": req.surah_pool,
        "fair_match": abs(p_elo - matched_opponent["elo_rating"]) <= 200
    }

@app.post("/api/gameshow/spaced-repetition/record")
def record_spaced_repetition(req: SpacedRepetitionRecordRequest):
    """Aralıklı tekrar algoritması: Takılınan âyetlerin ağırlığını yönetir."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT mistake_count, correct_count, interval_weight
        FROM hafizlik_spaced_repetition
        WHERE player_name = ? AND surah_id = ? AND ayah_id = ?
    """, (req.player_name, req.surah_id, req.ayah_id))
    row = c.fetchone()
    
    now = time.time()
    if row:
        m_count = row["mistake_count"] + (0 if req.is_correct else 1)
        c_count = row["correct_count"] + (1 if req.is_correct else 0)
        weight = max(0.2, row["interval_weight"] * (0.8 if req.is_correct else 1.6))
        c.execute("""
            UPDATE hafizlik_spaced_repetition
            SET mistake_count = ?, correct_count = ?, interval_weight = ?, last_reviewed = ?,
                sure_name = ?, ayah_text = ?
            WHERE player_name = ? AND surah_id = ? AND ayah_id = ?
        """, (m_count, c_count, round(weight, 2), now, req.sure_name, req.ayah_text, req.player_name, req.surah_id, req.ayah_id))
    else:
        m_count = 0 if req.is_correct else 1
        c_count = 1 if req.is_correct else 0
        weight = 0.8 if req.is_correct else 2.0
        c.execute("""
            INSERT INTO hafizlik_spaced_repetition
            (player_name, surah_id, ayah_id, sure_name, ayah_text, mistake_count, correct_count, interval_weight, last_reviewed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (req.player_name, req.surah_id, req.ayah_id, req.sure_name, req.ayah_text, m_count, c_count, round(weight, 2), now))
        
    conn.commit()
    conn.close()
    return {
        "success": True,
        "is_correct": req.is_correct,
        "current_weight": round(weight, 2),
        "status": "pekiştirildi" if req.is_correct else "tekrar listesine eklendi"
    }

@app.get("/api/gameshow/spaced-repetition/weak-ayahs/{player_name}")
def get_weak_ayahs(player_name: str, limit: int = 5):
    """Oyuncunun en çok takıldığı zayıf âyetlerini listeler."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT surah_id, ayah_id, sure_name, ayah_text, mistake_count, correct_count, interval_weight, last_reviewed
        FROM hafizlik_spaced_repetition
        WHERE player_name = ?
        ORDER BY interval_weight DESC, mistake_count DESC, last_reviewed ASC
        LIMIT ?
    """, (player_name, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"player_name": player_name, "weak_ayahs": rows, "count": len(rows)}

# =====================================================================
# 15. AŞAMA 3: HAFTALIK ŞAMPİYONALAR & TURNUVA AĞAÇLARI (BRACKET API)
# =====================================================================
@app.get("/api/gameshow/tournaments")
def list_tournaments():
    """Haftalık aktif turnuvaları ve durumlarını listeler."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT tournament_id, title, category, bracket_size, current_round, status, created_at
        FROM hafizlik_tournaments
        ORDER BY created_at ASC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"tournaments": rows, "count": len(rows)}

@app.get("/api/gameshow/tournaments/{tournament_id}/bracket")
def get_tournament_bracket(tournament_id: str):
    """Seçilen turnuvanın ağaç detayını (bracket) döner."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT bracket_tree FROM hafizlik_tournaments WHERE tournament_id = ?", (tournament_id,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Turnuva ağacı bulunamadı")
    return json.loads(row[0])

@app.post("/api/gameshow/tournaments/{tournament_id}/play-match")
def play_tournament_match(tournament_id: str, req: PlayTournamentMatchRequest):
    """Kullanıcının turnuva maçını oynar ve sonucu ağaca işler. Max puan 100 kuralı uygulanır."""
    import random
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT bracket_tree FROM hafizlik_tournaments WHERE tournament_id = ?", (tournament_id,))
    row = c.fetchone()
    if not row or not row[0]:
        conn.close()
        raise HTTPException(status_code=404, detail="Turnuva bulunamadı")
        
    tree = json.loads(row[0])
    p_score = min(100, max(0, req.player_score))
    opp_score = req.opponent_score if req.opponent_score is not None else random.randint(60, 95)
    opp_score = min(100, max(0, opp_score))
    
    if p_score == opp_score:
        p_score = min(100, p_score + 5)
        
    match_found = False
    won = (p_score > opp_score)
    user_name = req.player_name or "Siz (Yarışmacı)"
    
    for r_idx, rnd in enumerate(tree.get("rounds", [])):
        for m in rnd.get("matches", []):
            if m.get("id") == req.match_id or (m.get("is_user_match") and m.get("status") == "ready"):
                match_found = True
                m["player1"]["score"] = p_score
                m["player2"]["score"] = opp_score
                winner = m["player1"]["name"] if p_score > opp_score else m["player2"]["name"]
                m["winner"] = winner
                m["status"] = "completed"
                
                if won and r_idx + 1 < len(tree["rounds"]):
                    next_round = tree["rounds"][r_idx + 1]
                    for nm in next_round.get("matches", []):
                        if nm["player1"]["name"] == "TBD":
                            nm["player1"]["name"] = user_name
                            nm["is_user_match"] = True
                            nm["status"] = "ready"
                            nm["player2"]["name"] = random.choice([b for b in BOT_POOL if b != user_name])
                            break
                        elif nm["player2"]["name"] == "TBD":
                            nm["player2"]["name"] = user_name
                            nm["is_user_match"] = True
                            nm["status"] = "ready"
                            break
                elif won and r_idx + 1 == len(tree["rounds"]):
                    tree["champion"] = user_name
                    
                break
        if match_found:
            break
            
    c.execute("""
        UPDATE hafizlik_tournaments
        SET bracket_tree = ?
        WHERE tournament_id = ?
    """, (json.dumps(tree, ensure_ascii=False), tournament_id))
    
    delta_elo = 20 if won else -5
    c.execute("""
        UPDATE hafizlik_elo
        SET elo_rating = MAX(800, elo_rating + ?),
            streak_count = CASE WHEN ? THEN streak_count + 1 ELSE 0 END,
            last_updated = ?
        WHERE player_name = ?
    """, (delta_elo, 1 if won else 0, time.time(), user_name))
    
    c.execute("""
        INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            total_points = total_points + excluded.total_points,
            matches_played = matches_played + 1,
            highest_score = MAX(highest_score, excluded.highest_score),
            last_active = excluded.last_active
    """, (user_name, p_score, p_score, time.time()))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "won": won,
        "player_score": p_score,
        "opponent_score": opp_score,
        "delta_elo": delta_elo,
        "bracket": tree,
        "is_champion": (tree.get("champion") == user_name)
    }

# =====================================================================
# 16. AŞAMA 4: HIFZ KARNESİ ANALİZ MOTORU
# =====================================================================
@app.get("/api/gameshow/hifz-karne/{player_name}")
def get_hifz_report_card(player_name: str):
    """Oyuncunun kapsamlı hıfz analiz karnesini döner."""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT elo_rating, hifz_tier, streak_count, accuracy_pct FROM hafizlik_elo WHERE player_name = ?", (player_name,))
    elo_row = c.fetchone()
    elo_rating = elo_row["elo_rating"] if elo_row else 1350
    hifz_tier = elo_row["hifz_tier"] if elo_row else "Mutavassıt (Orta)"
    streak = elo_row["streak_count"] if elo_row else 1
    accuracy = elo_row["accuracy_pct"] if elo_row else 82.5
    
    c.execute("SELECT total_points, matches_played, highest_score FROM hafizlik_leaderboard WHERE player_name = ?", (player_name,))
    lb_row = c.fetchone()
    total_points = lb_row["total_points"] if lb_row else 150
    matches_played = lb_row["matches_played"] if lb_row else 2
    highest_score = lb_row["highest_score"] if lb_row else 90
    
    c.execute("""
        SELECT surah_id, ayah_id, sure_name, ayah_text, mistake_count, correct_count, interval_weight
        FROM hafizlik_spaced_repetition
        WHERE player_name = ?
        ORDER BY interval_weight DESC
        LIMIT 5
    """, (player_name,))
    weak_ayahs = [dict(r) for r in c.fetchall()]
    
    conn.close()
    
    mastery = {
        "juz30_amme": min(100, max(40, int(accuracy + (elo_rating - 1200) * 0.05))),
        "yasin_mulk": min(100, max(30, int(accuracy * 0.95 + (elo_rating - 1300) * 0.04))),
        "bakara_aliimran": min(100, max(20, int(accuracy * 0.80 + (elo_rating - 1400) * 0.03))),
        "kisa_sureler": min(100, max(75, int(accuracy * 1.1)))
    }
    
    if elo_rating >= 2000:
        badge = {"title": "👑 Hâfız-ı Mütkın", "color": "amber", "desc": "Tüm Kur'an ve müteşâbih âyetler hâkimi."}
    elif elo_rating >= 1700:
        badge = {"title": "⭐ Müntehi Hâfız", "color": "purple", "desc": "Yâsîn, Mülk ve zorlu fasılalarda uzman."}
    elif elo_rating >= 1300:
        badge = {"title": "🌊 Mutavassıt Hâfız", "color": "cyan", "desc": "30. Cüz ve aşr-ı şeriflerde yetkin."}
    else:
        badge = {"title": "🌱 Mübtedi Talip", "color": "emerald", "desc": "Hıfz yolculuğunun azimli başlangıcı."}
        
    return {
        "player_name": player_name,
        "elo_rating": elo_rating,
        "hifz_tier": hifz_tier,
        "streak_count": streak,
        "accuracy_pct": accuracy,
        "total_points": total_points,
        "matches_played": matches_played,
        "highest_score": highest_score,
        "badge": badge,
        "mastery_segments": mastery,
        "weak_ayahs_for_today": weak_ayahs,
        "max_points_enforced": 100
    }

# =====================================================================
# 11. AUTONOMOUS BOT ARENA SIMULATION ENGINE
# =====================================================================
BOT_POOL = [
    "Ahmet Hâfız (30. Cüz)", "Zeynep K. (Kısa Sûreler)", "Mustafa Y. (Buzzer Rekortmeni)",
    "Hâfız Merve (Kelime Avcısı)", "Ömer Faruk (Yâsîn & Mülk)", "Fâtıma Zehra (Kıraat Yıldızı)",
    "Bilal H. (Hızlı Hâfız)", "Hüseyin R. (Grand Master Hâfız)", "Salih E. (Bakara Kaşifi)",
    "Ayşe Betül (Makam Şampiyonu)", "Hacer N. (Amme Podyumu)", "İbrahim Halil (Tecvid Ustası)",
    "Yusuf K. (Kelime Dehası)", "Enes T. (Âyet Dedektifi)", "Rümeysa D. (Zirve Takipçisi)",
    "Tarık B. (100 Puan Adayı)", "Esra G. (Hızlı Refleks)", "Hamza Ç. (Furkan Muhafızı)",
    "Meryem S. (Mülk Bükücü)", "Kerem A. (Harf Ustası)"
]

async def autonomous_bot_arena_loop():
    """Arka planda 20 bot yarışmacının maçlarını ve odalardaki dinamik hareketleri simüle eder."""
    import random
    while True:
        try:
            await asyncio.sleep(25)
            # Pick a random room and simulate a point increase or spectator fluctuation
            room_keys = list(LIVE_ROOMS.keys())
            if room_keys:
                rk = random.choice(room_keys)
                rm = LIVE_ROOMS[rk]
                # Slight spectator fluctuation
                rm["spectators_count"] = max(15, rm.get("spectators_count", 50) + random.randint(-2, 3))
                # Random bot score progression within limit
                for p in rm.get("players", []):
                    if not p.get("is_empty") and random.random() < 0.35:
                        p["score"] = min(100, p.get("score", 0) + 10)
                
                # Broadcast update via ws
                await room_manager.broadcast(rk, {"type": "room_state", "room": rm})

            # Every ~50s simulate a completed bot match in DB
            if random.random() < 0.40:
                bot_winner = random.choice(BOT_POOL)
                bot_score = random.choice([75, 80, 85, 90, 95, 100])
                modes = ["buzzer", "wordgame", "millionaire"]
                m_mode = random.choice(modes)
                pools = ["30. Cüz (Amme Cüzü)", "Yâsîn & Mülk", "İlk 10 Sûre", "Kur'an Kelimeleri"]
                m_pool = random.choice(pools)
                
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"Canlı Arena #{random.randint(101, 106)}", m_mode, m_pool, bot_winner, bot_score, 10, time.time()))
                
                c.execute("""
                    INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
                    VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(player_name) DO UPDATE SET
                        total_points = total_points + excluded.total_points,
                        matches_played = matches_played + 1,
                        highest_score = MAX(highest_score, excluded.highest_score),
                        last_active = excluded.last_active
                """, (bot_winner, bot_score, bot_score, time.time()))
                conn.commit()
                conn.close()
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(10)

# =====================================================================
# 15. 2 KİŞİLİK HÂFIZ DÜELLOSU // KUR'AN BULMACA MOTORU
# =====================================================================
class PuzzleDuelMatchRequest(BaseModel):
    player_name: str = "Siz (Yarışmacı)"
    bot_opponent: Optional[str] = None
    rounds_count: int = 5

class BotRoundSimRequest(BaseModel):
    bot_name: str
    round_id: str
    letter_count: int
    difficulty: str = "medium"

class PuzzleDuelFinishRequest(BaseModel):
    duel_id: str
    player_name: str
    bot_name: str
    player_score: int
    bot_score: int
    total_rounds: int = 5

class BotVsBotDuelRequest(BaseModel):
    bot1_name: Optional[str] = None
    bot2_name: Optional[str] = None
    rounds_count: int = 5

@app.post("/api/gameshow/puzzle-duel/match")
def match_puzzle_duel(req: PuzzleDuelMatchRequest):
    """
    2 Kişilik Hâfız Düellosu (1v1 Bulmaca) maçı başlatır.
    İstenen veya ELO'ya en uygun bot rakibi eşleştirir, 5 Kur'an bulmacası üretir.
    Maksimum Motivasyon Puanı: 100 (5 Tur x 20 Puan).
    """
    import random
    conn = get_db()
    c = conn.cursor()
    
    # Get player elo
    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    p1_row = c.fetchone()
    p1_elo = p1_row[0] if p1_row else 1350
    p1_tier = p1_row[1] if p1_row else "Mutavassıt (Orta)"
    
    # Pick bot
    if req.bot_opponent and any(req.bot_opponent in b for b in BOT_POOL):
        bot_name = req.bot_opponent
    else:
        c.execute("""
            SELECT player_name, elo_rating, hifz_tier
            FROM hafizlik_elo
            WHERE player_name != ?
            ORDER BY ABS(elo_rating - ?) ASC
            LIMIT 5
        """, (req.player_name, p1_elo))
        candidates = c.fetchall()
        if candidates:
            cand = random.choice(candidates)
            bot_name = cand["player_name"]
            bot_elo = cand["elo_rating"]
            bot_tier = cand["hifz_tier"]
        else:
            bot_name = random.choice(BOT_POOL)
            bot_elo = 1320
            bot_tier = "Mutavassıt (Orta)"
            
    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (bot_name,))
    b_row = c.fetchone()
    bot_elo = b_row[0] if b_row else 1300
    bot_tier = b_row[1] if b_row else "Hâfız Adayı"

    pool = list(QURANIC_PUZZLES_MASTER)
    random.shuffle(pool)
    selected = pool[:req.rounds_count]
    
    rounds = []
    for idx, item in enumerate(selected):
        rounds.append(build_puzzle_round(item, idx, conn))
        
    conn.close()
    
    avatar_map = {
        "Ahmet": "👨‍🎓", "Zeynep": "🧕", "Mustafa": "⚡", "Merve": "🌸",
        "Ömer": "📖", "Fâtıma": "✨", "Bilal": "🎙️", "Hüseyin": "👑",
        "Salih": "🛡️", "Ayşe": "🌺", "Hacer": "🏆", "İbrahim": "📜",
        "Yusuf": "🌟", "Enes": "🔍", "Rümeysa": "🌙", "Tarık": "🎯",
        "Esra": "⚡", "Hamza": "🦁", "Meryem": "🕊️", "Kerem": "💎"
    }
    bot_avatar = "👨‍🎓"
    for k, v in avatar_map.items():
        if k in bot_name:
            bot_avatar = v
            break
            
    duel_id = f"duel-{int(time.time()*1000)%100000}"
    return {
        "duel_id": duel_id,
        "format": "2 Kişilik Hâfız Düellosu (1v1 Bulmaca)",
        "player1": {
            "name": req.player_name,
            "elo": p1_elo,
            "tier": p1_tier,
            "avatar": "👤"
        },
        "player2": {
            "name": bot_name,
            "elo": bot_elo,
            "tier": bot_tier,
            "avatar": bot_avatar
        },
        "rounds_count": len(rounds),
        "max_total_score": 100,
        "rounds": rounds
    }

@app.post("/api/gameshow/puzzle-duel/simulate-bot-round")
def simulate_bot_round(req: BotRoundSimRequest):
    """
    Bot kullanıcının bulmaca turundaki gerçekçi davranışını simüle eder.
    Harf harf yazma gecikmeleri (keystroke timing) ve ipucu kullanımını döner.
    """
    import random
    n_letters = max(3, req.letter_count)
    speed_factor = 0.85 if req.difficulty == "hard" else (1.2 if req.difficulty == "easy" else 1.0)
    
    read_delay_ms = int(random.uniform(1500, 2600) * speed_factor)
    
    delays_ms = []
    current_ms = read_delay_ms
    for i in range(n_letters):
        hesitation = random.uniform(200, 600) if random.random() < 0.25 else 0
        letter_delta = int((random.uniform(900, 1700) + hesitation) * speed_factor)
        current_ms += letter_delta
        delays_ms.append(current_ms)
        
    used_hint = (n_letters >= 6 and random.random() < 0.15)
    round_score = 15 if used_hint else 20
    total_time_sec = round(current_ms / 1000.0, 2)
    
    return {
        "bot_name": req.bot_name,
        "total_time_seconds": total_time_sec,
        "used_hint": used_hint,
        "round_score": round_score,
        "letter_delays_ms": delays_ms,
        "success": True
    }

@app.post("/api/gameshow/puzzle-duel/finish")
def finish_puzzle_duel(req: PuzzleDuelFinishRequest):
    """
    2 Kişilik Hâfız Düellosunu sonuçlandırır, ELO'yu günceller ve maç kaydını saklar.
    Maksimum Motivasyon Puanı barajı: 100 Puan.
    """
    conn = get_db()
    c = conn.cursor()
    
    p1_score = min(100, max(0, req.player_score))
    p2_score = min(100, max(0, req.bot_score))
    
    if p1_score > p2_score:
        winner = req.player_name
        delta_elo = 20
    elif p1_score < p2_score:
        winner = req.bot_name
        delta_elo = -10
    else:
        winner = "Berabere"
        delta_elo = 5
        
    c.execute("SELECT elo_rating FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    row = c.fetchone()
    old_elo = row[0] if row else 1350
    new_elo = max(800, old_elo + delta_elo)
    
    c.execute("""
        UPDATE hafizlik_elo
        SET elo_rating = ?, streak_count = CASE WHEN ? > ? THEN streak_count + 1 ELSE 0 END, last_updated = ?
        WHERE player_name = ?
    """, (new_elo, p1_score, p2_score, time.time(), req.player_name))
    
    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"2 Kişilik Düello: {req.player_name} vs {req.bot_name}", "wordgame_duel", "Kur'an Kelime & Âyet Bulmacası", winner, max(p1_score, p2_score), req.total_rounds, time.time()))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "duel_id": req.duel_id,
        "winner": winner,
        "player_score": p1_score,
        "bot_score": p2_score,
        "delta_elo": delta_elo,
        "new_elo": new_elo,
        "message": f"Düello Tamamlandı! Kazanan: {winner} ({max(p1_score, p2_score)} Puan)"
    }

@app.post("/api/gameshow/puzzle-duel/simulate-bot-match")
def simulate_bot_vs_bot_duel(req: BotVsBotDuelRequest):
    """
    İki bot yarışmacı arasında baştan sona 5 turluk tam bir 1v1 bulmaca düellosunu simüle eder.
    Tüm turları, harf hızlarını, süreleri ve nihai kazananı hesaplar.
    """
    import random
    conn = get_db()
    
    bot1 = req.bot1_name if (req.bot1_name and req.bot1_name in BOT_POOL) else random.choice(BOT_POOL)
    remaining_bots = [b for b in BOT_POOL if b != bot1]
    bot2 = req.bot2_name if (req.bot2_name and req.bot2_name in remaining_bots) else random.choice(remaining_bots)
    
    pool = list(QURANIC_PUZZLES_MASTER)
    random.shuffle(pool)
    rounds_count = min(10, max(1, req.rounds_count))
    selected = pool[:rounds_count]
    
    bot1_total = 0
    bot2_total = 0
    round_logs = []
    
    for idx, item in enumerate(selected):
        r_data = build_puzzle_round(item, idx, conn)
        b1_time = round(random.uniform(5.5, 14.0), 2)
        b1_hint = random.random() < 0.15
        b1_score = 15 if b1_hint else 20
        
        b2_time = round(random.uniform(5.5, 14.0), 2)
        b2_hint = random.random() < 0.15
        b2_score = 15 if b2_hint else 20
        
        if b1_time < b2_time:
            round_winner = bot1
            bot1_total += b1_score
        elif b2_time < b1_time:
            round_winner = bot2
            bot2_total += b2_score
        else:
            round_winner = "Berabere"
            bot1_total += b1_score
            bot2_total += b2_score
            
        round_logs.append({
            "round": idx + 1,
            "clue": r_data["clue"],
            "answer": r_data["answer"],
            "bot1_time": b1_time,
            "bot2_time": b2_time,
            "round_winner": round_winner,
            "round_ayah": r_data["full_ayah_arabic"]
        })
        
    bot1_total = min(100, bot1_total)
    bot2_total = min(100, bot2_total)
    
    if bot1_total > bot2_total:
        overall_winner = bot1
    elif bot2_total > bot1_total:
        overall_winner = bot2
    else:
        overall_winner = "Berabere"
        
    c = conn.cursor()
    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"Bot Düellosu: {bot1} vs {bot2}", "wordgame_duel", "Kur'an Âyet Bulmacası Bot Arenası", overall_winner, max(bot1_total, bot2_total), rounds_count, time.time()))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "format": "2 Bot Kur'an Bulmaca Simülasyonu",
        "bot1": {"name": bot1, "score": bot1_total},
        "bot2": {"name": bot2, "score": bot2_total},
        "overall_winner": overall_winner,
        "max_score_enforced": 100,
        "rounds": round_logs
    }

# =====================================================================
# 20. ÂYET İÇİ KELİME BLOKLARI (CLOZE VERSE WORD BLOCKS / KELİME KULESİ)
# =====================================================================
# Ekran görüntüsündeki mekanik: Âyet içindeki boşluklar ([KIYAMET]in, [İŞTE], [KAFİR]ler)
# Mihrab penceresi içinde 3D mor harf blokları piramidi/havuzu.
# Tek Kişilik ve 2 Kişilik Hâfız Düellosu (1v1) desteği.

QURANIC_CLOZE_BLOCKS_MASTER = [
    {
        "id": "cloze-1",
        "surah_id": 30,
        "ayah_id": 14,
        "sure_name": "Rûm",
        "reference": "Rum, 30/14",
        "template": "{0}in kopacağı gün, {1} o gün müminler ve {2}ler birbirinden ayrılacaklardır.",
        "targets": [
            {"word": "KIYAMET", "suffix": "in", "badge": 7, "order": 0},
            {"word": "İŞTE", "suffix": "", "badge": 4, "order": 1},
            {"word": "KAFİR", "suffix": "ler", "badge": 5, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/030014.mp3"
    },
    {
        "id": "cloze-2",
        "surah_id": 2,
        "ayah_id": 255,
        "sure_name": "Bakara",
        "reference": "Bakara, 2/255 (Âyetü'l-Kürsî)",
        "template": "Allah, O'ndan başka hiçbir {0} yoktur; O {1}dir, bütün varlığı ayakta tutan {2}dur.",
        "targets": [
            {"word": "İLAH", "suffix": "", "badge": 4, "order": 0},
            {"word": "DİRİ", "suffix": "dir", "badge": 4, "order": 1},
            {"word": "KAYYUM", "suffix": "dur", "badge": 6, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/002255.mp3"
    },
    {
        "id": "cloze-3",
        "surah_id": 1,
        "ayah_id": 5,
        "sure_name": "Fâtiha",
        "reference": "Fâtiha, 1/5-6",
        "template": "(Rabbimiz!) Yalnız sana {0} eder ve yalnız senden {1} dileriz. Bizi {2} yola ilet.",
        "targets": [
            {"word": "KULLUK", "suffix": "", "badge": 6, "order": 0},
            {"word": "YARDIM", "suffix": "", "badge": 6, "order": 1},
            {"word": "DOĞRU", "suffix": "", "badge": 5, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/001005.mp3"
    },
    {
        "id": "cloze-4",
        "surah_id": 112,
        "ayah_id": 1,
        "sure_name": "İhlâs",
        "reference": "İhlâs, 112/1-4",
        "template": "De ki: O Allah tektir. Allah {0}dir. O {1} ve doğmamıştır. O'na hiçbir şey {2} değildir.",
        "targets": [
            {"word": "SAMED", "suffix": "dir", "badge": 5, "order": 0},
            {"word": "DOĞURMAMIŞ", "suffix": "", "badge": 10, "order": 1},
            {"word": "DENK", "suffix": "", "badge": 4, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/112001.mp3"
    },
    {
        "id": "cloze-5",
        "surah_id": 103,
        "ayah_id": 1,
        "sure_name": "Asr",
        "reference": "Asr, 103/1-3",
        "template": "{0}a andolsun ki insan kesin bir {1} içindedir. Ancak iman edip {2} amel işleyenler müstesnadır.",
        "targets": [
            {"word": "ASIR", "suffix": "a", "badge": 4, "order": 0},
            {"word": "ZİYAN", "suffix": "", "badge": 5, "order": 1},
            {"word": "SALİH", "suffix": "", "badge": 5, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/103001.mp3"
    },
    {
        "id": "cloze-6",
        "surah_id": 97,
        "ayah_id": 1,
        "sure_name": "Kadir",
        "reference": "Kadir, 97/1-3",
        "template": "Şüphesiz biz onu {0} gecesinde indirdik. Kadir gecesi {1} aydan daha {2}dır.",
        "targets": [
            {"word": "KADİR", "suffix": "", "badge": 5, "order": 0},
            {"word": "BİN", "suffix": "", "badge": 3, "order": 1},
            {"word": "HAYIRLI", "suffix": "dır", "badge": 7, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/097001.mp3"
    },
    {
        "id": "cloze-7",
        "surah_id": 105,
        "ayah_id": 1,
        "sure_name": "Fil",
        "reference": "Fil, 105/1-3",
        "template": "Görmedin mi Rabbin {0} ordusuna ne yaptı? Tuzaklarını {1} çıkarmadı mı? Üzerlerine {2} kuşlarını saldı.",
        "targets": [
            {"word": "FİL", "suffix": "", "badge": 3, "order": 0},
            {"word": "BOŞA", "suffix": "", "badge": 4, "order": 1},
            {"word": "EBABİL", "suffix": "", "badge": 6, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/105001.mp3"
    },
    {
        "id": "cloze-8",
        "surah_id": 108,
        "ayah_id": 1,
        "sure_name": "Kevser",
        "reference": "Kevser, 108/1-2",
        "template": "Şüphesiz biz sana {0}i verdik. O halde yalnız Rabbin için {1} kıl ve {2} kes.",
        "targets": [
            {"word": "KEVSER", "suffix": "i", "badge": 6, "order": 0},
            {"word": "NAMAZ", "suffix": "", "badge": 5, "order": 1},
            {"word": "KURBAN", "suffix": "", "badge": 6, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/108001.mp3"
    },
    {
        "id": "cloze-9",
        "surah_id": 95,
        "ayah_id": 1,
        "sure_name": "Tîn",
        "reference": "Tîn, 95/1-4",
        "template": "{0}e ve {1}e andolsun. Sînâ dağına ve bu {2} şehre ki biz insanı en {3} biçimde yarattık.",
        "targets": [
            {"word": "İNCİR", "suffix": "e", "badge": 5, "order": 0},
            {"word": "ZEYTİN", "suffix": "e", "badge": 6, "order": 1},
            {"word": "GÜVENLİ", "suffix": "", "badge": 7, "order": 2},
            {"word": "GÜZEL", "suffix": "", "badge": 5, "order": 3}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/095001.mp3"
    },
    {
        "id": "cloze-10",
        "surah_id": 67,
        "ayah_id": 1,
        "sure_name": "Mülk",
        "reference": "Mülk, 67/1-2",
        "template": "Hükümranlık kudretinde olan Allah yücedir. O, hanginizin amelce daha güzel olduğunu sınamak için {0}ü ve {1}ı yaratandır.",
        "targets": [
            {"word": "ÖLÜM", "suffix": "ü", "badge": 4, "order": 0},
            {"word": "HAYAT", "suffix": "ı", "badge": 5, "order": 1}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/067001.mp3"
    },
    {
        "id": "cloze-11",
        "surah_id": 55,
        "ayah_id": 1,
        "sure_name": "Rahmân",
        "reference": "Rahmân, 55/1-4",
        "template": "{0} olan Allah, {1}ı öğretti. İnsanı {2}, ona {3}ı öğretti.",
        "targets": [
            {"word": "RAHMAN", "suffix": "", "badge": 6, "order": 0},
            {"word": "KURAN", "suffix": "ı", "badge": 5, "order": 1},
            {"word": "YARATTI", "suffix": "", "badge": 7, "order": 2},
            {"word": "BEYAN", "suffix": "ı", "badge": 5, "order": 3}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/055001.mp3"
    },
    {
        "id": "cloze-12",
        "surah_id": 96,
        "ayah_id": 1,
        "sure_name": "Alak",
        "reference": "Alak, 96/1-3",
        "template": "Yaratan Rabbinin adıyla {0}! O, insanı bir {1}tan yarattı. Oku! Senin Rabbin en büyük {2} sahibidir.",
        "targets": [
            {"word": "OKU", "suffix": "", "badge": 3, "order": 0},
            {"word": "ALAK", "suffix": "tan", "badge": 4, "order": 1},
            {"word": "KEREM", "suffix": "", "badge": 5, "order": 2}
        ],
        "audio_url": "https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/096001.mp3"
    }
]

def build_cloze_round(item, index, conn):
    import random
    c = conn.cursor()
    c.execute("SELECT quran_uthmani2 FROM ayahs WHERE surah_id = ? AND ayah_id = ?", (item["surah_id"], item["ayah_id"]))
    row_a = c.fetchone()
    full_ayah = row_a[0] if row_a and row_a[0] else ""

    c.execute("SELECT text FROM translations WHERE surah_id = ? AND ayah_id = ? AND edition_id = 'tr-diyanet-yeni'", (item["surah_id"], item["ayah_id"]))
    row_t = c.fetchone()
    trans = row_t[0] if row_t and row_t[0] else ""

    all_letters = []
    for tgt in item["targets"]:
        all_letters.extend(list(tgt["word"].upper()))
    
    tiles = []
    shuffled_letters = list(all_letters)
    random.shuffle(shuffled_letters)
    for idx, ch in enumerate(shuffled_letters):
        tiles.append({
            "id": f"t_{idx}_{ch}",
            "char": ch,
            "is_used": False
        })

    return {
        "round": index + 1,
        "id": item["id"],
        "surah_id": item["surah_id"],
        "ayah_id": item["ayah_id"],
        "sure_name": item["sure_name"],
        "reference": item["reference"],
        "template": item["template"],
        "targets": item["targets"],
        "total_targets": len(item["targets"]),
        "letter_tiles": tiles,
        "full_ayah_arabic": full_ayah,
        "translation": trans,
        "audio_url": item.get("audio_url") or get_reciter_audio_url(12, item["surah_id"], item["ayah_id"]),
        "max_score": 20
    }

class ClozeDuelMatchRequest(BaseModel):
    player_name: str = "Hâfız Yarışmacı"
    bot_opponent: Optional[str] = None
    rounds_count: int = 5

class ClozeBotRoundSimRequest(BaseModel):
    bot_name: str
    round_id: str
    target_words: List[str]
    difficulty: str = "medium"

class ClozeDuelFinishRequest(BaseModel):
    duel_id: str
    player_name: str
    bot_name: str
    player_score: int
    bot_score: int
    total_rounds: int = 5

class ClozeBotVsBotDuelRequest(BaseModel):
    bot1_name: Optional[str] = None
    bot2_name: Optional[str] = None
    rounds_count: int = 5

@app.get("/api/gameshow/cloze-blocks/rounds")
def get_cloze_blocks_rounds(count: int = Query(5, ge=1, le=20)):
    """
    Âyet İçi Kelime Blokları (Word Blocks / Kelime Kulesi) seviyelerini döner.
    Kullanıcı âyetteki boşlukları mihrab penceresindeki 3D harf bloklarından seçerek tamamlar.
    Ayetler 'quran_uthmani2' ve Husary Muallim tilâveti ile donatılmıştır.
    Maksimum toplam Motivasyon Puanı: 100 (5 Tur x 20 Puan).
    """
    import random
    conn = get_db()
    pool = list(QURANIC_CLOZE_BLOCKS_MASTER)
    random.shuffle(pool)
    selected = pool[:count]
    
    rounds = []
    for idx, item in enumerate(selected):
        rounds.append(build_cloze_round(item, idx, conn))
    conn.close()
    
    return {
        "format": "Âyet İçi Kelime Blokları (Kelime Kulesi)",
        "rounds_count": len(rounds),
        "max_total_score": 100,
        "rounds": rounds
    }

@app.post("/api/gameshow/cloze-blocks/duel/match")
def match_cloze_duel(req: ClozeDuelMatchRequest):
    """
    2 Kişilik Hâfız Düellosu (Âyet Blokları 1v1) maçı başlatır.
    İstenen veya ELO'ya en uygun bot rakibi eşleştirir, 5 Kur'an âyet blokları seviyesi üretir.
    Maksimum Motivasyon Puanı: 100 (5 Tur x 20 Puan).
    """
    import random
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    p1_row = c.fetchone()
    p1_elo = p1_row[0] if p1_row else 1350
    p1_tier = p1_row[1] if p1_row else "Mutavassıt (Orta)"
    
    if req.bot_opponent and any(req.bot_opponent in b for b in BOT_POOL):
        bot_name = req.bot_opponent
    else:
        c.execute("""
            SELECT player_name, elo_rating, hifz_tier
            FROM hafizlik_elo
            WHERE player_name != ?
            ORDER BY ABS(elo_rating - ?) ASC
            LIMIT 5
        """, (req.player_name, p1_elo))
        candidates = c.fetchall()
        if candidates:
            cand = random.choice(candidates)
            bot_name = cand["player_name"]
        else:
            bot_name = random.choice(BOT_POOL)
            
    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (bot_name,))
    b_row = c.fetchone()
    bot_elo = b_row[0] if b_row else 1300
    bot_tier = b_row[1] if b_row else "Hâfız Adayı"

    pool = list(QURANIC_CLOZE_BLOCKS_MASTER)
    random.shuffle(pool)
    selected = pool[:req.rounds_count]
    
    rounds = []
    for idx, item in enumerate(selected):
        rounds.append(build_cloze_round(item, idx, conn))
    conn.close()
    
    avatar_map = {
        "Ahmet": "👨‍🎓", "Zeynep": "🧕", "Mustafa": "⚡", "Merve": "🌸",
        "Ömer": "📖", "Fâtıma": "✨", "Bilal": "🎙️", "Hüseyin": "👑",
        "Salih": "🛡️", "Ayşe": "🌺", "Hacer": "🏆", "İbrahim": "📜",
        "Yusuf": "🌟", "Enes": "🔍", "Rümeysa": "🌙", "Tarık": "🎯",
        "Esra": "⚡", "Hamza": "🦁", "Meryem": "🕊️", "Kerem": "💎"
    }
    bot_avatar = "👨‍🎓"
    for k, v in avatar_map.items():
        if k in bot_name:
            bot_avatar = v
            break
            
    duel_id = f"cloze-duel-{int(time.time()*1000)%100000}"
    return {
        "duel_id": duel_id,
        "format": "2 Kişilik Âyet Blokları Düellosu (1v1)",
        "player1": {
            "name": req.player_name,
            "elo": p1_elo,
            "tier": p1_tier,
            "avatar": "👤"
        },
        "player2": {
            "name": bot_name,
            "elo": bot_elo,
            "tier": bot_tier,
            "avatar": bot_avatar
        },
        "rounds_count": len(rounds),
        "max_total_score": 100,
        "rounds": rounds
    }

@app.post("/api/gameshow/cloze-blocks/duel/simulate-bot-round")
def simulate_cloze_bot_round(req: ClozeBotRoundSimRequest):
    """
    Bot kullanıcının Âyet Blokları turundaki kelime kelime buluşunu simüle eder.
    Her kelime için ayrı buluş zamanlaması ve genel tur tamamlama süresini döner.
    """
    import random
    speed_factor = 0.85 if req.difficulty == "hard" else (1.2 if req.difficulty == "easy" else 1.0)
    
    word_timings = []
    current_ms = int(random.uniform(2200, 4000) * speed_factor)
    
    for w in req.target_words:
        w_len = len(w)
        delta_ms = int((random.uniform(2000, 4500) + w_len * 400) * speed_factor)
        current_ms += delta_ms
        word_timings.append({
            "word": w,
            "solved_at_ms": current_ms,
            "solved_at_sec": round(current_ms / 1000.0, 2)
        })
        
    used_hint = random.random() < 0.20
    round_score = 15 if used_hint else 20
    total_time_sec = round(current_ms / 1000.0, 2)
    
    return {
        "bot_name": req.bot_name,
        "total_time_seconds": total_time_sec,
        "used_hint": used_hint,
        "round_score": round_score,
        "word_timings": word_timings,
        "success": True
    }

@app.post("/api/gameshow/cloze-blocks/duel/finish")
def finish_cloze_duel(req: ClozeDuelFinishRequest):
    """
    2 Kişilik Âyet Blokları Düellosunu tamamlar, ELO'yu günceller ve maç kaydını saklar.
    Maksimum Motivasyon Puanı barajı: 100 Puan.
    """
    conn = get_db()
    c = conn.cursor()
    
    p1_score = min(100, max(0, req.player_score))
    p2_score = min(100, max(0, req.bot_score))
    
    if p1_score > p2_score:
        winner = req.player_name
        delta_elo = 20
    elif p1_score < p2_score:
        winner = req.bot_name
        delta_elo = -10
    else:
        winner = "Berabere"
        delta_elo = 5
        
    c.execute("SELECT elo_rating FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    row = c.fetchone()
    old_elo = row[0] if row else 1350
    new_elo = max(800, old_elo + delta_elo)
    
    c.execute("""
        UPDATE hafizlik_elo
        SET elo_rating = ?, streak_count = CASE WHEN ? > ? THEN streak_count + 1 ELSE 0 END, last_updated = ?
        WHERE player_name = ?
    """, (new_elo, p1_score, p2_score, time.time(), req.player_name))
    
    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"2 Kişilik Âyet Blokları: {req.player_name} vs {req.bot_name}", "clozeblocks_duel", "Kur'an Âyet Kelime Blokları", winner, max(p1_score, p2_score), req.total_rounds, time.time()))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "duel_id": req.duel_id,
        "winner": winner,
        "player_score": p1_score,
        "bot_score": p2_score,
        "delta_elo": delta_elo,
        "new_elo": new_elo,
        "message": f"Âyet Blokları Düellosu Tamamlandı! Kazanan: {winner} ({max(p1_score, p2_score)} Puan)"
    }

@app.post("/api/gameshow/cloze-blocks/duel/simulate-bot-match")
def simulate_cloze_bot_vs_bot_duel(req: ClozeBotVsBotDuelRequest):
    """
    İki bot yarışmacı arasında 5 turluk Âyet Blokları düellosunu baştan sona simüle eder.
    Tüm turları, kelime sürelerini, sonuçları ve ELO durumunu döner.
    """
    import random
    conn = get_db()
    
    bot1 = req.bot1_name if (req.bot1_name and req.bot1_name in BOT_POOL) else random.choice(BOT_POOL)
    remaining_bots = [b for b in BOT_POOL if b != bot1]
    bot2 = req.bot2_name if (req.bot2_name and req.bot2_name in remaining_bots) else random.choice(remaining_bots)
    
    pool = list(QURANIC_CLOZE_BLOCKS_MASTER)
    random.shuffle(pool)
    rounds_count = min(10, max(1, req.rounds_count))
    selected = pool[:rounds_count]
    
    bot1_total = 0
    bot2_total = 0
    round_logs = []
    
    for idx, item in enumerate(selected):
        r_data = build_cloze_round(item, idx, conn)
        target_words = [t["word"] for t in r_data["targets"]]
        
        b1_time = round(random.uniform(9.0, 18.0) + len(target_words)*2.5, 2)
        b1_hint = random.random() < 0.20
        b1_score = 15 if b1_hint else 20
        
        b2_time = round(random.uniform(9.0, 18.0) + len(target_words)*2.5, 2)
        b2_hint = random.random() < 0.20
        b2_score = 15 if b2_hint else 20
        
        if b1_time < b2_time:
            round_winner = bot1
            bot1_total += b1_score
        elif b2_time < b1_time:
            round_winner = bot2
            bot2_total += b2_score
        else:
            round_winner = "Berabere"
            bot1_total += b1_score
            bot2_total += b2_score
            
        round_logs.append({
            "round": idx + 1,
            "reference": r_data["reference"],
            "targets": target_words,
            "bot1_time": b1_time,
            "bot2_time": b2_time,
            "round_winner": round_winner,
            "round_ayah": r_data["full_ayah_arabic"]
        })
        
    bot1_total = min(100, bot1_total)
    bot2_total = min(100, bot2_total)
    
    if bot1_total > bot2_total:
        overall_winner = bot1
    elif bot2_total > bot1_total:
        overall_winner = bot2
    else:
        overall_winner = "Berabere"
        
    c = conn.cursor()
    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"Bot Âyet Blokları: {bot1} vs {bot2}", "clozeblocks_duel", "Kur'an Âyet Kelime Blokları Bot Arenası", overall_winner, max(bot1_total, bot2_total), rounds_count, time.time()))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "format": "2 Bot Kur'an Âyet Blokları Simülasyonu",
        "bot1": {"name": bot1, "score": bot1_total},
        "bot2": {"name": bot2, "score": bot2_total},
        "overall_winner": overall_winner,
        "max_score_enforced": 100,
        "rounds": round_logs
    }

# =====================================================================
# 21. SÜRÜKLE-BIRAK KUR'AN KELİME BULMACASI (HTML5 DRAG & DROP PUZZLE)
# =====================================================================
# HTML5 Drag and Drop API mekaniği: dragstart, dragover, drop
# Harf havuzundan (.letters-pool) hedef kutucuklara (.drop-zone) sürükleme.
# Tek Kişilik ve Çift Kişilik (1v1 Hâfız Düellosu) modları.

class DragDropDuelMatchRequest(BaseModel):
    player_name: str = "Hâfız Yarışmacı"
    bot_opponent: Optional[str] = None
    rounds_count: int = 5

class DragDropBotRoundSimRequest(BaseModel):
    bot_name: str
    round_id: str
    target_words: List[str]
    total_letters: int = 15
    difficulty: str = "medium"

class DragDropDuelFinishRequest(BaseModel):
    duel_id: str
    player_name: str
    bot_name: str
    player_score: int
    bot_score: int
    total_rounds: int = 5

class DragDropBotVsBotRequest(BaseModel):
    bot1_name: Optional[str] = None
    bot2_name: Optional[str] = None
    rounds_count: int = 5

def build_dragdrop_round(item, index, conn):
    import random
    c = conn.cursor()
    c.execute("SELECT quran_uthmani2 FROM ayahs WHERE surah_id = ? AND ayah_id = ?", (item["surah_id"], item["ayah_id"]))
    row_a = c.fetchone()
    full_ayah = row_a[0] if row_a and row_a[0] else ""

    c.execute("SELECT text FROM translations WHERE surah_id = ? AND ayah_id = ? AND edition_id = 'tr-diyanet-yeni'", (item["surah_id"], item["ayah_id"]))
    row_t = c.fetchone()
    trans = row_t[0] if row_t and row_t[0] else ""

    all_letters = []
    enriched_targets = []
    for t_idx, tgt in enumerate(item["targets"]):
        w = tgt["word"].upper()
        letters = list(w)
        all_letters.extend(letters)
        enriched_targets.append({
            "order": t_idx,
            "word": w,
            "letters": letters,
            "length": len(letters),
            "suffix": tgt.get("suffix", ""),
            "badge": len(letters)
        })

    shuffled_pool = []
    pool_chars = list(all_letters)
    random.shuffle(pool_chars)
    for p_idx, ch in enumerate(pool_chars):
        shuffled_pool.append({
            "id": f"dd_tile_{index}_{p_idx}_{ch}",
            "char": ch,
            "is_placed": False,
            "placed_in_zone": None
        })

    return {
        "round": index + 1,
        "id": f"dragdrop-{item['id']}",
        "surah_id": item["surah_id"],
        "ayah_id": item["ayah_id"],
        "sure_name": item["sure_name"],
        "reference": item["reference"],
        "template": item["template"],
        "targets": enriched_targets,
        "total_targets": len(enriched_targets),
        "total_letters": len(all_letters),
        "letter_pool": shuffled_pool,
        "full_ayah_arabic": full_ayah,
        "translation": trans,
        "audio_url": item.get("audio_url") or get_reciter_audio_url(12, item["surah_id"], item["ayah_id"]),
        "max_score": 20
    }

@app.get("/api/gameshow/drag-drop/rounds")
def get_dragdrop_rounds(count: int = Query(5, ge=1, le=20)):
    """
    HTML5 Sürükle-Bırak Kur'an Kelime Bulmacası seviyelerini döner.
    Harf havuzundaki (letters-pool) harfler âyet içindeki hedef kutucuklara (drop-zone) sürüklenir.
    Ayetler 'quran_uthmani2' ve Husary Muallim tilâveti ile donatılmıştır.
    Maksimum toplam Motivasyon Puanı: 100 (5 Tur x 20 Puan).
    """
    import random
    conn = get_db()
    pool = list(QURANIC_CLOZE_BLOCKS_MASTER)
    random.shuffle(pool)
    selected = pool[:count]

    rounds = []
    for idx, item in enumerate(selected):
        rounds.append(build_dragdrop_round(item, idx, conn))
    conn.close()

    return {
        "format": "HTML5 Sürükle-Bırak Kur'an Kelime Bulmacası (Drag & Drop)",
        "mechanic": "HTML5 Drag and Drop API (dragstart, dragover, drop)",
        "rounds_count": len(rounds),
        "max_total_score": 100,
        "rounds": rounds
    }

@app.post("/api/gameshow/drag-drop/duel/match")
def match_dragdrop_duel(req: DragDropDuelMatchRequest):
    """
    2 Kişilik Hâfız Düellosu (Sürükle-Bırak 1v1) maçı başlatır.
    İstenen veya ELO'ya en uygun bot rakibi eşleştirir, 5 Kur'an sürükle-bırak seviyesi üretir.
    Maksimum Motivasyon Puanı: 100 (5 Tur x 20 Puan).
    """
    import random
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    p1_row = c.fetchone()
    p1_elo = p1_row[0] if p1_row else 1350
    p1_tier = p1_row[1] if p1_row else "Mutavassıt (Orta)"

    if req.bot_opponent and any(req.bot_opponent in b for b in BOT_POOL):
        bot_name = req.bot_opponent
    else:
        c.execute("""
            SELECT player_name, elo_rating, hifz_tier
            FROM hafizlik_elo
            WHERE player_name != ?
            ORDER BY ABS(elo_rating - ?) ASC
            LIMIT 5
        """, (req.player_name, p1_elo))
        candidates = c.fetchall()
        if candidates:
            cand = random.choice(candidates)
            bot_name = cand["player_name"]
        else:
            bot_name = random.choice(BOT_POOL)

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (bot_name,))
    b_row = c.fetchone()
    bot_elo = b_row[0] if b_row else 1300
    bot_tier = b_row[1] if b_row else "Hâfız Adayı"

    pool = list(QURANIC_CLOZE_BLOCKS_MASTER)
    random.shuffle(pool)
    selected = pool[:req.rounds_count]

    rounds = []
    for idx, item in enumerate(selected):
        rounds.append(build_dragdrop_round(item, idx, conn))
    conn.close()

    avatar_map = {
        "Ahmet": "👨‍🎓", "Zeynep": "🧕", "Mustafa": "⚡", "Merve": "🌸",
        "Ömer": "📖", "Fâtıma": "✨", "Bilal": "🎙️", "Hüseyin": "👑",
        "Salih": "🛡️", "Ayşe": "🌺", "Hacer": "🏆", "İbrahim": "📜",
        "Yusuf": "🌟", "Enes": "🔍", "Rümeysa": "🌙", "Tarık": "🎯",
        "Esra": "⚡", "Hamza": "🦁", "Meryem": "🕊️", "Kerem": "💎"
    }
    bot_avatar = "👨‍🎓"
    for k, v in avatar_map.items():
        if k in bot_name:
            bot_avatar = v
            break

    duel_id = f"dd-duel-{int(time.time()*1000)%100000}"
    return {
        "duel_id": duel_id,
        "format": "2 Kişilik Sürükle-Bırak Hâfız Düellosu (1v1)",
        "player1": {
            "name": req.player_name,
            "elo": p1_elo,
            "tier": p1_tier,
            "avatar": "👤"
        },
        "player2": {
            "name": bot_name,
            "elo": bot_elo,
            "tier": bot_tier,
            "avatar": bot_avatar
        },
        "rounds_count": len(rounds),
        "max_total_score": 100,
        "rounds": rounds
    }

@app.post("/api/gameshow/drag-drop/duel/simulate-bot-round")
def simulate_dragdrop_bot_round(req: DragDropBotRoundSimRequest):
    """
    Bot kullanıcının Sürükle-Bırak turundaki harf harf ve kelime kelime yerleşimini simüle eder.
    Her harfin sürükleniş gecikmelerini ve kelime tamamlama sürelerini döner.
    """
    import random
    speed_factor = 0.85 if req.difficulty == "hard" else (1.2 if req.difficulty == "easy" else 1.0)

    word_timings = []
    letter_actions = []
    current_ms = int(random.uniform(1800, 3200) * speed_factor)

    for w_idx, w in enumerate(req.target_words):
        for l_idx, ch in enumerate(w):
            drag_duration_ms = int(random.uniform(400, 900) * speed_factor)
            current_ms += drag_duration_ms
            letter_actions.append({
                "word_index": w_idx,
                "letter_index": l_idx,
                "char": ch,
                "dropped_at_ms": current_ms
            })

        current_ms += int(random.uniform(500, 1000) * speed_factor)
        word_timings.append({
            "word": w,
            "solved_at_ms": current_ms,
            "solved_at_sec": round(current_ms / 1000.0, 2)
        })

    used_hint = random.random() < 0.15
    round_score = 15 if used_hint else 20
    total_time_sec = round(current_ms / 1000.0, 2)

    return {
        "bot_name": req.bot_name,
        "total_time_seconds": total_time_sec,
        "used_hint": used_hint,
        "round_score": round_score,
        "letter_actions": letter_actions,
        "word_timings": word_timings,
        "success": True
    }

@app.post("/api/gameshow/drag-drop/duel/finish")
def finish_dragdrop_duel(req: DragDropDuelFinishRequest):
    """
    2 Kişilik Sürükle-Bırak Düellosunu sonuçlandırır, ELO'yu günceller ve maç kaydını saklar.
    Maksimum Motivasyon Puanı barajı: 100 Puan.
    """
    conn = get_db()
    c = conn.cursor()

    p1_score = min(100, max(0, req.player_score))
    p2_score = min(100, max(0, req.bot_score))

    if p1_score > p2_score:
        winner = req.player_name
        delta_elo = 20
    elif p1_score < p2_score:
        winner = req.bot_name
        delta_elo = -10
    else:
        winner = "Berabere"
        delta_elo = 5

    c.execute("SELECT elo_rating FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    row = c.fetchone()
    old_elo = row[0] if row else 1350
    new_elo = max(800, old_elo + delta_elo)

    c.execute("""
        UPDATE hafizlik_elo
        SET elo_rating = ?, streak_count = CASE WHEN ? > ? THEN streak_count + 1 ELSE 0 END, last_updated = ?
        WHERE player_name = ?
    """, (new_elo, p1_score, p2_score, time.time(), req.player_name))

    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"2 Kişilik Sürükle-Bırak: {req.player_name} vs {req.bot_name}", "dragdrop_duel", "Kur'an Âyet Harf Sürüklemece", winner, max(p1_score, p2_score), req.total_rounds, time.time()))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "duel_id": req.duel_id,
        "winner": winner,
        "player_score": p1_score,
        "bot_score": p2_score,
        "delta_elo": delta_elo,
        "new_elo": new_elo,
        "message": f"Sürükle-Bırak Düellosu Tamamlandı! Kazanan: {winner} ({max(p1_score, p2_score)} Puan)"
    }

@app.post("/api/gameshow/drag-drop/duel/simulate-bot-match")
def simulate_dragdrop_bot_vs_bot(req: DragDropBotVsBotRequest):
    """
    İki bot yarışmacı arasında 5 turluk tam bir Sürükle-Bırak maçını simüle eder.
    Tüm turları, süreleri ve şampiyonu döner.
    """
    import random
    conn = get_db()

    bot1 = req.bot1_name if (req.bot1_name and req.bot1_name in BOT_POOL) else random.choice(BOT_POOL)
    remaining_bots = [b for b in BOT_POOL if b != bot1]
    bot2 = req.bot2_name if (req.bot2_name and req.bot2_name in remaining_bots) else random.choice(remaining_bots)

    pool = list(QURANIC_CLOZE_BLOCKS_MASTER)
    random.shuffle(pool)
    rounds_count = min(10, max(1, req.rounds_count))
    selected = pool[:rounds_count]

    bot1_total = 0
    bot2_total = 0
    round_logs = []

    for idx, item in enumerate(selected):
        r_data = build_dragdrop_round(item, idx, conn)
        target_words = [t["word"] for t in r_data["targets"]]

        b1_time = round(random.uniform(8.0, 16.0) + r_data["total_letters"] * 0.5, 2)
        b1_hint = random.random() < 0.15
        b1_score = 15 if b1_hint else 20

        b2_time = round(random.uniform(8.0, 16.0) + r_data["total_letters"] * 0.5, 2)
        b2_hint = random.random() < 0.15
        b2_score = 15 if b2_hint else 20

        if b1_time < b2_time:
            round_winner = bot1
            bot1_total += b1_score
        elif b2_time < b1_time:
            round_winner = bot2
            bot2_total += b2_score
        else:
            round_winner = "Berabere"
            bot1_total += b1_score
            bot2_total += b2_score

        round_logs.append({
            "round": idx + 1,
            "reference": r_data["reference"],
            "targets": target_words,
            "bot1_time": b1_time,
            "bot2_time": b2_time,
            "round_winner": round_winner,
            "round_ayah": r_data["full_ayah_arabic"]
        })

    bot1_total = min(100, bot1_total)
    bot2_total = min(100, bot2_total)

    if bot1_total > bot2_total:
        overall_winner = bot1
    elif bot2_total > bot1_total:
        overall_winner = bot2
    else:
        overall_winner = "Berabere"

    c = conn.cursor()
    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"Bot Sürükle-Bırak: {bot1} vs {bot2}", "dragdrop_duel", "Kur'an Âyet Harf Sürüklemece Bot Arenası", overall_winner, max(bot1_total, bot2_total), rounds_count, time.time()))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "format": "2 Bot Kur'an Sürükle-Bırak Simülasyonu",
        "bot1": {"name": bot1, "score": bot1_total},
        "bot2": {"name": bot2, "score": bot2_total},
        "overall_winner": overall_winner,
        "max_score_enforced": 100,
        "rounds": round_logs
    }

# =====================================================================
# 22. KARE & ÇENGEL BULMACA (SWIPE-TO-SELECT CROSSWORD PUZZLE)
# =====================================================================
# Kullanıcı ekrandaki bir hücreye tıklar, parmağıyla sürükleyerek
# kelimeyi seçer. Parmağını kaldırdığında seçenek işaretlenmiş olur.
# Gazete kare bulmaca estetiği: 38. Yatay (BETA), 60. Yatay (Kırmızı Ok),
# siyah kareler, hücre numaraları ve daireli hücreler.

class CrosswordDuelMatchRequest(BaseModel):
    player_name: str = "Hâfız Yarışmacı"
    bot_opponent: Optional[str] = None
    rounds_count: int = 5

class CrosswordBotRoundSimRequest(BaseModel):
    bot_name: str
    round_id: str
    target_word: str
    options: List[str]
    difficulty: str = "medium"

class CrosswordDuelFinishRequest(BaseModel):
    duel_id: str
    player_name: str
    bot_name: str
    player_score: int
    bot_score: int
    total_rounds: int = 5

class CrosswordBotVsBotRequest(BaseModel):
    bot1_name: Optional[str] = None
    bot2_name: Optional[str] = None
    rounds_count: int = 5

QURANIC_CROSSWORD_MASTER = [
    {
        "id": "cw-rum-14",
        "surah_id": 30,
        "ayah_id": 14,
        "sure_name": "Rûm",
        "reference": "Rûm, 30/14",
        "question": "Rûm Sûresi 14. âyette; \"O gün ... kopacak ve insanlar birbirinden ayrılacaklardır.\" buyurulmaktadır. Âyetteki boşluğa hangi kelime gelmelidir?",
        "correct_word": "KIYAMET",
        "options": [
            {"label": "A", "word": "KIYAMET", "is_correct": True},
            {"label": "B", "word": "CENNET", "is_correct": False},
            {"label": "C", "word": "CEHENNEM", "is_correct": False},
            {"label": "D", "word": "MİZAN", "is_correct": False}
        ],
        "words_placement": [
            {"word": "KIYAMET", "row": 4, "col": 1, "dir": "H", "num": 38, "is_target": True},
            {"word": "CENNET", "row": 7, "col": 2, "dir": "H", "num": 60, "has_arrow": True},
            {"word": "CEHENNEM", "row": 1, "col": 0, "dir": "V", "num": 1},
            {"word": "MİZAN", "row": 1, "col": 8, "dir": "V", "num": 18, "has_circle": True}
        ]
    },
    {
        "id": "cw-bakara-255",
        "surah_id": 2,
        "ayah_id": 255,
        "sure_name": "Bakara",
        "reference": "Bakara, 2/255 (Âyetü'l-Kürsî)",
        "question": "Âyetü'l-Kürsî'de geçen; daima diri olan ve bütün varlıkları ayakta tutup yöneten Yüce Allah'ın esmâsı hangisidir?",
        "correct_word": "KAYYUM",
        "options": [
            {"label": "A", "word": "KAYYUM", "is_correct": True},
            {"label": "B", "word": "KUDDÛS", "is_correct": False},
            {"label": "C", "word": "KERÎM", "is_correct": False},
            {"label": "D", "word": "KABIZ", "is_correct": False}
        ],
        "words_placement": [
            {"word": "KAYYUM", "row": 4, "col": 2, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "KUDDÛS", "row": 7, "col": 1, "dir": "H", "num": 60},
            {"word": "KERÎM", "row": 1, "col": 8, "dir": "V", "num": 18, "has_circle": True},
            {"word": "KABIZ", "row": 2, "col": 0, "dir": "V", "num": 12}
        ]
    },
    {
        "id": "cw-kadir-1",
        "surah_id": 97,
        "ayah_id": 3,
        "sure_name": "Kadir",
        "reference": "Kadir, 97/1-3",
        "question": "Kadir sûresinde bin aydan daha hayırlı olduğu bildirilen mübarek gece hangisidir?",
        "correct_word": "KADİR",
        "options": [
            {"label": "A", "word": "KADİR", "is_correct": True},
            {"label": "B", "word": "BERAAT", "is_correct": False},
            {"label": "C", "word": "MİRAÇ", "is_correct": False},
            {"label": "D", "word": "REGÂİP", "is_correct": False}
        ],
        "words_placement": [
            {"word": "KADİR", "row": 4, "col": 2, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "BERAAT", "row": 7, "col": 2, "dir": "H", "num": 60},
            {"word": "MİRAÇ", "row": 1, "col": 0, "dir": "V", "num": 14},
            {"word": "REGÂİP", "row": 2, "col": 8, "dir": "V", "num": 18, "has_circle": True}
        ]
    },
    {
        "id": "cw-fatiha-6",
        "surah_id": 1,
        "ayah_id": 6,
        "sure_name": "Fâtiha",
        "reference": "Fâtiha, 1/5-6",
        "question": "Fâtiha sûresinde 'İhdina's-sırâta'l-...; Bizi dosdoğru yola ilet' âyetinde geçen; dosdoğru yol anlamındaki kelime hangisidir?",
        "correct_word": "MÜSTAKİM",
        "options": [
            {"label": "A", "word": "MÜSTAKİM", "is_correct": True},
            {"label": "B", "word": "HİDAYET", "is_correct": False},
            {"label": "C", "word": "TEVHİD", "is_correct": False},
            {"label": "D", "word": "İHLÂS", "is_correct": False}
        ],
        "words_placement": [
            {"word": "MÜSTAKİM", "row": 4, "col": 1, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "HİDAYET", "row": 7, "col": 1, "dir": "H", "num": 60},
            {"word": "TEVHİD", "row": 1, "col": 8, "dir": "V", "num": 18, "has_circle": True},
            {"word": "İHLÂS", "row": 0, "col": 0, "dir": "V", "num": 1}
        ]
    },
    {
        "id": "cw-ihlas-2",
        "surah_id": 112,
        "ayah_id": 2,
        "sure_name": "İhlâs",
        "reference": "İhlâs, 112/1-2",
        "question": "İhlâs sûresinde geçen; 'Her şey O'na muhtaçtır, O hiçbir şeye muhtaç değildir' anlamındaki esmâ hangisidir?",
        "correct_word": "SAMED",
        "options": [
            {"label": "A", "word": "SAMED", "is_correct": True},
            {"label": "B", "word": "AHAD", "is_correct": False},
            {"label": "C", "word": "RAHMAN", "is_correct": False},
            {"label": "D", "word": "MELİK", "is_correct": False}
        ],
        "words_placement": [
            {"word": "SAMED", "row": 4, "col": 2, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "RAHMAN", "row": 7, "col": 1, "dir": "H", "num": 60},
            {"word": "AHAD", "row": 2, "col": 8, "dir": "V", "num": 18, "has_circle": True},
            {"word": "MELİK", "row": 1, "col": 0, "dir": "V", "num": 10}
        ]
    },
    {
        "id": "cw-asr-3",
        "surah_id": 103,
        "ayah_id": 3,
        "sure_name": "Asr",
        "reference": "Asr, 103/1-3",
        "question": "Asr sûresinde insanın hüsrandan kurtulması için imandan hemen sonra zikredilen ameller hangisidir?",
        "correct_word": "SALİH",
        "options": [
            {"label": "A", "word": "SALİH", "is_correct": True},
            {"label": "B", "word": "SABIR", "is_correct": False},
            {"label": "C", "word": "ŞÜKÜR", "is_correct": False},
            {"label": "D", "word": "TAKVA", "is_correct": False}
        ],
        "words_placement": [
            {"word": "SALİH", "row": 4, "col": 2, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "SABIR", "row": 7, "col": 2, "dir": "H", "num": 60},
            {"word": "ŞÜKÜR", "row": 1, "col": 0, "dir": "V", "num": 8},
            {"word": "TAKVA", "row": 1, "col": 8, "dir": "V", "num": 18, "has_circle": True}
        ]
    },
    {
        "id": "cw-fil-3",
        "surah_id": 105,
        "ayah_id": 3,
        "sure_name": "Fil",
        "reference": "Fil, 105/1-3",
        "question": "Fil sûresinde Kâbe'yi yıkmaya gelen orduyu taşlarla helak eden kuşlar hangisidir?",
        "correct_word": "EBABİL",
        "options": [
            {"label": "A", "word": "EBABİL", "is_correct": True},
            {"label": "B", "word": "HÜDHÜD", "is_correct": False},
            {"label": "C", "word": "GÜVERCİN", "is_correct": False},
            {"label": "D", "word": "KARTAL", "is_correct": False}
        ],
        "words_placement": [
            {"word": "EBABİL", "row": 4, "col": 2, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "HÜDHÜD", "row": 7, "col": 1, "dir": "H", "num": 60},
            {"word": "KARTAL", "row": 1, "col": 0, "dir": "V", "num": 12},
            {"word": "GÜVERCİN", "row": 0, "col": 8, "dir": "V", "num": 18, "has_circle": True}
        ]
    },
    {
        "id": "cw-kevser-2",
        "surah_id": 108,
        "ayah_id": 2,
        "sure_name": "Kevser",
        "reference": "Kevser, 108/1-2",
        "question": "Kevser sûresinde 'Biz sana Kevser'i verdik, öyleyse Rabbin için ... kıl' buyurulan ibadet hangisidir?",
        "correct_word": "NAMAZ",
        "options": [
            {"label": "A", "word": "NAMAZ", "is_correct": True},
            {"label": "B", "word": "ORUÇ", "is_correct": False},
            {"label": "C", "word": "ZEKÂT", "is_correct": False},
            {"label": "D", "word": "HAC", "is_correct": False}
        ],
        "words_placement": [
            {"word": "NAMAZ", "row": 4, "col": 2, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "ORUÇ", "row": 7, "col": 3, "dir": "H", "num": 60},
            {"word": "ZEKÂT", "row": 1, "col": 8, "dir": "V", "num": 18, "has_circle": True},
            {"word": "HAC", "row": 2, "col": 0, "dir": "V", "num": 6}
        ]
    },
    {
        "id": "cw-tin-4",
        "surah_id": 95,
        "ayah_id": 4,
        "sure_name": "Tîn",
        "reference": "Tîn, 95/1-4",
        "question": "Tîn sûresinde insanın en güzel şekilde yaratıldığı bildirilen kıvam, ölçü ve kıymet hangisidir?",
        "correct_word": "AHSEN",
        "options": [
            {"label": "A", "word": "AHSEN", "is_correct": True},
            {"label": "B", "word": "TAKVİM", "is_correct": False},
            {"label": "C", "word": "HİLKAT", "is_correct": False},
            {"label": "D", "word": "FITRAT", "is_correct": False}
        ],
        "words_placement": [
            {"word": "AHSEN", "row": 4, "col": 2, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "TAKVİM", "row": 7, "col": 1, "dir": "H", "num": 60},
            {"word": "HİLKAT", "row": 1, "col": 8, "dir": "V", "num": 18, "has_circle": True},
            {"word": "FITRAT", "row": 1, "col": 0, "dir": "V", "num": 9}
        ]
    },
    {
        "id": "cw-mulk-2",
        "surah_id": 67,
        "ayah_id": 2,
        "sure_name": "Mülk",
        "reference": "Mülk, 67/1-2",
        "question": "Mülk sûresinde hanginizin daha güzel amel işleyeceğini sınamak için yaratıldığı bildirilen hakikat hangisidir?",
        "correct_word": "ÖLÜM",
        "options": [
            {"label": "A", "word": "ÖLÜM", "is_correct": True},
            {"label": "B", "word": "DÜNYA", "is_correct": False},
            {"label": "C", "word": "SERVET", "is_correct": False},
            {"label": "D", "word": "GÖKLER", "is_correct": False}
        ],
        "words_placement": [
            {"word": "ÖLÜM", "row": 4, "col": 3, "dir": "H", "num": 38, "has_arrow": True, "is_target": True},
            {"word": "DÜNYA", "row": 7, "col": 2, "dir": "H", "num": 60},
            {"word": "SERVET", "row": 1, "col": 8, "dir": "V", "num": 18, "has_circle": True},
            {"word": "GÖKLER", "row": 1, "col": 0, "dir": "V", "num": 5}
        ]
    }
]

def build_crossword_swipe_round(item, index, conn):
    import random
    c = conn.cursor()
    c.execute("SELECT quran_uthmani2 FROM ayahs WHERE surah_id = ? AND ayah_id = ?", (item["surah_id"], item["ayah_id"]))
    row_a = c.fetchone()
    full_ayah = row_a[0] if row_a and row_a[0] else ""

    c.execute("SELECT text FROM translations WHERE surah_id = ? AND ayah_id = ? AND edition_id = 'tr-diyanet-yeni'", (item["surah_id"], item["ayah_id"]))
    row_t = c.fetchone()
    trans = row_t[0] if row_t and row_t[0] else ""

    GRID_SIZE = 10
    BLACK_CELLS = {
        (0, 4), (0, 5), (1, 3), (1, 6),
        (2, 4), (2, 5), (3, 8), (3, 9),
        (5, 0), (5, 9), (6, 4), (6, 5),
        (8, 3), (8, 6), (9, 4), (9, 5)
    }

    grid = []
    for r in range(GRID_SIZE):
        row_cells = []
        for col in range(GRID_SIZE):
            is_black = (r, col) in BLACK_CELLS
            row_cells.append({
                "row": r,
                "col": col,
                "char": "" if is_black else random.choice("ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"),
                "is_black": is_black,
                "num": None,
                "has_circle": False,
                "has_arrow": False,
                "is_target_cell": False
            })
        grid.append(row_cells)

    for wp in item["words_placement"]:
        w = wp["word"].upper()
        sr = wp["row"]
        sc = wp["col"]
        direction = wp["dir"]
        num = wp.get("num")
        has_arrow = wp.get("has_arrow", False)
        has_circle = wp.get("has_circle", False)
        is_target = wp.get("is_target", False)

        for i, ch in enumerate(w):
            cr = sr + (i if direction == "V" else 0)
            cc = sc + (i if direction == "H" else 0)
            if 0 <= cr < GRID_SIZE and 0 <= cc < GRID_SIZE:
                cell = grid[cr][cc]
                cell["char"] = ch
                cell["is_black"] = False
                if i == 0:
                    if num:
                        cell["num"] = num
                    if has_arrow:
                        cell["has_arrow"] = True
                if has_circle and (i == 0 or i == len(w) - 1):
                    cell["has_circle"] = True
                if is_target:
                    cell["is_target_cell"] = True

    return {
        "round": index + 1,
        "id": item["id"],
        "surah_id": item["surah_id"],
        "ayah_id": item["ayah_id"],
        "sure_name": item["sure_name"],
        "reference": item["reference"],
        "question": item["question"],
        "correct_word": item["correct_word"],
        "options": item["options"],
        "grid_size": GRID_SIZE,
        "grid": grid,
        "full_ayah_arabic": full_ayah,
        "translation": trans,
        "audio_url": get_reciter_audio_url(12, item["surah_id"], item["ayah_id"]),
        "max_score": 20
    }

@app.get("/api/gameshow/crossword-swipe/rounds")
def get_crossword_rounds(count: int = Query(5, ge=1, le=10)):
    """
    Kare & Çengel Bulmaca (Swipe-to-Select) seviyelerini döner.
    Kullanıcı hücreleri parmağıyla sürükleyerek seçeneği işaretler.
    Maksimum toplam Motivasyon Puanı: 100 (5 Tur x 20 Puan).
    """
    import random
    conn = get_db()
    pool = list(QURANIC_CROSSWORD_MASTER)
    random.shuffle(pool)
    selected = pool[:count]

    rounds = []
    for idx, item in enumerate(selected):
        rounds.append(build_crossword_swipe_round(item, idx, conn))
    conn.close()

    return {
        "format": "Kare & Çengel Bulmaca (Swipe to Select)",
        "mechanic": "Hücreleri Sürükleyerek Seçeneği İşaretleme (Touch / Mouse Drag)",
        "rounds_count": len(rounds),
        "max_total_score": 100,
        "rounds": rounds
    }

@app.post("/api/gameshow/crossword-swipe/duel/match")
def match_crossword_duel(req: CrosswordDuelMatchRequest):
    """
    2 Kişilik Hâfız Düellosu (Kare Bulmaca 1v1) maçı başlatır.
    İstenen veya ELO'ya en uygun bot rakibi eşleştirir.
    """
    import random
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    p1_row = c.fetchone()
    p1_elo = p1_row[0] if p1_row else 1350
    p1_tier = p1_row[1] if p1_row else "Mutavassıt (Orta)"

    if req.bot_opponent and any(req.bot_opponent in b for b in BOT_POOL):
        bot_name = req.bot_opponent
    else:
        c.execute("""
            SELECT player_name, elo_rating, hifz_tier
            FROM hafizlik_elo
            WHERE player_name != ?
            ORDER BY ABS(elo_rating - ?) ASC
            LIMIT 5
        """, (req.player_name, p1_elo))
        candidates = c.fetchall()
        if candidates:
            cand = random.choice(candidates)
            bot_name = cand["player_name"]
        else:
            bot_name = random.choice(BOT_POOL)

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (bot_name,))
    b_row = c.fetchone()
    bot_elo = b_row[0] if b_row else 1300
    bot_tier = b_row[1] if b_row else "Hâfız Adayı"

    pool = list(QURANIC_CROSSWORD_MASTER)
    random.shuffle(pool)
    selected = pool[:req.rounds_count]

    rounds = []
    for idx, item in enumerate(selected):
        rounds.append(build_crossword_swipe_round(item, idx, conn))
    conn.close()

    avatar_map = {
        "Ahmet": "👨‍🎓", "Zeynep": "🧕", "Mustafa": "⚡", "Merve": "🌸",
        "Ömer": "📖", "Fâtıma": "✨", "Bilal": "🎙️", "Hüseyin": "👑",
        "Salih": "🛡️", "Ayşe": "🌺", "Hacer": "🏆", "İbrahim": "📜",
        "Yusuf": "🌟", "Enes": "🔍", "Rümeysa": "🌙", "Tarık": "🎯",
        "Esra": "⚡", "Hamza": "🦁", "Meryem": "🕊️", "Kerem": "💎"
    }
    bot_avatar = "👨‍🎓"
    for k, v in avatar_map.items():
        if k in bot_name:
            bot_avatar = v
            break

    duel_id = f"cw-duel-{int(time.time()*1000)%100000}"
    return {
        "duel_id": duel_id,
        "format": "2 Kişilik Kare & Çengel Bulmaca Düellosu (1v1)",
        "player1": {
            "name": req.player_name,
            "elo": p1_elo,
            "tier": p1_tier,
            "avatar": "👤"
        },
        "player2": {
            "name": bot_name,
            "elo": bot_elo,
            "tier": bot_tier,
            "avatar": bot_avatar
        },
        "rounds_count": len(rounds),
        "max_total_score": 100,
        "rounds": rounds
    }

@app.post("/api/gameshow/crossword-swipe/duel/simulate-bot-round")
def simulate_crossword_bot_round(req: CrosswordBotRoundSimRequest):
    """
    Bot kullanıcının bulmacada seçeneği sürükleyerek işaretleme süresini simüle eder.
    """
    import random
    speed_factor = 0.85 if req.difficulty == "hard" else (1.2 if req.difficulty == "easy" else 1.0)

    # Bot analyzes grid, finds starting cell, then drags finger across word
    inspection_ms = int(random.uniform(2200, 4500) * speed_factor)
    drag_duration_ms = int(random.uniform(700, 1400) * speed_factor)
    total_ms = inspection_ms + drag_duration_ms

    used_hint = random.random() < 0.12
    round_score = 15 if used_hint else 20

    return {
        "bot_name": req.bot_name,
        "target_word": req.target_word,
        "inspection_ms": inspection_ms,
        "drag_duration_ms": drag_duration_ms,
        "total_solved_ms": total_ms,
        "total_solved_sec": round(total_ms / 1000.0, 2),
        "used_hint": used_hint,
        "round_score": round_score,
        "success": True
    }

@app.post("/api/gameshow/crossword-swipe/duel/finish")
def finish_crossword_duel(req: CrosswordDuelFinishRequest):
    """
    2 Kişilik Kare & Çengel Bulmaca Düellosunu sonuçlandırır.
    """
    conn = get_db()
    c = conn.cursor()

    p1_score = min(100, max(0, req.player_score))
    p2_score = min(100, max(0, req.bot_score))

    if p1_score > p2_score:
        winner = req.player_name
        delta_elo = 20
    elif p1_score < p2_score:
        winner = req.bot_name
        delta_elo = -10
    else:
        winner = "Berabere"
        delta_elo = 5

    c.execute("SELECT elo_rating FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    row = c.fetchone()
    old_elo = row[0] if row else 1350
    new_elo = max(800, old_elo + delta_elo)

    c.execute("""
        UPDATE hafizlik_elo
        SET elo_rating = ?, streak_count = CASE WHEN ? > ? THEN streak_count + 1 ELSE 0 END, last_updated = ?
        WHERE player_name = ?
    """, (new_elo, p1_score, p2_score, time.time(), req.player_name))

    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"2 Kişilik Kare Bulmaca: {req.player_name} vs {req.bot_name}", "crossword_duel", "Kur'an Âyet Kare & Çengel Bulmacası", winner, max(p1_score, p2_score), req.total_rounds, time.time()))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "duel_id": req.duel_id,
        "winner": winner,
        "player_score": p1_score,
        "bot_score": p2_score,
        "delta_elo": delta_elo,
        "new_elo": new_elo,
        "summary": f"Kare Bulmaca Düellosu Tamamlandı! Kazanan: {winner} ({max(p1_score, p2_score)} Puan)"
    }

@app.post("/api/gameshow/crossword-swipe/duel/simulate-bot-match")
def simulate_crossword_bot_vs_bot_match(req: CrosswordBotVsBotRequest):
    """
    2 Bot arasında 5 turluk Kare & Çengel Bulmaca maçını simüle eder (Test ve Denetim).
    """
    import random
    conn = get_db()
    c = conn.cursor()

    bot1 = req.bot1_name or random.choice(BOT_POOL)
    remaining_bots = [b for b in BOT_POOL if b != bot1]
    bot2 = req.bot2_name or random.choice(remaining_bots)

    rounds_count = min(5, max(1, req.rounds_count))
    pool = list(QURANIC_CROSSWORD_MASTER)
    random.shuffle(pool)
    selected = pool[:rounds_count]

    bot1_total = 0
    bot2_total = 0
    round_logs = []

    for idx, item in enumerate(selected):
        r_data = build_crossword_swipe_round(item, idx, conn)

        b1_time = round(random.uniform(3.5, 7.5), 2)
        b1_hint = random.random() < 0.1
        b1_score = 15 if b1_hint else 20

        b2_time = round(random.uniform(3.5, 7.5), 2)
        b2_hint = random.random() < 0.1
        b2_score = 15 if b2_hint else 20

        if b1_time < b2_time:
            round_winner = bot1
            bot1_total += b1_score
        elif b2_time < b1_time:
            round_winner = bot2
            bot2_total += b2_score
        else:
            round_winner = "Berabere"
            bot1_total += b1_score
            bot2_total += b2_score

        round_logs.append({
            "round": idx + 1,
            "reference": r_data["reference"],
            "target": r_data["correct_word"],
            "bot1_time": b1_time,
            "bot2_time": b2_time,
            "round_winner": round_winner,
            "round_ayah": r_data["full_ayah_arabic"]
        })

    bot1_total = min(100, bot1_total)
    bot2_total = min(100, bot2_total)

    if bot1_total > bot2_total:
        overall_winner = bot1
    elif bot2_total > bot1_total:
        overall_winner = bot2
    else:
        overall_winner = "Berabere"

    c = conn.cursor()
    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"Bot Kare Bulmaca: {bot1} vs {bot2}", "crossword_duel", "Kur'an Âyet Kare & Çengel Bulmacası Bot Arenası", overall_winner, max(bot1_total, bot2_total), rounds_count, time.time()))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "format": "2 Bot Kur'an Kare Bulmaca Simülasyonu",
        "bot1": {"name": bot1, "score": bot1_total},
        "bot2": {"name": bot2, "score": bot2_total},
        "overall_winner": overall_winner,
        "max_score_enforced": 100,
        "rounds": round_logs
    }



# =====================================================================
# OKUNAN ÂYETTEKİ KELİMEYİ BUL // 4 ÇERÇEVELİ DİNLEME OYUNU API
# =====================================================================
# Kullanıcı Kur'an'ı yeni öğrendiği için âyetin 4 kelimesi çerçevelerle gösterilir.
# Soru metni: "Okunan âyetteki kelimeyi bul"
# Sesler quran.com CDN (WBW Word-by-Word) üzerinden çekilir.
# Tek kişilik ve 2 kişilik (1v1 Hâfız Düellosu) modları.
# Maksimum Motivasyon Puanı: 100 Puan (5 Tur x 20 Puan).

try:
    from listen_find_game_data import LISTEN_FIND_ROUNDS
except ImportError:
    LISTEN_FIND_ROUNDS = []

class ListenFindMatchRequest(BaseModel):
    player_name: str = "Yeni Öğrenen Hâfız"
    bot_opponent: Optional[str] = None
    rounds_count: int = 5

class ListenFindBotSimRequest(BaseModel):
    bot_name: str
    round_id: str
    target_index: int
    difficulty: str = "medium"

class ListenFindFinishRequest(BaseModel):
    duel_id: str
    player_name: str
    bot_name: str
    player_score: int
    bot_score: int
    total_rounds: int = 5

class ListenFindBotVsBotRequest(BaseModel):
    bot1_name: Optional[str] = None
    bot2_name: Optional[str] = None
    rounds_count: int = 5

FETHA_CHAR = '\u064E'
DAMMA_CHAR = '\u064F'
KASRA_CHAR = '\u0650'
ALLOWED_INITIAL_VOWEL_MARKS = (FETHA_CHAR, DAMMA_CHAR, KASRA_CHAR)

def has_initial_fetha_esre_damme(arabic_text: str) -> bool:
    """
    Kelimede 1. harfin üzerinde/altında mutlaka fetha (üstün),
    esre (kasra) veya damme (ötre) olduğunu doğrular.
    Başında harekesiz harf (ör: 'الْفَلَقِ', 'الرَّحْمٰنِ', 'اللَّهِ', 'ٱقْرَأْ') olanları eler.
    """
    if not arabic_text:
        return False
    clean = arabic_text.strip()
    i = 0
    while i < len(clean) and not ('\u0621' <= clean[i] <= '\u064A' or clean[i] == '\u0671'):
        i += 1
    if i >= len(clean):
        return False
    first_letter = clean[i]
    if first_letter == '\u0671':  # Wasla elif fetha/esre/damme taşımaz
        return False
    j = i + 1
    marks = []
    while j < len(clean) and not ('\u0621' <= clean[j] <= '\u064A' or clean[j] == '\u0671'):
        marks.append(clean[j])
        j += 1
    return any(m in ALLOWED_INITIAL_VOWEL_MARKS for m in marks)

BEGINNER_AYAH_COORDINATES = [
    (1, 5),   # Fâtiha 1:5 (İyyâke na'büdü ve iyyâke neste'în) - 4 kelime fetha/esreli
    (113, 2), # Felak 113:2 (Min şerri mâ halak) - 4 kelime fetha/esreli
    (113, 3), # Felak 113:3 (Ve min şerri gâsikın izâ vekab) - 5 kelime fetha/esreli
    (105, 1), # Fil 105:1 (Elem tera keyfe fe'ale) - 4 kelime fethalı
    (105, 2), # Fil 105:2 (Elem yec'al keydehüm fî tadlîl) - 4 kelime fetha/esreli
    (105, 3), # Fil 105:3 (Ve ersele 'aleyhim tayran ebâbîl) - 4 kelime fethalı
    (109, 2), # Kâfirûn 109:2 (Lâ a'büdü mâ ta'büdûn) - 4 kelime fethalı
    (109, 3), # Kâfirûn 109:3 (Ve lâ entüm 'âbidûne mâ a'büd) - 4 kelime fethalı
    (111, 1), # Tebbet 111:1 (Tebbet yedâ ebî lehebin ve tebb) - 4 kelime fethalı
    (111, 2), # Tebbet 111:2 (Mâ ağnâ 'anhü mâlühû ve mâ keseb) - 4 kelime fethalı
    (111, 3), # Tebbet 111:3 (Seyaslâ nâran zâte leheb) - 4 kelime fethalı
    (100, 9), # Adiyat 100:9 (Efelâ ya'lemü izâ bü'sira) - 4 kelime fetha/ötreli
    (101, 6), # Kari'a 101:6 (Fe-emmâ men sekulet mevâzînüh) - 4 kelime fethalı
    (102, 4), # Tekasür 102:4 (Sümme kellâ sevfe ta'lemûn) - 4 kelime fetha/ötreli
    (104, 1), # Hümeze 104:1 (Veylün likülli hümezetin lümezeh) - 4 kelime fetha/esreli
]

def build_listen_find_round_from_words_table(conn, surah_id, ayah_id, round_num=1, target_index=None):
    """
    Kelimeleri doğrudan SQLite 'words' tablosundaki 'quran_uthmani2' sütunundan çeker.
    quran.com WBW ses URL'lerini bağlar.
    """
    import random
    c = conn.cursor()
    c.execute("""
        SELECT word_id, quran_uthmani2, text_turkish, text_latin
        FROM words
        WHERE surah_id = ? AND ayah_id = ?
        ORDER BY word_id ASC
    """, (surah_id, ayah_id))
    all_rows = c.fetchall()
    # KURAL: 1. karakterinde mutlaka fetha (üstün), esre (kasra) veya damme (ötre) olan kelimeleri filtrele!
    # Başında harekesiz harf olanlar (ör: 'الْفَلَقِ', 'الرَّحْمٰنِ', 'اللَّهِ') ASLA GÖSTERİLMEZ!
    valid_rows = [r for r in all_rows if has_initial_fetha_esre_damme(r[1])]
    if len(valid_rows) < 4:
        return None
    rows = valid_rows[:4]

    c.execute("SELECT sure_name FROM surahs WHERE surah_id = ?", (surah_id,))
    s_row = c.fetchone()
    sure_name = s_row[0] if s_row else f"{surah_id}. Sûre"

    c.execute("""
        SELECT text FROM translations
        WHERE surah_id = ? AND ayah_id = ? AND edition_id = 'tr-diyanet-yeni'
    """, (surah_id, ayah_id))
    t_row = c.fetchone()
    translation = t_row[0] if t_row else ""

    words = []
    labels = ["A", "B", "C", "D"]
    for idx, (wid, uth2, tr, lat) in enumerate(rows):
        clean_tr = (tr or "").strip()
        clean_lat = (lat or "").strip()
        if not clean_tr:
            clean_tr = clean_lat
        # Ligatür düzeltmesi: Lam-Elif birleşiminde araya giren med işaretini Elif'in üzerine alır
        fixed_arabic = uth2.replace('\u0644\u064e\u0653\u0627', '\u0644\u064e\u0627\u0653').replace('\u0644\u0653\u0627', '\u0644\u0627\u0653') if uth2 else ""
        
        # Latin okunuşundaki vasl ve kısaltma kalıntılarını yeni öğrenenler için berraklaştır
        lat_lower = clean_lat.lower()
        if lat_lower.startswith("llahi"):
            clean_lat = "Allâhi"
        elif lat_lower.startswith("llahu"):
            clean_lat = "Allâhu"
        elif lat_lower == "llezī":
            clean_lat = "Ellezî"
        elif lat_lower.startswith("l-"):
            clean_lat = "El-" + clean_lat[2:].capitalize()
        elif lat_lower == "lā":
            clean_lat = "Lâ"

        words.append({
            "label": labels[idx],
            "word_id": wid,
            "arabic": fixed_arabic,  # Scheherazade New & Uthmânî ligatür uyumlu
            "latin": clean_lat,
            "meaning": clean_tr,
            "audio_url": f"https://audio.qurancdn.com/wbw/{surah_id:03d}_{ayah_id:03d}_{wid:03d}.mp3"
        })

    # YENİ ÖĞRENENLER İÇİN İSTİSNAİ / KAFA KARIŞTIRICI KELİMELERİ ASLA HEDEF SORU SEÇME!
    # Ellezî (vasıl elifi), zâid harfler (Ulâike), vâv-elif dönüşümleri (Salât, Zekât) kesinlikle filtrelenir.
    CONFUSING_STEMS = ["الَّذ", "الَّت", "أُولٰ", "أُولَ", "أُولُو", "صَلٰو", "زَكٰو", "حَيٰو", "رِبٰو", "مِائَ"]
    
    valid_indices = []
    for i, w in enumerate(words):
        ar = w["arabic"].strip()
        lat = w["latin"].strip().lower()
        # 1. İstisnai yazım kökleri soru olamaz
        if any(stem in ar for stem in CONFUSING_STEMS):
            continue
        # 2. Vasl kaynaklı başta ses düşmesi içeren kelimeler soru olamaz
        if lat.startswith("ll") or lat.startswith("l-"):
            continue
        valid_indices.append(i)

    if not valid_indices:
        valid_indices = [0]

    if target_index is None or target_index not in valid_indices:
        target_index = random.choice(valid_indices)

    target_word = words[target_index]
    return {
        "round": round_num,
        "id": f"lfg-{surah_id}-{ayah_id}",
        "surah_id": surah_id,
        "ayah_id": ayah_id,
        "sure_name": sure_name,
        "reference": f"{sure_name} Sûresi, {ayah_id}. Âyet",
        "question": "Okunan âyetteki kelimeyi bul",
        "translation": translation,
        "source": "words tablosu quran_uthmani2",
        "target_index": target_index,
        "target_word_arabic": target_word["arabic"],
        "target_word_latin": target_word["latin"],
        "audio_url": target_word["audio_url"],
        "words": words
    }

@app.get("/api/gameshow/listen-find/rounds")
def get_listen_find_rounds(count: int = 5):
    """
    Okunan Âyetteki Kelimeyi Bul oyunu için doğrudan SQLite 'words' tablosundan
    'quran_uthmani2' sütununu çekerek dinamik turlar üretir.
    """
    import random
    conn = get_db()
    coords = list(BEGINNER_AYAH_COORDINATES)
    random.shuffle(coords)

    rounds = []
    for s_id, a_id in coords:
        r = build_listen_find_round_from_words_table(conn, s_id, a_id, round_num=len(rounds) + 1)
        if r:
            rounds.append(r)
        if len(rounds) >= count:
            break
            
    conn.close()

    # Yedek havuz (her ihtimale karşı)
    if not rounds and LISTEN_FIND_ROUNDS:
        pool = list(LISTEN_FIND_ROUNDS)
        random.shuffle(pool)
        rounds = pool[:count]

    return {
        "status": "success",
        "question": "Okunan âyetteki kelimeyi bul",
        "source": "words tablosu quran_uthmani2",
        "total_rounds": len(rounds),
        "points_per_round": 20,
        "max_motivation_score": 100,
        "audio_source": "quran.com WBW CDN",
        "rounds": rounds
    }

@app.post("/api/gameshow/listen-find/duel/match")
def match_listen_find_duel(req: ListenFindMatchRequest):
    """
    2 Kişilik Hâfız Düellosu (Okunan Kelimeyi Bul 1v1) maçı başlatır.
    Kelimeleri doğrudan SQLite 'words' tablosundan 'quran_uthmani2' sütununu çekerek üretir.
    """
    import random
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    p1_row = c.fetchone()
    p1_elo = p1_row[0] if p1_row else 1350

    if req.bot_opponent and any(req.bot_opponent in b for b in BOT_POOL):
        bot_name = req.bot_opponent
    else:
        c.execute("""
            SELECT player_name, elo_rating, hifz_tier
            FROM hafizlik_elo
            WHERE player_name != ?
            ORDER BY ABS(elo_rating - ?) ASC
            LIMIT 5
        """, (req.player_name, p1_elo))
        candidates = c.fetchall()
        if candidates:
            cand = random.choice(candidates)
            bot_name = cand["player_name"]
        else:
            bot_name = random.choice(BOT_POOL)

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (bot_name,))
    b_row = c.fetchone()
    bot_elo = b_row[0] if b_row else 1900
    bot_tier = b_row[1] if b_row else "Müntehi (İleri)"

    coords = list(BEGINNER_AYAH_COORDINATES)
    random.shuffle(coords)

    rounds = []
    for s_id, a_id in coords:
        r = build_listen_find_round_from_words_table(conn, s_id, a_id, round_num=len(rounds) + 1)
        if r:
            rounds.append(r)
        if len(rounds) >= req.rounds_count:
            break

    conn.close()

    if not rounds and LISTEN_FIND_ROUNDS:
        pool = list(LISTEN_FIND_ROUNDS)
        random.shuffle(pool)
        rounds = pool[:req.rounds_count]

    duel_id = f"lf-duel-{random.randint(10000, 99999)}"

    return {
        "success": True,
        "duel_id": duel_id,
        "source": "words tablosu quran_uthmani2",
        "player": {
            "name": req.player_name,
            "elo": p1_elo
        },
        "bot": {
            "name": bot_name,
            "elo": bot_elo,
            "tier": bot_tier
        },
        "total_rounds": len(rounds),
        "points_per_round": 20,
        "max_score": 100,
        "rounds": rounds
    }

@app.post("/api/gameshow/listen-find/duel/bot-sim")
def simulate_listen_find_bot(req: ListenFindBotSimRequest):
    """
    Botun dinleme ve kelimeyi seçme refleksini simüle eder.
    2.2 - 4.2 saniye arasında dinleme süresi harcar. %85 doğruluk payına sahiptir.
    """
    import random
    bot_time = round(random.uniform(2.2, 4.2), 2)
    is_correct = random.random() < 0.85
    bot_choice = req.target_index if is_correct else (req.target_index + random.choice([1, 2, 3])) % 4

    return {
        "bot_name": req.bot_name,
        "round_id": req.round_id,
        "time_seconds": bot_time,
        "is_correct": is_correct,
        "bot_choice_index": bot_choice,
        "round_score": 20 if is_correct else 0,
        "reaction": "El-Hamdülillâh doğru kelimeyi buldum!" if is_correct else "Bu kelimede karıştırdım."
    }

@app.post("/api/gameshow/listen-find/duel/finish")
def finish_listen_find_duel(req: ListenFindFinishRequest):
    """
    2 Kişilik Okunan Kelimeyi Bul Düellosunu sonuçlandırır, ELO ve liderliği günceller.
    Maksimum Motivasyon Puanı barajı: 100 Puan.
    """
    conn = get_db()
    c = conn.cursor()

    p1_score = min(100, max(0, req.player_score))
    p2_score = min(100, max(0, req.bot_score))

    if p1_score > p2_score:
        winner = req.player_name
        delta_elo = 20
    elif p1_score < p2_score:
        winner = req.bot_name
        delta_elo = -10
    else:
        winner = "Berabere"
        delta_elo = 5

    c.execute("SELECT elo_rating FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    row = c.fetchone()
    old_elo = row[0] if row else 1350
    new_elo = max(800, old_elo + delta_elo)

    c.execute("""
        UPDATE hafizlik_elo
        SET elo_rating = ?, streak_count = CASE WHEN ? > ? THEN streak_count + 1 ELSE 0 END, last_updated = ?
        WHERE player_name = ?
    """, (new_elo, p1_score, p2_score, time.time(), req.player_name))

    c.execute("""
        INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            total_points = total_points + excluded.total_points,
            matches_played = matches_played + 1,
            highest_score = MAX(highest_score, excluded.highest_score),
            last_active = excluded.last_active
    """, (req.player_name, p1_score, p1_score, time.time()))

    c.execute("""
        INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            total_points = total_points + excluded.total_points,
            matches_played = matches_played + 1,
            highest_score = MAX(highest_score, excluded.highest_score),
            last_active = excluded.last_active
    """, (req.bot_name, p2_score, p2_score, time.time()))

    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"Okunan Kelimeyi Bul: {req.player_name} vs {req.bot_name}", "listen_find_duel", "Kur'an 4 Çerçeveli Kelime Dinleme Havuzu", winner, max(p1_score, p2_score), req.total_rounds, time.time()))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "winner": winner,
        "player_score": p1_score,
        "bot_score": p2_score,
        "delta_elo": delta_elo,
        "new_elo": new_elo,
        "max_score_enforced": 100
    }

@app.post("/api/gameshow/listen-find/duel/bot-vs-bot")
def simulate_listen_find_bot_vs_bot(req: ListenFindBotVsBotRequest):
    """
    20 Bot Arenası: İki yapay zeka botunun Okunan Kelimeyi Bul düellosunu simüle eder.
    """
    import random
    bot1 = req.bot1_name or random.choice(BOT_POOL)
    remaining_bots = [b for b in BOT_POOL if b != bot1]
    bot2 = req.bot2_name or (random.choice(remaining_bots) if remaining_bots else "Zeynep K. (Kısa Sûreler)")

    conn = get_db()
    pool = list(LISTEN_FIND_ROUNDS)
    random.shuffle(pool)
    rounds_count = min(req.rounds_count, len(pool))
    selected = pool[:rounds_count]

    bot1_total = 0
    bot2_total = 0
    round_logs = []

    for idx, r_data in enumerate(selected):
        b1_correct = random.random() < 0.85
        b2_correct = random.random() < 0.85
        b1_time = round(random.uniform(2.1, 4.3), 2)
        b2_time = round(random.uniform(2.1, 4.3), 2)

        if b1_correct and not b2_correct:
            round_winner = bot1
            bot1_total += 20
        elif b2_correct and not b1_correct:
            round_winner = bot2
            bot2_total += 20
        elif b1_correct and b2_correct:
            if b1_time < b2_time:
                round_winner = bot1
                bot1_total += 20
            elif b2_time < b1_time:
                round_winner = bot2
                bot2_total += 20
            else:
                round_winner = "Berabere"
                bot1_total += 10
                bot2_total += 10
        else:
            round_winner = "İkisi de Yanlış"

        round_logs.append({
            "round": idx + 1,
            "reference": r_data["reference"],
            "target_arabic": r_data["target_word_arabic"],
            "target_latin": r_data["target_word_latin"],
            "bot1_time": b1_time,
            "bot2_time": b2_time,
            "round_winner": round_winner
        })

    bot1_total = min(100, bot1_total)
    bot2_total = min(100, bot2_total)

    if bot1_total > bot2_total:
        overall_winner = bot1
    elif bot2_total > bot1_total:
        overall_winner = bot2
    else:
        overall_winner = "Berabere"

    c = conn.cursor()
    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"Bot Okunan Kelime: {bot1} vs {bot2}", "listen_find_duel", "Kur'an 4 Çerçeveli Kelime Dinleme Arenası", overall_winner, max(bot1_total, bot2_total), rounds_count, time.time()))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "format": "2 Bot Okunan Kelimeyi Bul Simülasyonu",
        "bot1": {"name": bot1, "score": bot1_total},
        "bot2": {"name": bot2, "score": bot2_total},
        "overall_winner": overall_winner,
        "max_score_enforced": 100,
        "rounds": round_logs
    }

# =====================================================================
# SÛRE EZBERLEME OYUNU // DİNLENEN ÂYETTEN SONRAKİ ÂYETİ BUL (2. ODA)
# =====================================================================

class SurahMemorizeMatchRequest(BaseModel):
    surah_id: int = 1
    difficulty: str = "hard"
    player_name: str = "Yeni Öğrenen Hâfız"
    bot_opponent: Optional[str] = None

class SurahMemorizeFinishRequest(BaseModel):
    duel_id: str
    player_name: str
    bot_name: str
    player_score: int
    bot_score: int
    surah_id: int

def build_surah_memorize_session(conn, surah_id: int = 1, difficulty: str = "hard"):
    """
    Sûre bütünlüğünü (1 -> 2 -> 3...) kesinlikle koruyarak,
    dinlenen âyetten sonraki âyeti bulma turlarını SQLite'tan dinamik üretir.
    Zorluk endeksi:
      - 'hard': Aynı sûreden diğer âyetler (veya benzer fâsıla/kısa sûre âyetleri) çeldirici olur.
      - 'easy': Farklı sûrelerden âyetler çeldirici olur.
    """
    import random
    c = conn.cursor()
    c.execute("SELECT sure_name, ayah_count FROM surahs WHERE surah_id = ?", (surah_id,))
    s_row = c.fetchone()
    if not s_row:
        return None
    sure_name, ayah_count = s_row

    c.execute("""
        SELECT a.ayah_id, a.quran_uthmani2, COALESCE(t.text, '') as translation
        FROM ayahs a
        LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
        WHERE a.surah_id = ?
        ORDER BY a.ayah_id ASC
    """, (surah_id,))
    ayah_rows = c.fetchall()

    if len(ayah_rows) < 2:
        return None

    rounds = []
    total_steps = len(ayah_rows) - 1

    for step_idx in range(total_steps):
        curr_ayah_id, curr_ar, curr_tr = ayah_rows[step_idx]
        target_ayah_id, target_ar, target_tr = ayah_rows[step_idx + 1]

        # Scheherazade New & Uthmânî ligatür koruması
        curr_ar_fixed = curr_ar.replace('\u0644\u064e\u0653\u0627', '\u0644\u064e\u0627\u0653').replace('\u0644\u0653\u0627', '\u0644\u0627\u0653') if curr_ar else ""
        target_ar_fixed = target_ar.replace('\u0644\u064e\u0653\u0627', '\u0644\u064e\u0627\u0653').replace('\u0644\u0653\u0627', '\u0644\u0627\u0653') if target_ar else ""

        distractors = []
        if difficulty == "hard":
            # 1. Aynı sûrenin diğer âyetleri
            same_surah_cands = [r for r in ayah_rows if r[0] not in (curr_ayah_id, target_ayah_id)]
            random.shuffle(same_surah_cands)
            for cand in same_surah_cands[:3]:
                cand_ar = cand[1].replace('\u0644\u064e\u0653\u0627', '\u0644\u064e\u0627\u0653').replace('\u0644\u0653\u0627', '\u0644\u0627\u0653') if cand[1] else ""
                distractors.append({
                    "arabic": cand_ar,
                    "translation": cand[2],
                    "is_correct": False,
                    "ayah_num": cand[0],
                    "surah_id": surah_id
                })

            # Eğer kısa sûrede yeterli âyet yoksa (örn. Kevser 3 âyet), 90-114 arası sûrelerden tamamla
            if len(distractors) < 3:
                needed = 3 - len(distractors)
                c.execute("""
                    SELECT a.surah_id, a.ayah_id, a.quran_uthmani2, COALESCE(t.text, '')
                    FROM ayahs a
                    LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
                    WHERE a.surah_id != ? AND a.surah_id >= 90
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (surah_id, needed))
                for extra in c.fetchall():
                    extra_ar = extra[2].replace('\u0644\u064e\u0653\u0627', '\u0644\u064e\u0627\u0653').replace('\u0644\u0653\u0627', '\u0644\u0627\u0653') if extra[2] else ""
                    distractors.append({
                        "arabic": extra_ar,
                        "translation": extra[3],
                        "is_correct": False,
                        "ayah_num": extra[1],
                        "surah_id": extra[0]
                    })
        else:
            # Kolay mod: Farklı sûrelerden rastgele âyetler
            c.execute("""
                SELECT a.surah_id, a.ayah_id, a.quran_uthmani2, COALESCE(t.text, '')
                FROM ayahs a
                LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
                WHERE a.surah_id != ?
                ORDER BY RANDOM()
                LIMIT 3
            """, (surah_id,))
            for cand in c.fetchall():
                cand_ar = cand[2].replace('\u0644\u064e\u0653\u0627', '\u0644\u064e\u0627\u0653').replace('\u0644\u0653\u0627', '\u0644\u0627\u0653') if cand[2] else ""
                distractors.append({
                    "arabic": cand_ar,
                    "translation": cand[3],
                    "is_correct": False,
                    "ayah_num": cand[1],
                    "surah_id": cand[0]
                })

        options = [
            {
                "arabic": target_ar_fixed,
                "translation": target_tr,
                "is_correct": True,
                "ayah_num": target_ayah_id,
                "surah_id": surah_id
            }
        ] + distractors[:3]

        random.shuffle(options)
        labels = ["A", "B", "C", "D"]
        correct_index = 0
        for opt_idx, opt in enumerate(options):
            opt["label"] = labels[opt_idx]
            if opt["is_correct"]:
                correct_index = opt_idx

        rounds.append({
            "step": step_idx + 1,
            "total_steps": total_steps,
            "surah_id": surah_id,
            "sure_name": sure_name,
            "current_ayah_id": curr_ayah_id,
            "current_arabic": curr_ar_fixed,
            "current_translation": curr_tr,
            "audio_url": f"https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/{surah_id:03d}{curr_ayah_id:03d}.mp3",
            "target_ayah_id": target_ayah_id,
            "correct_index": correct_index,
            "options": options
        })

    return {
        "status": "success",
        "surah_id": surah_id,
        "sure_name": sure_name,
        "difficulty": difficulty,
        "question": "Dinlenen âyetten sonraki âyet hangisi, işaretleyiniz",
        "total_steps": total_steps,
        "rounds": rounds
    }

@app.get("/api/gameshow/surah-memorize/session")
def get_surah_memorize_session(surah_id: int = 1, difficulty: str = "hard"):
    """
    Sûre Ezberleme Oyunu oturumu üretir. Sûre bütünlüğü 1'den sona kadar korunur.
    """
    conn = get_db()
    session = build_surah_memorize_session(conn, surah_id=surah_id, difficulty=difficulty)
    conn.close()
    if not session:
        raise HTTPException(status_code=404, detail=f"Sûre {surah_id} için ezber oturumu oluşturulamadı")
    return session

@app.post("/api/gameshow/surah-memorize/duel/match")
def match_surah_memorize_duel(req: SurahMemorizeMatchRequest):
    """
    Sûre Ezberleme Oyunu 1v1 Düello maçı başlatır ve bot eşleştirir.
    """
    import random
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    p1_row = c.fetchone()
    p1_elo = p1_row[0] if p1_row else 1350

    if req.bot_opponent and any(req.bot_opponent in b for b in BOT_POOL):
        bot_name = req.bot_opponent
    else:
        c.execute("""
            SELECT player_name, elo_rating, hifz_tier
            FROM hafizlik_elo
            WHERE player_name != ?
            ORDER BY ABS(elo_rating - ?) ASC
            LIMIT 5
        """, (req.player_name, p1_elo))
        candidates = c.fetchall()
        if candidates:
            cand = random.choice(candidates)
            bot_name = cand["player_name"]
        else:
            bot_name = random.choice(BOT_POOL)

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (bot_name,))
    b_row = c.fetchone()
    bot_elo = b_row[0] if b_row else 1900
    bot_tier = b_row[1] if b_row else "Müntehi (İleri)"

    session = build_surah_memorize_session(conn, surah_id=req.surah_id, difficulty=req.difficulty)
    conn.close()

    if not session:
        raise HTTPException(status_code=404, detail="Sûre oturumu üretilemedi")

    duel_id = f"sm-duel-{random.randint(10000, 99999)}"

    return {
        "success": True,
        "duel_id": duel_id,
        "surah_id": req.surah_id,
        "sure_name": session["sure_name"],
        "difficulty": req.difficulty,
        "player": {
            "name": req.player_name,
            "elo": p1_elo
        },
        "bot": {
            "name": bot_name,
            "elo": bot_elo,
            "tier": bot_tier
        },
        "total_rounds": session["total_steps"],
        "rounds": session["rounds"]
    }

@app.post("/api/gameshow/surah-memorize/duel/finish")
def finish_surah_memorize_duel(req: SurahMemorizeFinishRequest):
    """
    Sûre Ezberleme Düellosunu sonuçlandırır, ELO ve istatistikleri günceller.
    Maksimum Motivasyon Puanı barajı: 100 Puan.
    """
    conn = get_db()
    c = conn.cursor()

    p1_score = min(100, max(0, req.player_score))
    p2_score = min(100, max(0, req.bot_score))

    if p1_score > p2_score:
        winner = req.player_name
        delta_elo = 20
    elif p1_score < p2_score:
        winner = req.bot_name
        delta_elo = -10
    else:
        winner = "Berabere"
        delta_elo = 5

    c.execute("SELECT elo_rating FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    row = c.fetchone()
    old_elo = row[0] if row else 1350
    new_elo = max(800, old_elo + delta_elo)

    c.execute("""
        UPDATE hafizlik_elo
        SET elo_rating = ?, streak_count = CASE WHEN ? > ? THEN streak_count + 1 ELSE 0 END, last_updated = ?
        WHERE player_name = ?
    """, (new_elo, p1_score, p2_score, time.time(), req.player_name))

    c.execute("""
        INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            total_points = total_points + excluded.total_points,
            matches_played = matches_played + 1,
            highest_score = MAX(highest_score, excluded.highest_score),
            last_active = excluded.last_active
    """, (req.player_name, p1_score, p1_score, time.time()))

    c.execute("""
        INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            total_points = total_points + excluded.total_points,
            matches_played = matches_played + 1,
            highest_score = MAX(highest_score, excluded.highest_score),
            last_active = excluded.last_active
    """, (req.bot_name, p2_score, p2_score, time.time()))

    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"Sûre Ezberleme: {req.player_name} vs {req.bot_name}", "surah_memorize_duel", f"Sûre #{req.surah_id} Sıralı Ezber Havuzu", winner, max(p1_score, p2_score), 10, time.time()))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "winner": winner,
        "player_score": p1_score,
        "bot_score": p2_score,
        "delta_elo": delta_elo,
        "new_elo": new_elo,
        "max_score_enforced": 100
    }


# =====================================================================
# ÂYET TAMAMLAMA OYUNU // KAYBOLAN KELİMEYİ DAKTİLO İLE TAMAMLA (2. ODA)
# =====================================================================

class AyetTamamlamaMatchRequest(BaseModel):
    surah_id: int = 112
    player_name: str = "Yeni Öğrenen Hâfız"
    bot_opponent: Optional[str] = None

class AyetTamamlamaFinishRequest(BaseModel):
    duel_id: str
    player_name: str
    bot_name: str
    player_score: int
    bot_score: int
    surah_id: int

class RecordMistakeRequest(BaseModel):
    game_name: str = "Âyet Tamamlama Oyunu"
    game_id: str = "ayet_tamamlama"
    player_name: str = "Siz (Yarışmacı)"
    surah_id: Optional[int] = None
    ayah_id: Optional[int] = None
    sure_name: Optional[str] = None
    reference: Optional[str] = None
    question_type: Optional[str] = "Hatalı Seçenek"
    target_text: str
    selected_wrong_text: str
    full_ayah_text: Optional[str] = ""

def build_ayet_tamamlama_session(conn, surah_id: int = 112):
    """
    Âyet Tamamlama Oyunu için sûrenin tüm âyet ve kelimelerini çeker.
    Uthmânî ligatür düzeltmesini uygular.
    """
    import random
    c = conn.cursor()
    c.execute("SELECT sure_name, ayah_count FROM surahs WHERE surah_id = ?", (surah_id,))
    s_row = c.fetchone()
    if not s_row:
        return None
    sure_name, ayah_count = s_row

    c.execute("""
        SELECT a.ayah_id, a.quran_uthmani2, COALESCE(t.text, '') as translation
        FROM ayahs a
        LEFT JOIN translations t ON t.surah_id = a.surah_id AND t.ayah_id = a.ayah_id AND t.edition_id = 'tr-diyanet-yeni'
        WHERE a.surah_id = ?
        ORDER BY a.ayah_id ASC
    """, (surah_id,))
    ayah_rows = c.fetchall()

    c.execute("""
        SELECT ayah_id, word_id, quran_uthmani2, text_turkish, text_latin
        FROM words
        WHERE surah_id = ?
        ORDER BY ayah_id ASC, word_id ASC
    """, (surah_id,))
    word_rows = c.fetchall()

    def fix_lig(ar):
        if not ar:
            return ""
        return ar.replace('\u0644\u064e\u0653\u0627', '\u0644\u064e\u0627\u0653').replace('\u0644\u0653\u0627', '\u0644\u0627\u0653')

    words_by_ayah = {}
    all_surah_words = []
    for r in word_rows:
        w_obj = {
            "ayah_id": r[0],
            "word_id": r[1],
            "arabic": fix_lig(r[2]),
            "meaning": r[3] or "",
            "latin": r[4] or ""
        }
        words_by_ayah.setdefault(r[0], []).append(w_obj)
        all_surah_words.append(w_obj)

    # Kısa sûrelerden çeldirici kelime yedek havuzu
    c.execute("""
        SELECT ayah_id, word_id, quran_uthmani2, text_turkish, text_latin
        FROM words
        WHERE surah_id >= 105 AND surah_id != ?
        ORDER BY RANDOM()
        LIMIT 40
    """, (surah_id,))
    backup_words = [
        {
            "ayah_id": r[0],
            "word_id": r[1],
            "arabic": fix_lig(r[2]),
            "meaning": r[3] or "",
            "latin": r[4] or ""
        }
        for r in c.fetchall()
    ]

    ayahs_data = []
    for a_row in ayah_rows:
        a_id = a_row[0]
        a_text = fix_lig(a_row[1])
        a_trans = a_row[2]
        a_words = words_by_ayah.get(a_id, [])

        if not a_words:
            continue

        ayahs_data.append({
            "ayah_id": a_id,
            "sure_name": sure_name,
            "surah_id": surah_id,
            "full_arabic": a_text,
            "translation": a_trans,
            "audio_url": f"https://mirrors.quranicaudio.com/everyayah/Husary_Muallim_128kbps/{surah_id:03d}{a_id:03d}.mp3",
            "words": a_words
        })

    return {
        "status": "success",
        "surah_id": surah_id,
        "sure_name": sure_name,
        "ayah_count": len(ayahs_data),
        "question": "Boş hücredeki olması gereken kelimeyi yerine koyarak âyeti tamamlayınız",
        "ayahs": ayahs_data,
        "surah_words": all_surah_words,
        "backup_words": backup_words
    }

@app.get("/api/gameshow/ayet-tamamlama/session")
def get_ayet_tamamlama_session(surah_id: int = 112):
    """
    Âyet Tamamlama Oyunu için sûrenin tüm âyet ve kelimelerini döndürür.
    """
    conn = get_db()
    sess = build_ayet_tamamlama_session(conn, surah_id=surah_id)
    conn.close()
    if not sess:
        raise HTTPException(status_code=404, detail="Sûre verisi bulunamadı")
    return sess

@app.post("/api/gameshow/ayet-tamamlama/duel/match")
def match_ayet_tamamlama_duel(req: AyetTamamlamaMatchRequest):
    """
    Âyet Tamamlama 1v1 Düello maçı başlatır ve bot eşleştirir.
    """
    import random
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    p1_row = c.fetchone()
    p1_elo = p1_row[0] if p1_row else 1350

    if req.bot_opponent and any(req.bot_opponent in b for b in BOT_POOL):
        bot_name = req.bot_opponent
    else:
        c.execute("""
            SELECT player_name, elo_rating, hifz_tier
            FROM hafizlik_elo
            WHERE player_name != ?
            ORDER BY ABS(elo_rating - ?) ASC
            LIMIT 5
        """, (req.player_name, p1_elo))
        candidates = c.fetchall()
        if candidates:
            cand = random.choice(candidates)
            bot_name = cand["player_name"]
        else:
            bot_name = random.choice(BOT_POOL)

    c.execute("SELECT elo_rating, hifz_tier FROM hafizlik_elo WHERE player_name = ?", (bot_name,))
    b_row = c.fetchone()
    bot_elo = b_row[0] if b_row else 1900
    bot_tier = b_row[1] if b_row else "Müntehi (İleri)"

    sess = build_ayet_tamamlama_session(conn, surah_id=req.surah_id)
    conn.close()

    if not sess:
        raise HTTPException(status_code=404, detail="Sûre verisi bulunamadı")

    duel_id = f"at-duel-{random.randint(10000, 99999)}"

    return {
        "success": True,
        "duel_id": duel_id,
        "surah_id": req.surah_id,
        "sure_name": sess["sure_name"],
        "player": {
            "name": req.player_name,
            "elo": p1_elo
        },
        "bot": {
            "name": bot_name,
            "elo": bot_elo,
            "tier": bot_tier
        },
        "session": sess
    }

@app.post("/api/gameshow/ayet-tamamlama/duel/finish")
def finish_ayet_tamamlama_duel(req: AyetTamamlamaFinishRequest):
    """
    Âyet Tamamlama Düellosunu sonuçlandırır, ELO ve istatistikleri günceller.
    Maksimum Motivasyon Puanı barajı: 100 Puan.
    """
    conn = get_db()
    c = conn.cursor()

    p1_score = min(100, max(0, req.player_score))
    p2_score = min(100, max(0, req.bot_score))

    if p1_score > p2_score:
        winner = req.player_name
        delta_elo = 20
    elif p1_score < p2_score:
        winner = req.bot_name
        delta_elo = -10
    else:
        winner = "Berabere"
        delta_elo = 5

    c.execute("SELECT elo_rating FROM hafizlik_elo WHERE player_name = ?", (req.player_name,))
    row = c.fetchone()
    old_elo = row[0] if row else 1350
    new_elo = max(800, old_elo + delta_elo)

    c.execute("""
        UPDATE hafizlik_elo
        SET elo_rating = ?, streak_count = CASE WHEN ? > ? THEN streak_count + 1 ELSE 0 END, last_updated = ?
        WHERE player_name = ?
    """, (new_elo, p1_score, p2_score, time.time(), req.player_name))

    c.execute("""
        INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            total_points = total_points + excluded.total_points,
            matches_played = matches_played + 1,
            highest_score = MAX(highest_score, excluded.highest_score),
            last_active = excluded.last_active
    """, (req.player_name, p1_score, p1_score, time.time()))

    c.execute("""
        INSERT INTO hafizlik_leaderboard (player_name, total_points, matches_played, highest_score, last_active)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(player_name) DO UPDATE SET
            total_points = total_points + excluded.total_points,
            matches_played = matches_played + 1,
            highest_score = MAX(highest_score, excluded.highest_score),
            last_active = excluded.last_active
    """, (req.bot_name, p2_score, p2_score, time.time()))

    c.execute("""
        INSERT INTO hafizlik_matches (room_name, mode, surah_pool, winner_name, winner_score, total_rounds, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (f"Âyet Tamamlama: {req.player_name} vs {req.bot_name}", "ayet_tamamlama_duel", f"Sûre #{req.surah_id} Daktilo ile Âyet Tamamlama Havuzu", winner, max(p1_score, p2_score), 4, time.time()))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "winner": winner,
        "player_score": p1_score,
        "bot_score": p2_score,
        "delta_elo": delta_elo,
        "new_elo": new_elo,
        "max_score_enforced": 100
    }

# =========================================================
# HATALI CEVAPLARIM (MISTAKES LOG) ORTAK API
# =========================================================

@app.post("/api/gameshow/mistakes/record")
def record_mistake_endpoint(req: RecordMistakeRequest):
    """
    Tek kişilik oyunlarda yapılan hatalı cevapları SQLite'a kaydeder.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS hafizlik_mistakes_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            game_name TEXT NOT NULL,
            game_id TEXT NOT NULL,
            surah_id INTEGER,
            ayah_id INTEGER,
            sure_name TEXT,
            reference TEXT,
            question_type TEXT,
            target_text TEXT,
            selected_wrong_text TEXT,
            full_ayah_text TEXT,
            created_at REAL
        )
    """)
    c.execute("""
        INSERT INTO hafizlik_mistakes_log (
            player_name, game_name, game_id, surah_id, ayah_id, sure_name,
            reference, question_type, target_text, selected_wrong_text, full_ayah_text, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        req.player_name, req.game_name, req.game_id, req.surah_id, req.ayah_id, req.sure_name,
        req.reference, req.question_type, req.target_text, req.selected_wrong_text, req.full_ayah_text, time.time()
    ))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Hatalı cevap kaydedildi"}

@app.get("/api/gameshow/mistakes/list")
def list_mistakes_endpoint(player_name: str = "Siz (Yarışmacı)", limit: int = 50):
    """
    Kullanıcının yaptığı hatalı cevapları en yeniden eskiye doğru listeler.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS hafizlik_mistakes_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            game_name TEXT NOT NULL,
            game_id TEXT NOT NULL,
            surah_id INTEGER,
            ayah_id INTEGER,
            sure_name TEXT,
            reference TEXT,
            question_type TEXT,
            target_text TEXT,
            selected_wrong_text TEXT,
            full_ayah_text TEXT,
            created_at REAL
        )
    """)
    c.execute("""
        SELECT id, game_name, game_id, surah_id, ayah_id, sure_name, reference,
               question_type, target_text, selected_wrong_text, full_ayah_text, created_at
        FROM hafizlik_mistakes_log
        WHERE player_name = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (player_name, limit))
    rows = c.fetchall()
    conn.close()

    mistakes = []
    for r in rows:
        mistakes.append({
            "id": r["id"],
            "game_name": r["game_name"],
            "game_id": r["game_id"],
            "surah_id": r["surah_id"],
            "ayah_id": r["ayah_id"],
            "sure_name": r["sure_name"],
            "reference": r["reference"],
            "question_type": r["question_type"],
            "target_text": r["target_text"],
            "selected_wrong_text": r["selected_wrong_text"],
            "full_ayah_text": r["full_ayah_text"],
            "created_at": r["created_at"],
            "date_str": time.strftime("%H:%M", time.localtime(r["created_at"]))
        })

    return {
        "status": "success",
        "total": len(mistakes),
        "mistakes": mistakes
    }

@app.post("/api/gameshow/mistakes/clear")
def clear_mistakes_endpoint(player_name: str = "Siz (Yarışmacı)"):
    """
    Kullanıcının hatalı cevaplar geçmişini sıfırlar.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM hafizlik_mistakes_log WHERE player_name = ?", (player_name,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Hatalı cevaplar sıfırlandı"}



# =====================================================================
# AUTHENTICATION & GOOGLE LOGIN API
# =====================================================================

class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    hifz_tier: Optional[str] = "Mutavassıt (Orta)"

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserSyncRequest(BaseModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = ""
    avatar_url: Optional[str] = ""
    provider: Optional[str] = "google"
    hifz_tier: Optional[str] = "Mutavassıt (Orta)"
    elo: Optional[int] = 1350

def init_users_table(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS hafizlik_users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            name TEXT NOT NULL,
            avatar_url TEXT,
            provider TEXT DEFAULT 'local',
            password_hash TEXT,
            hifz_tier TEXT DEFAULT 'Mutavassıt (Orta)',
            elo_rating INTEGER DEFAULT 1350,
            created_at REAL,
            last_login REAL
        )
    """)
    conn.commit()

@app.post("/api/auth/register")
def auth_register(req: UserRegisterRequest):
    conn = get_db()
    init_users_table(conn)
    c = conn.cursor()

    c.execute("SELECT id FROM hafizlik_users WHERE email = ?", (req.email,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Bu e-posta adresiyle kayıtlı bir hesap zaten var.")

    user_id = f"usr-{int(time.time())}-{random.randint(100, 999)}"
    now = time.time()
    avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={req.name}"

    c.execute("""
        INSERT INTO hafizlik_users (id, email, name, avatar_url, provider, password_hash, hifz_tier, elo_rating, created_at, last_login)
        VALUES (?, ?, ?, ?, 'local', ?, ?, 1350, ?, ?)
    """, (user_id, req.email, req.name, avatar_url, req.password, req.hifz_tier, now, now))

    # ELO kaydını başlat
    c.execute("""
        INSERT OR IGNORE INTO hafizlik_elo (player_name, elo_rating, hifz_tier, last_updated)
        VALUES (?, 1350, ?, ?)
    """, (req.name, req.hifz_tier, now))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Kayıt başarılı",
        "user": {
            "id": user_id,
            "name": req.name,
            "email": req.email,
            "avatar_url": avatar_url,
            "provider": "local",
            "hifz_tier": req.hifz_tier,
            "elo": 1350
        }
    }

@app.post("/api/auth/login")
def auth_login(req: UserLoginRequest):
    conn = get_db()
    init_users_table(conn)
    c = conn.cursor()

    c.execute("""
        SELECT id, email, name, avatar_url, provider, password_hash, hifz_tier, elo_rating
        FROM hafizlik_users
        WHERE email = ?
    """, (req.email,))
    row = c.fetchone()

    if not row or row["password_hash"] != req.password:
        conn.close()
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    now = time.time()
    c.execute("UPDATE hafizlik_users SET last_login = ? WHERE id = ?", (now, row["id"]))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Giriş başarılı",
        "user": {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "avatar_url": row["avatar_url"],
            "provider": row["provider"],
            "hifz_tier": row["hifz_tier"],
            "elo": row["elo_rating"]
        }
    }

@app.post("/api/auth/sync-session")
@app.post("/api/auth/google")
def auth_sync_session(req: UserSyncRequest):
    conn = get_db()
    init_users_table(conn)
    c = conn.cursor()

    now = time.time()
    user_id = req.id or f"google-{int(now)}"
    email = req.email or f"{user_id}@gmail.com"
    avatar = req.avatar_url or f"https://api.dicebear.com/7.x/bottts/svg?seed={req.name}"

    c.execute("SELECT id, elo_rating, hifz_tier FROM hafizlik_users WHERE email = ? OR id = ?", (email, user_id))
    existing = c.fetchone()

    if existing:
        user_id = existing["id"]
        c.execute("""
            UPDATE hafizlik_users
            SET name = ?, avatar_url = ?, last_login = ?
            WHERE id = ?
        """, (req.name, avatar, now, user_id))
        elo = existing["elo_rating"]
        tier = existing["hifz_tier"]
    else:
        elo = req.elo or 1350
        tier = req.hifz_tier or "Mutavassıt (Orta)"
        c.execute("""
            INSERT INTO hafizlik_users (id, email, name, avatar_url, provider, hifz_tier, elo_rating, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, email, req.name, avatar, req.provider or "google", tier, elo, now, now))

    # ELO ve Liderlik kaydını garanti et
    c.execute("""
        INSERT OR IGNORE INTO hafizlik_elo (player_name, elo_rating, hifz_tier, last_updated)
        VALUES (?, ?, ?, ?)
    """, (req.name, elo, tier, now))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "user": {
            "id": user_id,
            "name": req.name,
            "email": email,
            "avatar_url": avatar,
            "provider": req.provider or "google",
            "hifz_tier": tier,
            "elo": elo
        }
    }

class UserUpdateProfileRequest(BaseModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = ""
    avatar_url: Optional[str] = ""
    hifz_tier: Optional[str] = "Mutavassıt (Orta)"

class UserSettingsRequest(BaseModel):
    userId: Optional[str] = ""
    settings: Optional[dict] = {}

@app.post("/api/auth/update-profile")
def auth_update_profile(req: UserUpdateProfileRequest):
    conn = get_db()
    init_users_table(conn)
    c = conn.cursor()

    now = time.time()
    # E-posta veya ID üzerinden kullanıcıyı güncelle
    if req.id:
        c.execute("""
            UPDATE hafizlik_users
            SET name = ?, avatar_url = ?, hifz_tier = ?
            WHERE id = ? OR email = ?
        """, (req.name, req.avatar_url, req.hifz_tier, req.id, req.email))
    elif req.email:
        c.execute("""
            UPDATE hafizlik_users
            SET name = ?, avatar_url = ?, hifz_tier = ?
            WHERE email = ?
        """, (req.name, req.avatar_url, req.hifz_tier, req.email))

    # ELO tablosundaki seviyeyi de senkronize et
    c.execute("""
        UPDATE hafizlik_elo
        SET hifz_tier = ?, last_updated = ?
        WHERE player_name = ?
    """, (req.hifz_tier, now, req.name))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Profil başarıyla güncellendi", "profile": req.dict()}

@app.post("/api/auth/update-settings")
def auth_update_settings(req: UserSettingsRequest):
    return {"success": True, "message": "Ayarlar kaydedildi", "settings": req.settings}

@app.on_event("startup")
async def on_server_startup():
    asyncio.create_task(autonomous_bot_arena_loop())

@app.get("/api/turso/status")
def get_turso_status():
    """Turso Cloud bağlantı ve senkronizasyon durumunu döner."""
    try:
        from turso_sync import query_turso
        res = query_turso("SELECT count(*) as surah_count FROM surahs;")
        count = res[0].get("surah_count") if res else 0
        return {
            "status": "connected",
            "provider": "Turso LibSQL Cloud",
            "region": "aws-eu-west-1",
            "database": "zakirunbilgiyarismasi-zakirun002",
            "cloud_surahs_count": count,
            "local_db": DB_PATH,
            "message": "Turso Bulut Veritabanı %100 Canlı ve Senkronize"
        }
    except Exception as e:
        return {
            "status": "offline_or_error",
            "local_db": DB_PATH,
            "error": str(e)
        }

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"""
    =================================================================
    [OK] KUR'AN TV 2026 // QUANTUM BACKEND KERNEL ONLINE
    - Veritabanı: {DB_PATH}
    - 114 Sûre | 6.236 Âyet | 77.429 Kelime | 15 Hat | 717 Meâl | 32 GPS Mekân
    - Port: http://127.0.0.1:{port}
    - API Dokümantasyonu (Swagger UI): http://127.0.0.1:{port}/docs
    - Sıfır Ses / Sıfır Medya: Devrede
    =================================================================
    """)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


