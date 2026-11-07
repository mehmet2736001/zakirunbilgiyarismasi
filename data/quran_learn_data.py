"""
ZÂKİRÛN & DİYANET KUR'AN ÖĞRENME PORTALI MÜFREDAT MOTORU
======================================================
Diyanet İşleri Başkanlığı Kur'an Portalı (https://kuran.diyanet.gov.tr/elifba)
resmi müfredatı, 4 ana bölüm, 30+ ana konu, 91 ders ünitesi ve 1.890+ otantik ses kaydı
ile %100 senkronize edilmiş veri modülü.
"""

import os
import json

CURRICULUM_FILE = os.path.join(os.path.dirname(__file__), "diyanet_curriculum_v2.json")

def _load_diyanet_curriculum():
    if os.path.exists(CURRICULUM_FILE):
        try:
            with open(CURRICULUM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("curriculum", []), data.get("parts", [])
        except Exception as e:
            print(f"Error loading {CURRICULUM_FILE}: {e}")
    return [], []

QURAN_LEARNING_CURRICULUM, DIYANET_PARTS = _load_diyanet_curriculum()

def get_curriculum_summary():
    """Tüm müfredatın özetini döner."""
    summary = []
    for d in QURAN_LEARNING_CURRICULUM:
        summary.append({
            "id": d["id"],
            "stage": d.get("stage", 1),
            "stage_title": d.get("stage_title", ""),
            "part_key": d.get("part_key", ""),
            "chapter_key": d.get("chapter_key", ""),
            "chapter_number": d.get("chapter_number", 0),
            "lesson_key": d.get("lesson_key", ""),
            "title": d["title"],
            "subtitle": d.get("subtitle", d["title"]),
            "intro": d.get("intro", ""),
            "rule_badge": d.get("rule_badge", ""),
            "items_count": len(d.get("items", [])),
            "groups_count": len(d.get("groups", [])),
            "quiz_count": len(d.get("quiz", []))
        })
    return summary

def get_lesson_by_id(lesson_id: int):
    """ID'ye göre dersin tam içeriğini döner."""
    for d in QURAN_LEARNING_CURRICULUM:
        if d["id"] == lesson_id:
            return d
    return None

def get_lessons_by_stage(stage: int):
    """Aşamaya göre dersleri filtreler."""
    return [d for d in QURAN_LEARNING_CURRICULUM if d.get("stage") == stage]

def get_lessons_by_part(part_key: str):
    """Bölüme göre dersleri filtreler."""
    return [d for d in QURAN_LEARNING_CURRICULUM if d.get("part_key") == part_key]
