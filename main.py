# -*- coding: utf-8 -*-
import sys
import traceback
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from licensing import check_license, show_activation_window

def main():
    try:
        # فحص الترخيص
        status, msg, days_left = check_license()

        if status == "TAMPERED":
            messagebox.showerror("خطأ أمني", msg)
            sys.exit(1)
            
        elif status == "EXPIRED":
            show_activation_window(status, "انتهت صلاحية البرنامج. يرجى إدخال كود تفعيل جديد.")
            return # البرنامج مش هيكمل
            
        elif status == "TRIAL":
            # تنبيه بسيط لو باقي 5 أيام أو أقل
            if days_left <= 5:
                messagebox.showwarning("تنبيه", f"الفترة التجريبية تنتهي بعد {days_left} أيام. يرجى التواصل مع المطور للتجديد.")
            
        # لو الترخيص سليم أو في فترة التجربة، البرنامج هيفتح عادي
        from app import BaytScanOS
        app = BaytScanOS()
        app.mainloop()
        
    except Exception:
        traceback.print_exc()
        try:
            messagebox.showerror("خطأ فادح", "حدث خطأ غير متوقع:\n" + traceback.format_exc(limit=3))
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()