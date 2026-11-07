import os
import sys
import uuid
import socket
import hashlib
import base64
import json
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime, timedelta

# ==========================================
# ⚠️ السر بتاعك (متغيرهوش أبداً بعد كده) ⚠️
SECRET_KEY = "AlBaytScan_SecretKey_2024_Ahmed"
LICENSE_FILE = "license.dat"
TRIAL_FILE = "trial.dat"
TRIAL_DAYS = 30

def get_hwid():
    """توليد كود فريد للجهاز (MAC + PC Name)"""
    mac = hex(uuid.getnode())
    pc_name = socket.gethostname()
    raw_id = f"{mac}-{pc_name}"
    return hashlib.sha256(raw_id.encode()).hexdigest()[:12].upper()

def _encrypt_data(data_str):
    """تشفير البيانات عشان محدش يعدل الملفات"""
    encoded = base64.b64encode(data_str.encode()).decode()
    sig = hashlib.sha256((data_str + SECRET_KEY).encode()).hexdigest()[:10]
    return f"{encoded}|{sig}"

def _decrypt_data(enc_str):
    """فك التشفير والتحقق من سلامة البيانات"""
    try:
        encoded, sig = enc_str.strip().split("|")
        data_str = base64.b64decode(encoded.encode()).decode()
        expected_sig = hashlib.sha256((data_str + SECRET_KEY).encode()).hexdigest()[:10]
        if sig == expected_sig:
            return data_str
    except Exception:
        pass
    return None

def check_license():
    """
    فحص الترخيص. بترجع tuple: (status, message, days_left)
    Status: 'ACTIVE', 'TRIAL', 'EXPIRED', 'TAMPERED'
    """
    today = datetime.now().date()
    hwid = get_hwid()

    # 1. فحص الترخيص المدفوع (لو موجود)
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r") as f:
                decrypted = _decrypt_data(f.read())
            if decrypted:
                data = json.loads(decrypted)
                if data.get("hwid") == hwid:
                    expiry = datetime.strptime(data["expiry"], "%Y-%m-%d").date()
                    if today <= expiry:
                        return "ACTIVE", "License is valid", (expiry - today).days
                    else:
                        return "EXPIRED", "انتهت صلاحية الترخيص", 0
        except Exception:
            pass
        return "TAMPERED", "ملف الترخيص تالف", 0

    # 2. فحص الفترة التجريبية (Trial)
    if not os.path.exists(TRIAL_FILE):
        # أول تشغيل للبرنامج
        trial_data = {
            "start": today.strftime("%Y-%m-%d"),
            "last_run": today.strftime("%Y-%m-%d")
        }
        with open(TRIAL_FILE, "w") as f:
            f.write(_encrypt_data(json.dumps(trial_data)))
        return "TRIAL", "بدأت الفترة التجريبية", TRIAL_DAYS

    try:
        with open(TRIAL_FILE, "r") as f:
            decrypted = _decrypt_data(f.read())
        if not decrypted:
            return "TAMPERED", "ملف التجربة تالف", 0
        
        trial_data = json.loads(decrypted)
        start_date = datetime.strptime(trial_data["start"], "%Y-%m-%d").date()
        last_run = datetime.strptime(trial_data["last_run"], "%Y-%m-%d").date()

        # التحقق من التلاعب في تاريخ الكمبيوتر (رجع التاريخ لورا)
        if today < last_run:
            return "TAMPERED", "تحذير: تم تغيير تاريخ الكمبيوتر للخلف", 0

        # تحديث تاريخ آخر تشغيل
        trial_data["last_run"] = today.strftime("%Y-%m-%d")
        with open(TRIAL_FILE, "w") as f:
            f.write(_encrypt_data(json.dumps(trial_data)))

        # حساب الأيام المتبقية
        days_passed = (today - start_date).days
        days_left = TRIAL_DAYS - days_passed

        if days_left > 0:
            return "TRIAL", "الفترة التجريبية سارية", days_left
        else:
            return "EXPIRED", "انتهت الفترة التجريبية", 0

    except Exception:
        return "TAMPERED", "حدث خطأ في قراءة ملف التجربة", 0

def activate_license(entered_code):
    """تفعيل البرنامج بكود جديد"""
    hwid = get_hwid()
    try:
        # الكود هيكون شكله كده: 2024-12-31-ABCDEF123456
        parts = entered_code.strip().split("-")
        if len(parts) != 4:
            return False, "صيغة الكود غير صحيحة"
            
        expiry_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
        key_hwid = parts[3].upper()
        
        # التأكد إن الكود يخص هذا الجهاز
        if key_hwid != hwid:
            return False, "هذا الكود لا يخص هذا الجهاز"
            
        expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        if datetime.now().date() > expiry:
            return False, "التاريخ المرفق بالكود قديم بالفعل"

        # حفظ الترخيص
        license_data = {
            "hwid": hwid,
            "expiry": expiry_str,
            "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(LICENSE_FILE, "w") as f:
            f.write(_encrypt_data(json.dumps(license_data)))
            
        return True, "تم التفعيل بنجاح"
    except ValueError:
        return False, "صيغة التاريخ غير صحيحة"
    except Exception:
        return False, "كود غير صالح"

def show_activation_window(status, msg):
    """نافذة التفعيل"""
    root = ctk.CTk()
    root.title("تفعيل النسخة - AL BAYT SCAN")
    root.geometry("500x400")
    root.configure(fg_color="#010812")
    
    ctk.CTkLabel(root, text="AL BAYT SCAN", font=ctk.CTkFont(size=24, weight="bold"), text_color="#00E5FF").pack(pady=(20, 10))
    ctk.CTkLabel(root, text=msg, text_color="#E74C3C", font=ctk.CTkFont(size=14, weight="bold"), wraplength=450).pack(pady=5)
    
    hwid_frame = ctk.CTkFrame(root, fg_color="#041424")
    hwid_frame.pack(pady=10, fill="x", padx=40)
    ctk.CTkLabel(hwid_frame, text="كود الجهاز (أرسله للمطور):", text_color="#FFF").pack(pady=(10,0))
    ctk.CTkLabel(hwid_frame, text=get_hwid(), font=ctk.CTkFont(family="Consolas", size=18, weight="bold"), text_color="#F39C12").pack(pady=(0,10))
    
    code_var = ctk.StringVar()
    ctk.CTkEntry(root, textvariable=code_var, placeholder_text="أدخل كود التفعيل هنا (YYYY-MM-DD-HWID)", width=380, height=40, justify="center").pack(pady=15)
    
    def do_activate():
        success, msg_text = activate_license(code_var.get())
        if success:
            messagebox.showinfo("نجاح", "تم تفعيل البرنامج بنجاح! سيتم فتح البرنامج الآن.")
            root.destroy()
            import subprocess
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit()
        else:
            messagebox.showerror("خطأ", msg_text)
            
    ctk.CTkButton(root, text="تفعيل", fg_color="#00C896", text_color="#000", command=do_activate, height=40, width=200).pack(pady=10)
    
    # زرار للخروج
    ctk.CTkButton(root, text="خروج", fg_color="transparent", border_width=1, text_color="#FFF", command=lambda: sys.exit(), height=30, width=100).pack(pady=5)
    
    root.mainloop()