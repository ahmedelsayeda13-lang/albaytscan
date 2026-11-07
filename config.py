# -*- coding: utf-8 -*-
"""إعدادات التطبيق العامة"""
import os
import sys

APP_NAME = "AL BAYT SCAN"
APP_VERSION = "2.0.0"


def get_base_dir():
    """مسار التطبيق — يتعامل مع exe والـ dev mode"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
DB_PATH = os.path.join(BASE_DIR, "albayt_center.db")
REPORTS_DIR = os.path.join(BASE_DIR, "Reports")
BACKUPS_DIR = os.path.join(BASE_DIR, "Backups")
EXPORTS_DIR = os.path.join(BASE_DIR, "Exports")

for _d in (REPORTS_DIR, BACKUPS_DIR, EXPORTS_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except OSError:
        pass

# ================= الثيم =================
BG_COLOR = "#010812"
CARD_BG = "#041424"
ACCENT_COLOR = "#00E5FF"
TEXT_MAIN = "#FFFFFF"
TEXT_MUTED = "#557A95"
SUCCESS_COLOR = "#00C896"
WARNING_COLOR = "#F39C12"
DANGER_COLOR = "#E74C3C"
INFO_COLOR = "#2980B9"
NAV_BG = "#010A14"
BORDER_COLOR = "#073656"

# ================= الأدمن الافتراضي =================
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASS = "12345"