# -*- coding: utf-8 -*-
"""كل عمليات قاعدة البيانات"""
import os
import shutil
import uuid
import sqlite3
from datetime import date, datetime

from config import (
    DB_PATH, BACKUPS_DIR,
    DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASS,
)
from utils import hash_password


class Database:
    """طبقة قاعدة البيانات — كل الـ queries هنا"""

    def __init__(self, path=None):
        self.path = path or DB_PATH

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ================= أدوات عامة =================
    def query(self, sql, params=(), fetch=True):
        """تنفيذ query مع إدارة آمنة للاتصال"""
        conn = self._connect()
        try:
            cur = conn.execute(sql, params)
            result = cur.fetchall() if fetch else None
            conn.commit()
            return result
        finally:
            conn.close()

    def query_one(self, sql, params=()):
        rows = self.query(sql, params, fetch=True)
        return rows[0] if rows else None

    # ================= Schema =================
    def init_schema(self):
        conn = self._connect()
        c = conn.cursor()
        try:
            c.execute('''CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS technicians (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )''')    
            c.execute('''CREATE TABLE IF NOT EXISTS receptionists (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS patients (
                serial INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_uid TEXT,
                patient_name TEXT NOT NULL,
                age INTEGER,
                phone TEXT,
                exam_type TEXT,
                price REAL,
                doctor_name TEXT,
                technician TEXT,
                receptionist TEXT,
                notes TEXT,
                exam_date TEXT,
                report_path TEXT,
                created_at TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )''')

            # Migration - إضافة أعمدة جديدة للـ DB القديمة
            existing = [r[1] for r in c.execute("PRAGMA table_info(patients)").fetchall()]
            migrations = {
                'phone': 'TEXT', 'technician': 'TEXT', 'report_path': 'TEXT',
                'patient_uid': 'TEXT', 'notes': 'TEXT', 'created_at': 'TEXT',
            }
            for col, typ in migrations.items():
                if col not in existing:
                    try:
                        c.execute("ALTER TABLE patients ADD COLUMN {} {}".format(col, typ))
                    except sqlite3.OperationalError:
                        pass

            # ملء patient_uid للسجلات القديمة
            rows = c.execute(
                "SELECT serial, patient_name, phone FROM patients "
                "WHERE patient_uid IS NULL OR patient_uid = ''"
            ).fetchall()
            for serial, name, phone in rows:
                uid = self._generate_uid(name or '', phone or '')
                c.execute("UPDATE patients SET patient_uid=? WHERE serial=?", (uid, serial))

            # فحوصات افتراضية
            if c.execute("SELECT COUNT(*) FROM exams").fetchone()[0] == 0:
                c.execute("INSERT INTO exams (name, price) VALUES (?, ?)", ('US & DOPPLER', 350))
                c.execute("INSERT INTO exams (name, price) VALUES (?, ?)", ('Panorama', 200))

            # بيانات الأدمن الافتراضية
            if not c.execute("SELECT value FROM settings WHERE key='admin_pass_hash'").fetchone():
                c.execute("INSERT INTO settings (key, value) VALUES (?, ?)",
                          ('admin_pass_hash', hash_password(DEFAULT_ADMIN_PASS)))
                c.execute("INSERT INTO settings (key, value) VALUES (?, ?)",
                          ('admin_user', DEFAULT_ADMIN_USER))

            conn.commit()
        finally:
            conn.close()

    # ================= Exams =================
    def get_exams(self):
        return self.query("SELECT name, price FROM exams ORDER BY name")

    def add_exam(self, name, price):
        self.query("INSERT INTO exams (name, price) VALUES (?, ?)", (name, price), fetch=False)

    def delete_exam(self, name):
        self.query("DELETE FROM exams WHERE name=?", (name,), fetch=False)

    # ================= Doctors =================
    def get_doctors(self):
        return [r[0] for r in self.query("SELECT name FROM doctors ORDER BY name")]

    def add_doctor(self, name):
        self.query("INSERT INTO doctors (name) VALUES (?)", (name,), fetch=False)

    def delete_doctor(self, name):
        self.query("DELETE FROM doctors WHERE name=?", (name,), fetch=False)

    # ================= Technicians =================
    def get_technicians(self):
        return [r[0] for r in self.query("SELECT name FROM technicians ORDER BY name")]

    def add_technician(self, name):
        self.query("INSERT INTO technicians (name) VALUES (?)", (name,), fetch=False)

    def delete_technician(self, name):
        self.query("DELETE FROM technicians WHERE name=?", (name,), fetch=False)

        # ================= Receptionists =================
    def get_receptionists(self):
        return [r[0] for r in self.query("SELECT name FROM receptionists ORDER BY name")]

    def add_receptionist(self, name):
        self.query("INSERT INTO receptionists (name) VALUES (?)", (name,), fetch=False)

    def delete_receptionist(self, name):
        self.query("DELETE FROM receptionists WHERE name=?", (name,), fetch=False)    

    # ================= Patients =================
    def _generate_uid(self):
        # بنجيب أعلى رقم كود موجود في الداتابيز
        last = self.query_one("SELECT MAX(CAST(SUBSTR(patient_uid, 2) AS INTEGER)) FROM patients WHERE patient_uid LIKE 'P%'")
        
        if last and last[0] is not None:
            new_num = last[0] + 1
        else:
            new_num = 1
            
        # بيرجع مثلا P0001 أو P0015
        return f"P{new_num:04d}"

    def add_patient(self, data):
        phone = data.get('phone', '').strip()
        uid = None
        
        # لو في رقم تليفون، بندور عليه الأول
        if phone:
            existing = self.query_one("SELECT patient_uid FROM patients WHERE phone = ?", (phone,))
            if existing and existing[0]:
                uid = existing[0] # المريض قديم، هنستخدم نفس الكود بتاعه
                
        # لو المريض جديد أو مفيش تليفون، بنعمل كود جديد
        if not uid:
            uid = self._generate_uid()
            
        self.query(
            '''INSERT INTO patients
            (patient_uid, patient_name, age, phone, exam_type, price,
             doctor_name, technician, receptionist, notes, exam_date, report_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (uid, data['patient_name'], data.get('age', 0), phone,
             data['exam_type'], data.get('price', 0), data.get('doctor_name', ''),
             data.get('technician', ''), data.get('receptionist', ''),
             data.get('notes', ''), data.get('exam_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
             data.get('report_path', ''), datetime.now().isoformat()),
            fetch=False
        )

    def update_patient(self, serial, data):
        self.query(
            '''UPDATE patients SET
            patient_name=?, age=?, phone=?, exam_type=?, price=?,
            doctor_name=?, technician=?, receptionist=?, notes=?
            WHERE serial=?''',
            (data['patient_name'], data.get('age', 0), data.get('phone', ''),
             data['exam_type'], data.get('price', 0), data.get('doctor_name', ''),
             data.get('technician', ''), data.get('receptionist', ''),
             data.get('notes', ''), serial),
            fetch=False
        )

    def delete_patient(self, serial):
        """يعيد مسار التقرير المرتبط (لحذفه من القرص)"""
        report = self.get_report_path(serial)
        self.query("DELETE FROM patients WHERE serial=?", (serial,), fetch=False)
        return report

    def get_report_path(self, serial):
        r = self.query_one("SELECT report_path FROM patients WHERE serial=?", (serial,))
        return r[0] if r else None

    def get_all_patients(self):
        return self.query("SELECT * FROM patients ORDER BY serial ASC")

    def search_patients(self, q):
        like = "%{}%".format(q)
        return self.query(
            '''SELECT * FROM patients
            WHERE patient_name LIKE ? OR phone LIKE ? OR exam_type LIKE ?
               OR exam_date LIKE ? OR doctor_name LIKE ? OR technician LIKE ?
            ORDER BY serial ASC''',
            (like, like, like, like, like, like)
        )

    def filter_by_date(self, date_from, date_to):
        sql = "SELECT * FROM patients WHERE 1=1"
        params = []
        if date_from:
            sql += " AND exam_date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND exam_date <= ?"
            params.append(date_to)
        sql += " ORDER BY serial ASC"
        return self.query(sql, tuple(params))

    def get_patient_history(self, uid):
        return self.query(
            "SELECT * FROM patients WHERE patient_uid = ? ORDER BY exam_date DESC",
            (uid,)
        )

    def update_report_path(self, serial, path):
        self.query("UPDATE patients SET report_path=? WHERE serial=?", (path, serial), fetch=False)

    # ================= Analytics =================
    def get_monthly_stats(self, month_prefix):
        return self.query_one(
            "SELECT COUNT(*), COALESCE(SUM(price), 0) FROM patients WHERE exam_date LIKE ?",
            ("{}%".format(month_prefix),)
        )

    def get_total_stats(self):
        return self.query_one("SELECT COUNT(*), COALESCE(SUM(price), 0) FROM patients")

    def get_monthly_trends(self):
        return self.query(
            "SELECT substr(exam_date, 1, 7) as month, COUNT(*) "
            "FROM patients GROUP BY month ORDER BY month"
        )

    def get_exam_distribution(self):
        return self.query("SELECT exam_type, COUNT(*) FROM patients GROUP BY exam_type")

    def get_technician_distribution(self):
        return self.query(
            "SELECT technician, COUNT(*) FROM patients "
            "WHERE technician != '' AND technician IS NOT NULL GROUP BY technician"
        )

    # ================= Settings =================
    def get_setting(self, key, default=None):
        r = self.query_one("SELECT value FROM settings WHERE key=?", (key,))
        return r[0] if r else default

    def set_setting(self, key, value):
        self.query("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                   (key, value), fetch=False)

    def verify_admin(self, username, password):
        stored_user = self.get_setting('admin_user', DEFAULT_ADMIN_USER)
        stored_hash = self.get_setting('admin_pass_hash', hash_password(DEFAULT_ADMIN_PASS))
        return username == stored_user and hash_password(password) == stored_hash

    def change_admin_password(self, new_password):
        self.set_setting('admin_pass_hash', hash_password(new_password))

    # ================= Backup =================
    def backup(self):
        if not os.path.exists(self.path):
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUPS_DIR, "albayt_backup_{}.db".format(timestamp))
        try:
            shutil.copy(self.path, backup_path)
            self._cleanup_old_backups(keep=10)
            self.set_setting('last_backup', datetime.now().isoformat())
            return backup_path
        except Exception:
            return None

    def _cleanup_old_backups(self, keep=10):
        try:
            files = sorted(
                [os.path.join(BACKUPS_DIR, f) for f in os.listdir(BACKUPS_DIR) if f.endswith('.db')],
                key=os.path.getmtime, reverse=True
            )
            for f in files[keep:]:
                try:
                    os.remove(f)
                except OSError:
                    pass
        except Exception:
            pass

    def needs_backup(self, hours=24):
        last = self.get_setting('last_backup')
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
            return (datetime.now() - last_dt).total_seconds() > hours * 3600
        except (ValueError, TypeError):
            return True