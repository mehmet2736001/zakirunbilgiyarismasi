"""
ZAKİRUN // TURSO CLOUD NATIVE QUERY & SYNC ENGINE
==================================================
Turso LibSQL Bulut Veritabanı ile çift yönlü iletişim,
senkronizasyon ve canlı sorgulama motoru.
"""

import json
import os
import urllib.request
import urllib.error
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

def get_config_path():
    candidates = [
        os.path.join(CURRENT_DIR, "config.json"),
        os.path.join(PARENT_DIR, "config.json"),
        r"E:\ZAKİRUN.COM\bilgiyarismasi\config.json"
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

CONFIG_PATH = get_config_path()

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

config = load_config()
TURSO_CFG = config.get("turso", {})
TURSO_HTTP_URL = TURSO_CFG.get("http_url")
TURSO_AUTH_TOKEN = TURSO_CFG.get("auth_token")

def query_turso(sql: str, params: list = None):
    """Executes a SQL statement on Turso Cloud via HTTP Pipeline API."""
    cfg = load_config()
    t_cfg = cfg.get("turso", {})
    http_url = t_cfg.get("http_url") or TURSO_HTTP_URL
    token = t_cfg.get("auth_token") or TURSO_AUTH_TOKEN

    if not http_url or not token:
        raise ValueError(f"Turso konfigürasyonu config.json içerisinde bulunamadı. Aranan yol: {CONFIG_PATH}")

    reqs = [{'type': 'execute', 'stmt': {'sql': sql}}]
    reqs.append({'type': 'close'})

    payload = json.dumps({'requests': reqs}).encode('utf-8')
    req = urllib.request.Request(
        http_url,
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        results = data.get('results', [])
        if results and results[0].get('type') == 'ok':
            res_body = results[0].get('response', {}).get('result', {})
            cols = [c.get('name') for c in res_body.get('cols', [])]
            raw_rows = res_body.get('rows', [])
            rows = []
            for r in raw_rows:
                row_dict = {}
                for idx, col_name in enumerate(cols):
                    cell = r[idx]
                    val = cell.get('value') if isinstance(cell, dict) else cell
                    row_dict[col_name] = val
                rows.append(row_dict)
            return rows
        else:
            err = results[0].get('response', {}).get('message', 'Bilinmeyen Turso hatası')
            raise RuntimeError(f"Turso SQL Hatası: {err}")

def test_connection():
    try:
        res = query_turso("SELECT count(*) as surah_count FROM surahs;")
        count = res[0].get("surah_count") if res else 0
        return True, f"Bağlantı Başarılı! Turso'da {count} Sûre kayıtlı."
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ok, msg = test_connection()
    if ok:
        print(f"[OK] {msg}")
    else:
        print(f"[HATA] {msg}")
