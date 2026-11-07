# -*- coding: utf-8 -*-
"""دوال مساعدة"""
import os
import sys
import re
import hashlib
from datetime import date

import arabic_reshaper
from bidi.algorithm import get_display

from config import BASE_DIR


def resource_path(relative_path):
    """إيجاد الملفات سواء في وضع التطوير أو EXE"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        ext_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(ext_path):
            return ext_path
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(BASE_DIR, relative_path)


def find_image(file_name):
    base_name, ext = os.path.splitext(file_name)
    candidates = [file_name, base_name + ext + ext, base_name]
    for name in candidates:
        p = resource_path(name)
        if os.path.exists(p):
            return p
    return None


def arabic_text(text):
    """تحويل النص العربي لعرضه في Matplotlib"""
    if not text:
        return ""
    try:
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


def get_safe_int(val, default=0):
    try:
        return int(float(val)) if val else default
    except (ValueError, TypeError):
        return default


def get_safe_float(val, default=0.0):
    try:
        return float(val) if val else default
    except (ValueError, TypeError):
        return default


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def validate_phone(phone):
    """التحقق من رقم الهاتف (مصري 11 رقم)"""
    if not phone:
        return True, ""
    digits = re.sub(r'\D', '', phone)
    if len(digits) != 11:
        return False, "رقم الهاتف يجب أن يكون 11 رقماً"
    return True, ""


def format_currency(value):
    try:
        return "{:,.0f}".format(float(value))
    except (ValueError, TypeError):
        return "0"


def calculate_age_from_dob(year, month, day):
    """حساب السن من تاريخ الميلاد"""
    try:
        birth = date(int(year), int(month), int(day))
        today = date.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age if age >= 0 else None
    except (ValueError, TypeError):
        return None


def open_file(path):
    """فتح ملف بالنظام الافتراضي"""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system('open "{}"'.format(path))
        else:
            os.system('xdg-open "{}"'.format(path))
        return True
    except Exception:
        return False