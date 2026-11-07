# -*- coding: utf-8 -*-
"""الواجهة الرئيسية"""
import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date

import customtkinter as ctk
from PIL import Image

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import *
from utils import *
from database import Database

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Tahoma', 'DejaVu Sans', 'Segoe UI']


class BaytScanOS(ctk.CTk):

    def __init__(self):
        super().__init__()
        # قاعدة البيانات
        self.db = Database()
        self.db.init_schema()

        # Backup تلقائي
        if self.db.needs_backup(24):
            self.db.backup()

        self.title("{} v{} — Advanced Radiology OS".format(APP_NAME, APP_VERSION))
        self.geometry("1400x820")
        self.resizable(True, True)
        self.state('zoomed')
        self.configure(fg_color=BG_COLOR)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        try:
            icon = find_image("image.png")
            if icon:
                self.wm_iconphoto(False, tk.PhotoImage(file=icon))
        except Exception:
            pass

        # كاش
        self.exams_dict = {}
        self.doctors_list = []
        self.technicians_list = []
        self.receptionists_list = []
        self.reload_catalogs()
        self.receptionists_list = self.db.get_receptionists() or [""]

        # خطوط
        self.font_title = ctk.CTkFont(family="Arial", size=26, weight="bold")
        self.font_main = ctk.CTkFont(family="Arial", size=15, weight="bold")
        self.font_entry = ctk.CTkFont(family="Arial", size=14)
        self.font_small = ctk.CTkFont(family="Arial", size=12)

        self.val_number = (self.register(self._validate_number), '%P')
        self.val_int = (self.register(self._validate_int), '%P')
        self.is_admin_logged_in = False
        self.current_edit_serial = None

        self.setup_ui()
        self.load_patients_data()

        self.dev_label = ctk.CTkLabel(
            self, text="Developer: Ahmed Elsayed | v{}".format(APP_VERSION),
            font=ctk.CTkFont("Consolas", 12, "bold"),
            text_color=ACCENT_COLOR, bg_color=BG_COLOR
        )
        self.dev_label.place(relx=0.5, rely=0.99, anchor="s")

        self.select_tab("home")

    # ================= Helpers =================
    def _validate_number(self, text):
        if text == "":
            return True
        if text.count('.') > 1:
            return False
        return text.replace('.', '').isdigit()

    def _validate_int(self, text):
        return text == "" or text.isdigit()

    def reload_catalogs(self):
        self.exams_dict = dict(self.db.get_exams())
        self.doctors_list = self.db.get_doctors() or [""]
        self.technicians_list = self.db.get_technicians() or [""]
        self.receptionists_list = self.db.get_receptionists() or [""]

    def on_closing(self):
        plt.close('all')
        self.destroy()

    # ================= Navigation =================
    def setup_ui(self):
        nav = ctk.CTkFrame(self, height=70, fg_color=NAV_BG,
                           corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        nav.pack(side="top", fill="x")
        nav.pack_propagate(False)

        ctk.CTkLabel(nav, text=" ⌂ AL BAYT SCAN ",
                     font=ctk.CTkFont("Arial", 22, "bold"),
                     text_color=ACCENT_COLOR).pack(side="left", padx=25)

        nav_container = ctk.CTkFrame(nav, fg_color="transparent")
        nav_container.pack(side="left", padx=20)

        self.nav_buttons = {}
        tabs = [("Home", "home"), ("Scan", "scan"),
                ("Patients", "patients"), ("Admin", "admin")]

        for label, key in tabs:
            btn = ctk.CTkButton(
                nav_container, text=label, font=self.font_main,
                fg_color="transparent", text_color=TEXT_MUTED,
                hover_color="#032038", corner_radius=5, height=40, width=100,
                command=lambda k=key: self.select_tab(k)
            )
            btn.pack(side="left", padx=10)
            self.nav_buttons[key] = btn

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        self.frames = {}
        for _, key in tabs:
            self.frames[key] = ctk.CTkFrame(self.main_container, fg_color="transparent")

        self.build_home_ui(self.frames["home"])
        self.build_scan_ui(self.frames["scan"])
        self.build_patients_ui(self.frames["patients"])
        self.build_admin_ui(self.frames["admin"])

    def select_tab(self, tab_name):
        for key, btn in self.nav_buttons.items():
            if key == tab_name:
                btn.configure(text_color=ACCENT_COLOR, fg_color=CARD_BG,
                              border_width=1, border_color=ACCENT_COLOR)
            else:
                btn.configure(text_color=TEXT_MUTED, fg_color="transparent", border_width=0)

        for frame in self.frames.values():
            frame.pack_forget()

        if tab_name == "patients":
            self.load_patients_data()
        if tab_name == "admin":
            if self.is_admin_logged_in:
                self.show_admin_dashboard()
                self.refresh_analysis_tab()
            else:
                self.show_admin_login()

        self.frames[tab_name].pack(fill="both", expand=True)
        self.dev_label.lift()

    # ================= HOME =================
    def build_home_ui(self, parent):
        try:
            img_path = find_image("image.png")
            if img_path:
                img = Image.open(img_path).resize((300, 300), Image.Resampling.LANCZOS)
                hero = ctk.CTkImage(light_image=img, size=(300, 300))
                ctk.CTkLabel(parent, image=hero, text="",
                             fg_color="transparent").pack(pady=(120, 20))
        except Exception:
            pass

        ctk.CTkButton(
            parent, text="بدء فحص جديد (START SCAN) ➔",
            font=self.font_main, fg_color=ACCENT_COLOR, text_color="#000",
            hover_color="#00B3CC", height=50, width=280, corner_radius=10,
            command=lambda: self.select_tab("scan")
        ).pack(pady=30)

    # ================= SCAN =================
    def build_scan_ui(self, parent):
        card = ctk.CTkFrame(parent, width=620, fg_color=CARD_BG,
                            corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        card.place(relx=0.5, rely=0.5, anchor="center")

        self.scan_title = ctk.CTkLabel(
            card, text="بيانات الفحص (SCAN DATA)",
            font=self.font_title, text_color=ACCENT_COLOR
        )
        self.scan_title.pack(pady=(25, 15))

        # المتغيرات
        self.var_name = ctk.StringVar()
        self.var_age = ctk.StringVar()
        self.var_phone = ctk.StringVar()
        self.var_exam = ctk.StringVar()
        self.var_price = ctk.StringVar()
        self.var_doctor = ctk.StringVar()
        self.var_technician = ctk.StringVar()
        self.var_receptionist = ctk.StringVar()
        self.var_notes = ctk.StringVar()

        self.var_dob_y = ctk.StringVar(value="السنة")
        self.var_dob_m = ctk.StringVar(value="الشهر")
        self.var_dob_d = ctk.StringVar(value="اليوم")

        # منع الأحرف في الهاتف والسن
        self.var_age.trace_add("write", lambda *a: self._force_int(self.var_age))
        self.var_phone.trace_add("write", lambda *a: self._force_int(self.var_phone))

        def calc_age(*args):
            y, m, d = self.var_dob_y.get(), self.var_dob_m.get(), self.var_dob_d.get()
            if y.isdigit() and m.isdigit() and d.isdigit():
                age = calculate_age_from_dob(y, m, d)
                if age is not None:
                    self.var_age.set(str(age))

        self.var_dob_y.trace_add("write", calc_age)
        self.var_dob_m.trace_add("write", calc_age)
        self.var_dob_d.trace_add("write", calc_age)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=40, pady=10)
        form.columnconfigure(0, weight=1)

        def add_row(label, var, row, widget="entry", locked=False, values=None, cmd=None, justify="right"):
            ctk.CTkLabel(form, text=label, font=self.font_main,
                         text_color=TEXT_MAIN).grid(row=row, column=1, sticky="e", pady=8, padx=15)
            if widget == "option":
                w = ctk.CTkOptionMenu(form, variable=var, values=values or [""],
                                      font=self.font_entry, fg_color="#010A14",
                                      text_color=TEXT_MAIN, button_color=ACCENT_COLOR,
                                      button_hover_color="#00B3CC", command=cmd, height=38)
            elif widget == "combo":
                w = ctk.CTkComboBox(form, variable=var, values=values or [""],
                                    font=self.font_entry, fg_color="#010A14",
                                    text_color=TEXT_MAIN, button_color=ACCENT_COLOR,
                                    height=38)
            else:
                w = ctk.CTkEntry(form, textvariable=var, font=self.font_entry,
                                 justify=justify,
                                 state="disabled" if locked else "normal",
                                 fg_color="#010A14", border_color=BORDER_COLOR,
                                 text_color=TEXT_MAIN, height=38)
            w.grid(row=row, column=0, sticky="ew", pady=8, padx=5)
            return w

        add_row("اسم المريض", self.var_name, 0)

        ctk.CTkLabel(form, text="تاريخ الميلاد", font=self.font_main,
                     text_color=TEXT_MAIN).grid(row=1, column=1, sticky="e", pady=8, padx=15)
        dob_frame = ctk.CTkFrame(form, fg_color="transparent")
        dob_frame.grid(row=1, column=0, sticky="ew", pady=8, padx=5)

        ctk.CTkOptionMenu(dob_frame, variable=self.var_dob_y,
                          values=[str(y) for y in range(datetime.now().year, 1920, -1)],
                          width=80, fg_color="#010A14", button_color=ACCENT_COLOR
                          ).pack(side="left", padx=2, expand=True, fill="x")
        ctk.CTkOptionMenu(dob_frame, variable=self.var_dob_m,
                          values=["{:02d}".format(m) for m in range(1, 13)],
                          width=70, fg_color="#010A14", button_color=ACCENT_COLOR
                          ).pack(side="left", padx=2, expand=True, fill="x")
        ctk.CTkOptionMenu(dob_frame, variable=self.var_dob_d,
                          values=["{:02d}".format(d) for d in range(1, 32)],
                          width=70, fg_color="#010A14", button_color=ACCENT_COLOR
                          ).pack(side="left", padx=2, expand=True, fill="x")

        add_row("السن", self.var_age, 2)
        add_row("رقم الهاتف", self.var_phone, 3)
        self.exam_menu = add_row("نوع الفحص", self.var_exam, 4,
                                 widget="option",
                                 values=list(self.exams_dict.keys()),
                                 cmd=self.update_price)
        self.price_entry = add_row("سعر الفحص", self.var_price, 5, locked=True)
        self.doctor_combo = add_row("الطبيب المعالج", self.var_doctor, 6,
                                    widget="combo", values=self.doctors_list)
        self.tech_combo = add_row("الفني", self.var_technician, 7,
                                  widget="combo", values=self.technicians_list)
        self.reception_combo = add_row("الاستقبال", self.var_receptionist, 8, widget="combo", values=self.receptionists_list)
        add_row("ملاحظات", self.var_notes, 9)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=(15, 25))

        ctk.CTkButton(btn_frame, text="حفظ ✚", font=self.font_main,
                      fg_color=SUCCESS_COLOR, hover_color="#009E76",
                      text_color="#000", height=42,
                      command=self.save_patient).pack(side="right", fill="x",
                                                     expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="تفريغ", font=self.font_main,
                      fg_color="transparent", border_width=1, border_color=TEXT_MUTED,
                      text_color=TEXT_MUTED, hover_color="#010A14", height=42,
                      command=self.clear_fields).pack(side="left", padx=5)

    def _force_int(self, var):
        v = var.get()
        clean = ''.join(c for c in v if c.isdigit())
        if v != clean:
            var.set(clean)

    def update_price(self, selected):
        if selected in self.exams_dict:
            self.price_entry.configure(state="normal")
            self.var_price.set(str(self.exams_dict[selected]))
            self.price_entry.configure(state="disabled")

    def _collect_patient_data(self):
        return {
            'patient_name': self.var_name.get().strip(),
            'age': get_safe_int(self.var_age.get()),
            'phone': self.var_phone.get().strip(),
            'exam_type': self.var_exam.get(),
            'price': get_safe_float(self.var_price.get()),
            'doctor_name': self.var_doctor.get(),
            'technician': self.var_technician.get(),
            'receptionist': self.var_receptionist.get(),
            'notes': self.var_notes.get().strip(),
        }

    def _validate_patient(self, data):
        if not data['patient_name']:
            return False, "من فضلك أدخل اسم المريض"
        if not data['exam_type']:
            return False, "من فضلك اختر نوع الفحص"
        if data['age'] < 0 or data['age'] > 150:
            return False, "السن غير صحيح"
        ok, err = validate_phone(data['phone'])
        if not ok:
            return False, err
        return True, ""

    def save_patient(self):
        """حفظ أو تعديل حسب السياق"""
        data = self._collect_patient_data()
        ok, err = self._validate_patient(data)
        if not ok:
            messagebox.showwarning("تنبيه", err)
            return

        try:
            if self.current_edit_serial:
                self.db.update_patient(self.current_edit_serial, data)
                messagebox.showinfo("تم", "تم تعديل بيانات المريض بنجاح ✓")
            else:
                self.db.add_patient(data)
                messagebox.showinfo("تم", "تم حفظ الفحص بنجاح ✓")
            self.clear_fields()
            self.select_tab("patients")
        except Exception as e:
            messagebox.showerror("خطأ", "فشل الحفظ:\n{}".format(e))

    def clear_fields(self):
        self.current_edit_serial = None
        for v in (self.var_name, self.var_age, self.var_phone,
                  self.var_exam, self.var_doctor, self.var_technician,
                  self.var_receptionist, self.var_notes):
            v.set("")
        self.price_entry.configure(state="normal")
        self.var_price.set("")
        self.price_entry.configure(state="disabled")
        self.var_dob_y.set("السنة")
        self.var_dob_m.set("الشهر")
        self.var_dob_d.set("اليوم")
        self.scan_title.configure(text="بيانات الفحص (SCAN DATA)", text_color=ACCENT_COLOR)

    # ================= PATIENTS =================
    def build_patients_ui(self, parent):
        top = ctk.CTkFrame(parent, fg_color=CARD_BG, height=100, corner_radius=10)
        top.pack(fill="x", padx=20, pady=15)

        # الصف الأول: البحث
        row1 = ctk.CTkFrame(top, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(10, 5))

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            row1, textvariable=self.search_var, font=self.font_entry,
            placeholder_text="بحث بالاسم / الهاتف / الطبيب...",
            justify="right", height=40, width=320,
            fg_color="#010A14", border_color=ACCENT_COLOR,
            text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED
        )
        search_entry.pack(side="right", padx=5)
        search_entry.bind('<Return>', lambda e: self.search_data())

        ctk.CTkButton(row1, text="بحث", font=self.font_main,
                      fg_color="#010A14", border_width=1, border_color=ACCENT_COLOR,
                      text_color=ACCENT_COLOR, hover_color="#032038",
                      command=self.search_data, height=40).pack(side="right", padx=5)
        ctk.CTkButton(row1, text="تحديث", font=self.font_main,
                      fg_color="#010A14", text_color=TEXT_MAIN,
                      command=self.load_patients_data, height=40
                      ).pack(side="right", padx=5)

        ctk.CTkButton(row1, text="تصدير CSV 📄", font=self.font_main,
                      fg_color=INFO_COLOR, text_color="#FFF",
                      command=self.export_csv, height=40).pack(side="left", padx=5)

        # الصف الثاني: فلتر التاريخ + أزرار
        row2 = ctk.CTkFrame(top, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 10))

        self.date_from_var = ctk.StringVar()
        self.date_to_var = ctk.StringVar()

        ctk.CTkEntry(row2, textvariable=self.date_from_var, placeholder_text="من (YYYY-MM-DD)",
                     width=140, height=35, justify="center",
                     fg_color="#010A14", text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED).pack(side="right", padx=3)
        ctk.CTkEntry(row2, textvariable=self.date_to_var, placeholder_text="إلى (YYYY-MM-DD)",
                     width=140, height=35, justify="center",
                     fg_color="#010A14", text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED).pack(side="right", padx=3)

        ctk.CTkButton(row2, text="تطبيق الفلتر", font=self.font_small,
                      fg_color=ACCENT_COLOR, text_color="#000", height=35, width=100,
                      command=self.apply_date_filter).pack(side="right", padx=5)

        ctk.CTkButton(row2, text="تعديل المحدد", font=self.font_main,
                      fg_color=WARNING_COLOR, text_color="#000", hover_color="#D68910",
                      command=self.edit_selected_patient, height=35
                      ).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="حذف", font=self.font_main,
                      fg_color=DANGER_COLOR, hover_color="#C0392B",
                      command=self.delete_patient, height=35
                      ).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="السجل التاريخي 📋", font=self.font_main,
                      fg_color="#8E44AD", text_color="#FFF",
                      command=self.show_patient_history, height=35
                      ).pack(side="left", padx=5)

        # الجدول
        table_wrap = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10)
        table_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 12), rowheight=38,
                        borderwidth=0, background=CARD_BG,
                        fieldbackground=CARD_BG, foreground=TEXT_MAIN)
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"),
                        background="#010A14", foreground=ACCENT_COLOR, borderwidth=0)
        style.map("Treeview", background=[('selected', ACCENT_COLOR)],
                  foreground=[('selected', '#000')])

        scroll = ctk.CTkScrollbar(table_wrap, button_color=ACCENT_COLOR)
        scroll.pack(side="right", fill="y", pady=8, padx=(0, 8))

        # أعمدة إضافية مخفية (patient_uid, notes) للقراءة الآمنة
        columns = ("serial", "patient_uid", "name", "age", "phone",
                   "exam", "price", "doctor", "technician", "receptionist",
                   "date", "report_status", "notes")
        display = ("report_status", "date", "receptionist", "technician",
                   "doctor", "price", "exam", "phone", "age", "patient_uid", "name", "serial")

        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings",
                                 displaycolumns=display, yscrollcommand=scroll.set)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)
        scroll.configure(command=self.tree.yview)

        self.tree.tag_configure('oddrow', background="#031A2E", foreground=TEXT_MAIN)
        self.tree.tag_configure('evenrow', background=CARD_BG, foreground=TEXT_MAIN)

                # ربط كل عنوان بالعمود بتاعه بالظبط عشان مفيش حاجة تتلخبط
        headers_map = {
            "serial": "م", "patient_uid": "كود المريض", "name": "الاسم", "age": "السن", "phone": "الهاتف",
            "exam": "الفحص", "price": "السعر", "doctor": "الطبيب", "technician": "الفني",
            "receptionist": "الاستقبال", "date": "التاريخ والوقت", "report_status": "التقرير"
        }
        widths_map = {
            "serial": 45, "patient_uid": 110, "name": 150, "age": 45, "phone": 100, "exam": 110,
            "price": 55, "doctor": 110, "technician": 110, "receptionist": 90,
            "date": 140, "report_status": 80
        }
        
        for col in columns:
            if col in headers_map:
                self.tree.heading(col, text=headers_map[col],
                                  command=lambda c=col: self.sort_column(c, False))
                self.tree.column(col, width=widths_map[col], anchor=tk.CENTER)
            else:
                # إخفاء الأعمدة الإضافية (uid والملاحظات) من العرض
                self.tree.column(col, width=0)

        self.tree.bind("<Double-1>", lambda e: self.edit_selected_patient())

        rep_bar = ctk.CTkFrame(parent, fg_color="transparent")
        rep_bar.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(rep_bar, text="إرفاق PDF", font=self.font_main,
                      fg_color="#8E44AD", height=38,
                      command=self.attach_report).pack(side="right", padx=5)
        ctk.CTkButton(rep_bar, text="عرض التقرير", font=self.font_main,
                      fg_color=INFO_COLOR, height=38,
                      command=self.view_report).pack(side="right", padx=5)
        ctk.CTkButton(rep_bar, text="حذف المرفق", font=self.font_main,
                      fg_color=DANGER_COLOR, height=38,
                      command=self.delete_report).pack(side="left", padx=5)

    def _row_to_values(self, row, idx):
        return (
            row[0],                    # serial (اللي بنستبدله بالترقيم التراكمي)
            row[1] or "",              # patient_uid (كود المريض)
            row[2],                    # name
            row[3],                    # age
            row[4] or "",              # phone
            row[5],                    # exam
            row[6],                    # price
            row[7] or "",              # doctor
            row[8] or "",              # technician
            row[9] or "",              # receptionist
            row[11] or "",             # exam_date
            "مرفق" if row[12] else "-",# report_status
            row[10] or "",             # notes
        )

    def _populate_tree(self, rows):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(rows):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            display_serial = i + 1  # الترقيم التسلسلي الجديد (1، 2، 3...)
            
            # تجهيز البيانات للعرض
            vals = list(self._row_to_values(row, i))
            vals[0] = display_serial  # نستبدل رقم السجل القديم بالرقم التسلسلي الجديد
            
            # السحر كله هنا: بنخزن الكود الأصلي (row[0]) في الـ iid عشان نستخدمه وقت التعديل أو الحذف
            self.tree.insert("", tk.END, iid=str(row[0]), values=tuple(vals), tags=(tag,))

    def load_patients_data(self):
        if hasattr(self, 'search_var'):
            self.search_var.set("")
        if hasattr(self, 'date_from_var'):
            self.date_from_var.set("")
            self.date_to_var.set("")
        try:
            self._populate_tree(self.db.get_all_patients())
        except Exception as e:
            messagebox.showerror("خطأ", "فشل تحميل البيانات:\n{}".format(e))

    def search_data(self):
        q = self.search_var.get().strip()
        if not q:
            self.load_patients_data()
            return
        try:
            self._populate_tree(self.db.search_patients(q))
        except Exception as e:
            messagebox.showerror("خطأ", "فشل البحث:\n{}".format(e))

    def apply_date_filter(self):
        d_from = self.date_from_var.get().strip()
        d_to = self.date_to_var.get().strip()
        # تحقق مبسط من الصيغة
        for d in (d_from, d_to):
            if d:
                try:
                    datetime.strptime(d, "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("تنبيه", "صيغة التاريخ يجب أن تكون YYYY-MM-DD")
                    return
        try:
            self._populate_tree(self.db.filter_by_date(d_from, d_to))
        except Exception as e:
            messagebox.showerror("خطأ", "فشل الفلترة:\n{}".format(e))

    def sort_column(self, col, reverse):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            items.sort(key=lambda t: float(t[0]), reverse=reverse)
        except (ValueError, TypeError):
            items.sort(reverse=reverse)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)
            self.tree.item(k, tags=('evenrow' if index % 2 == 0 else 'oddrow',))
        self.tree.heading(col, command=lambda c=col: self.sort_column(c, not reverse))

    def edit_selected_patient(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("تنبيه", "من فضلك اختر مريضاً أولاً")
            return
        real_serial = int(sel)
        try:
            row = self.db.query_one("SELECT * FROM patients WHERE serial=?", (real_serial,))
            if not row:
                return
            self.current_edit_serial = row[0]
            self.var_name.set(row[2])
            self.var_age.set(str(row[3]) if row[3] is not None else "")
            self.var_phone.set(row[4] or "")
            self.var_exam.set(row[5] or "")
            self.price_entry.configure(state="normal")
            self.var_price.set(str(row[6]) if row[6] else "")
            self.price_entry.configure(state="disabled")
            self.var_doctor.set(row[7] or "")
            self.var_technician.set(row[8] or "")
            self.var_receptionist.set(row[9] or "")
            self.var_notes.set(row[10] or "")
            self.var_dob_y.set("السنة")
            self.var_dob_m.set("الشهر")
            self.var_dob_d.set("اليوم")
            self.scan_title.configure(text="وضع التعديل — SCAN #{}".format(real_serial),
                                      text_color=WARNING_COLOR)
            self.select_tab("scan")
        except Exception as e:
            messagebox.showerror("خطأ", "فشل فتح السجل:\n{}".format(e))

    def delete_patient(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر مريضاً أولاً")
            return
        real_serial = int(sel)
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا السجل؟"):
            return
        try:
            # هنا كانت المشكلة، كنا بنبعت serial القديم
            report = self.db.delete_patient(real_serial) 
            if report and os.path.exists(report):
                try:
                    os.remove(report)
                except OSError:
                    pass
            messagebox.showinfo("تم", "تم حذف السجل بنجاح")
            self.load_patients_data()
        except Exception as e:
            messagebox.showerror("خطأ", "فشل الحذف:\n{}".format(e))

    def export_csv(self):
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("تنبيه", "لا توجد بيانات للتصدير")
            return
        path = filedialog.asksaveasfilename(
            title="حفظ ملف CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=EXPORTS_DIR,
            initialfile="patients_{}.csv".format(datetime.now().strftime("%Y%m%d"))
        )
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["م", "الاسم", "السن", "الهاتف", "الفحص",
                                 "السعر", "الطبيب", "الفني", "الاستقبال",
                                 "التاريخ", "التقرير", "ملاحظات"])
                for iid in items:
                    v = self.tree.item(iid)['values']
                    # v[1] = uid, v[12] = notes
                    writer.writerow([v[0], v[2], v[3], v[4], v[5], v[6],
                                     v[7], v[8], v[9], v[10], v[11], v[12]])
            messagebox.showinfo("تم", "تم التصدير بنجاح إلى:\n{}".format(path))
            open_file(path)
        except Exception as e:
            messagebox.showerror("خطأ", "فشل التصدير:\n{}".format(e))

    def show_patient_history(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر مريضاً أولاً")
            return
        
        uid = self.tree.set(sel, "patient_uid")
        if not uid:
            messagebox.showinfo("ملاحظة", "هذا المريض ليس لديه كود مسجل، لا يمكن عرض سجله التاريخي.")
            return
            
        try:
            rows = self.db.get_patient_history(uid)
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
            return
        if not rows:
            return

        # إنشاء نافذة السجل التاريخي
        win = ctk.CTkToplevel(self)
        win.title("السجل التاريخي — {}".format(rows[0][2]))
        win.geometry("950x550") # كبرنا النافذة شوية عشان الزراير
        win.configure(fg_color=BG_COLOR)
        win.transient(self)

        ctk.CTkLabel(win, text="السجل التاريخي للمريض: {}".format(rows[0][2]),
                     font=self.font_title, text_color=ACCENT_COLOR).pack(pady=15)

        wrap = ctk.CTkFrame(win, fg_color=CARD_BG, corner_radius=10)
        wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # ضفنا عمود مخفي (report_path) عشان نستخدمه في فتح الملفات
        cols = ("serial", "date", "exam", "price", "doctor", "tech", "report", "report_path")
        tv = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="extended") # selectmode="extended" عشان نقدر نختار أكتر من سطر
        
        headings = ["م", "التاريخ والوقت", "الفحص", "السعر", "الطبيب", "الفني", "التقرير", "المسار"]
        widths = [50, 150, 200, 80, 150, 150, 80, 0]
        
        for c, h, w in zip(cols, headings, widths):
            tv.heading(c, text=h)
            tv.column(c, width=w, anchor=tk.CENTER)
            
        # إخفاء عمود المسار (بس ناخد قيمته في الكود)
        tv.column("report_path", width=0, stretch=tk.NO)

        tv.pack(fill="both", expand=True, padx=10, pady=10)

        for r in rows:
            tv.insert("", tk.END, values=(
                r[0], r[11] or "", r[5] or "", r[6] or 0,
                r[7] or "", r[8] or "", "مرفق" if r[12] else "-", r[12] or ""
            ))

        # شريط الأزرار اللي تحت
        btn_bar = ctk.CTkFrame(win, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 15))

        def open_selected_report():
            selected = tv.selection()
            if not selected:
                messagebox.showwarning("تنبيه", "اختر زيارة أولاً")
                return
            path = tv.item(selected[0], 'values')[7] # بنجيب مسار التقرير من العمود المخفي
            if path and os.path.exists(path):
                open_file(path)
            else:
                messagebox.showinfo("ملاحظة", "هذه الزيارة ليس لها تقرير مرفق.")

        def compare_reports():
            selected = tv.selection()
            if len(selected) != 2:
                messagebox.showwarning("تنبيه", "للمقارنة، يجب أن تختار زيارتين بالضبط.\n(اضغط باستمرار على زر Ctrl في الكيبورد لتحديد أكثر من زيارة)")
                return
            
            path1 = tv.item(selected[0], 'values')[7]
            path2 = tv.item(selected[1], 'values')[7]

            if not (path1 and os.path.exists(path1)) or not (path2 and os.path.exists(path2)):
                messagebox.showwarning("تنبيه", "إحدى الزيارات المحددة أو كلاهما لا تحتوي على تقرير مرفق.")
                return
            
            # فتح الملفين مع بعض عشان الدكتور يقارن
            open_file(path1)
            open_file(path2)

        # الأزرار
        ctk.CTkButton(btn_bar, text="عرض التقرير المحدد", font=self.font_main,
                      fg_color=INFO_COLOR, height=40,
                      command=open_selected_report).pack(side="right", padx=5)
                      
        ctk.CTkButton(btn_bar, text="مقارنة (اختر تقريرين)", font=self.font_main,
                      fg_color="#8E44AD", height=40,
                      command=compare_reports).pack(side="right", padx=5)

        ctk.CTkLabel(btn_bar, text="عدد الزيارات: {}".format(len(rows)),
                     font=self.font_main, text_color=TEXT_MUTED).pack(side="left", padx=10)

    def attach_report(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر مريضاً أولاً")
            return
        real_serial = int(sel)
        name = self.tree.set(sel, "name")
        fpath = filedialog.askopenfilename(title="اختيار PDF",
                                           filetypes=[("PDF", "*.pdf")])
        if not fpath:
            return
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        dest = os.path.join(REPORTS_DIR, "Report_{}_{}_{}.pdf".format(real_serial, safe_name, timestamp))
        try:
            import shutil
            shutil.copy(fpath, dest)
            self.db.update_report_path(real_serial, dest)
            messagebox.showinfo("تم", "تم إرفاق التقرير بنجاح ✓")
            self.load_patients_data()
        except Exception as e:
            messagebox.showerror("خطأ", "فشل الإرفاق:\n{}".format(e))

    def view_report(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر مريضاً أولاً")
            return
        real_serial = int(sel)
        try:
            path = self.db.get_report_path(real_serial)
            if not path:
                messagebox.showinfo("ملاحظة", "لا يوجد تقرير مرفق بهذا السجل")
                return
            if not os.path.exists(path):
                messagebox.showwarning("تنبيه", "ملف التقرير غير موجود على القرص")
                return
            if not open_file(path):
                messagebox.showerror("خطأ", "تعذر فتح الملف")
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def delete_report(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("تنبيه", "اختر مريضاً أولاً")
            return
        real_serial = int(sel)
        path = self.db.get_report_path(real_serial)
        if not path:
            messagebox.showinfo("ملاحظة", "لا يوجد تقرير مرفق")
            return
        if not messagebox.askyesno("تأكيد", "حذف التقرير المرفق؟"):
            return
        try:
            if os.path.exists(path):
                os.remove(path)
            self.db.update_report_path(real_serial, "")
            messagebox.showinfo("تم", "تم حذف التقرير")
            self.load_patients_data()
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    # ================= ADMIN =================
    def build_admin_ui(self, parent):
        # Login box
        self.admin_login_box = ctk.CTkFrame(
            parent, width=400, height=340, fg_color=CARD_BG,
            corner_radius=15, border_width=1, border_color=ACCENT_COLOR
        )
        self.admin_login_box.pack_propagate(False)

        ctk.CTkLabel(self.admin_login_box, text="🔐 ADMIN AUTH",
                     font=self.font_title, text_color=ACCENT_COLOR
                     ).pack(pady=(30, 10))

        self.user_var = ctk.StringVar()
        self.pass_var = ctk.StringVar()

        ctk.CTkEntry(self.admin_login_box, textvariable=self.user_var,
                     placeholder_text="Username", justify="center",
                     width=260, height=40, fg_color="#010A14", 
                     text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED).pack(pady=10)
        pass_entry = ctk.CTkEntry(self.admin_login_box, textvariable=self.pass_var,
                                  placeholder_text="Password", show="*",
                                  justify="center", width=260, height=40,
                                  fg_color="#010A14", text_color=TEXT_MAIN, 
                                  placeholder_text_color=TEXT_MUTED)
        pass_entry.pack(pady=10)
        pass_entry.bind('<Return>', lambda e: self.verify_admin())

        ctk.CTkButton(self.admin_login_box, text="ENTER", font=self.font_main,
                      fg_color=ACCENT_COLOR, text_color="#000",
                      width=260, height=40,
                      command=self.verify_admin).pack(pady=15)

        # Dashboard
        self.admin_dash_box = ctk.CTkFrame(parent, fg_color="transparent")

        self.admin_tabs = ctk.CTkTabview(
            self.admin_dash_box, fg_color=CARD_BG,
            segmented_button_selected_color=ACCENT_COLOR,
            text_color=TEXT_MAIN
        )
        self.admin_tabs.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_analysis = self.admin_tabs.add("التحليلات والطباعة")
        self.tab_ex = self.admin_tabs.add("الفحوصات")
        self.tab_dc = self.admin_tabs.add("الأطباء")
        self.tab_tc = self.admin_tabs.add("الفنيين")
        self.tab_rc = self.admin_tabs.add("الاستقبال")
        self.tab_settings = self.admin_tabs.add("الإعدادات")

        self.analysis_container = ctk.CTkFrame(self.tab_analysis, fg_color="transparent")
        self.analysis_container.pack(fill="both", expand=True)

        self.setup_admin_lists()
        self.setup_admin_settings()

    def verify_admin(self):
        if self.db.verify_admin(self.user_var.get(), self.pass_var.get()):
            self.is_admin_logged_in = True
            self.user_var.set("")
            self.pass_var.set("")
            self.show_admin_dashboard()
            self.refresh_analysis_tab()
        else:
            messagebox.showerror("مرفوض", "بيانات الدخول غير صحيحة")

    def show_admin_login(self):
        self.admin_dash_box.pack_forget()
        self.admin_login_box.place(relx=0.5, rely=0.5, anchor="center")

    def show_admin_dashboard(self):
        self.admin_login_box.place_forget()
        self.admin_dash_box.pack(fill="both", expand=True)

    # ================= ADMIN: ANALYSIS =================
    def refresh_analysis_tab(self):
        for w in self.analysis_container.winfo_children():
            w.destroy()

        btn_row = ctk.CTkFrame(self.analysis_container, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(5, 5))
        ctk.CTkButton(btn_row, text="تصدير PDF 🖨️", font=self.font_main,
                      fg_color=WARNING_COLOR, text_color="#000",
                      hover_color="#D68910", height=38,
                      command=self.print_analysis).pack(side="left")

        try:
            current_month = datetime.now().strftime("%Y-%m")
            m_data = self.db.get_monthly_stats(current_month) or (0, 0)
            t_data = self.db.get_total_stats() or (0, 0)
            trends = self.db.get_monthly_trends()
            exams_dist = self.db.get_exam_distribution()
            tech_dist = self.db.get_technician_distribution()
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
            return

        cards = ctk.CTkFrame(self.analysis_container, fg_color="transparent")
        cards.pack(fill="x", pady=5)

        def stat_card(title, cases, rev, color):
            card = ctk.CTkFrame(cards, fg_color="#010A14",
                                corner_radius=10, border_width=1, border_color=color)
            card.pack(side="right", fill="both", expand=True, padx=10)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont("Arial", 16, "bold"),
                         text_color=color).pack(pady=(12, 5))
            ctk.CTkLabel(card,
                         text="الحالات: {}  |  الإيرادات: {} ج.م".format(cases, format_currency(rev)),
                         font=self.font_main, text_color=TEXT_MAIN).pack(pady=(0, 12))

        stat_card("أداء الشهر الحالي", m_data[0], m_data[1], ACCENT_COLOR)
        stat_card("الإحصائيات التراكمية", t_data[0], t_data[1], SUCCESS_COLOR)

        if not trends:
            return

        titles = ctk.CTkFrame(self.analysis_container, fg_color="transparent")
        titles.pack(fill="x", padx=15, pady=(10, 0))
        for i, (txt, col) in enumerate([
            ("الحالات شهرياً", ACCENT_COLOR),
            ("توزيع الفحوصات", ACCENT_COLOR),
            ("إنتاجية الفنيين", SUCCESS_COLOR),
        ]):
            titles.columnconfigure(i, weight=1)
            ctk.CTkLabel(titles, text=txt,
                         font=ctk.CTkFont("Arial", 18, "bold"),
                         text_color=col).grid(row=0, column=i, sticky="ew")

        plt.close('all')
        plt.style.use('dark_background')
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 3.5))
        fig.patch.set_facecolor(CARD_BG)
        for ax in (ax1, ax2, ax3):
            ax.set_facecolor(CARD_BG)

        # Trends
        x_t = range(len(trends))
        ax1.bar(x_t, [r[1] for r in trends], color=ACCENT_COLOR, width=0.5)
        ax1.set_xticks(x_t)
        ax1.set_xticklabels([arabic_text(r[0]) for r in trends],
                            fontfamily='Arial', fontsize=10)
        ax1.tick_params(axis='y', colors=TEXT_MUTED)
        ax1.tick_params(axis='x', colors=TEXT_MUTED)

        # Pie
        if exams_dist:
            ax2.pie([r[1] for r in exams_dist],
                    labels=[arabic_text(r[0]) for r in exams_dist],
                    autopct='%1.1f%%',
                    textprops={'color': TEXT_MAIN, 'fontfamily': 'Arial'},
                    colors=['#00E5FF', '#00C896', '#F39C12', '#E74C3C', '#8E44AD'])

        # Tech
        if tech_dist:
            x_te = range(len(tech_dist))
            ax3.bar(x_te, [r[1] for r in tech_dist], color=SUCCESS_COLOR, width=0.5)
            ax3.set_xticks(x_te)

            def wrap(t):
                t = str(t)
                if ' ' in t:
                    p = t.split(' ', 1)
                    return arabic_text("{}\n{}".format(p[0], p[1]))
                return arabic_text(t)

            ax3.set_xticklabels([wrap(r[0]) for r in tech_dist],
                                fontfamily='Arial', fontsize=9, ha='center')
            ax3.tick_params(axis='y', colors=TEXT_MUTED)
            ax3.tick_params(axis='x', colors=TEXT_MUTED)

        plt.tight_layout(pad=2)
        self.current_fig = fig

        canvas = FigureCanvasTkAgg(fig, master=self.analysis_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def print_analysis(self):
        if not hasattr(self, 'current_fig'):
            return
        try:
            report_name = "Analysis_Report_{}.pdf".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
            filepath = os.path.join(REPORTS_DIR, report_name)
            self.current_fig.savefig(filepath, format='pdf',
                                     bbox_inches='tight', facecolor=CARD_BG)
            messagebox.showinfo("نجاح", "تم حفظ التقرير في:\n{}".format(filepath))
            open_file(filepath)
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    # ================= ADMIN: SETTINGS =================
        # ================= ADMIN: SETTINGS =================
    def setup_admin_lists(self):
        # ================= Exams =================
        v_ex, v_pr = ctk.StringVar(), ctk.StringVar()
        v_pr.trace_add("write", lambda *a: self._force_number(v_pr))
        f1 = ctk.CTkFrame(self.tab_ex, fg_color="transparent")
        f1.pack(pady=10)
        ctk.CTkEntry(f1, textvariable=v_ex, placeholder_text="اسم الفحص",
                     width=200, height=35, justify="center",
                     fg_color="#010A14", text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED).pack(side="right", padx=5)
        ctk.CTkEntry(f1, textvariable=v_pr, placeholder_text="السعر",
                     width=100, height=35, justify="center",
                     fg_color="#010A14", text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED).pack(side="right", padx=5)

        lb_ex = tk.Listbox(self.tab_ex, font=("Arial", 13), justify="center",
                           bg="#010A14", fg=TEXT_MAIN, selectbackground=ACCENT_COLOR)
        lb_ex.pack(fill="both", expand=True, padx=60, pady=10)

        def refresh_ex():
            lb_ex.delete(0, tk.END)
            for k, v in self.exams_dict.items():
                lb_ex.insert(tk.END, "{} - {} ج.م".format(k, v))

        def add_ex():
            name = v_ex.get().strip()
            if not name or not v_pr.get().strip():
                messagebox.showwarning("تنبيه", "أدخل الاسم والسعر")
                return
            try:
                self.db.add_exam(name, float(v_pr.get()))
                self.reload_catalogs()
                self.exam_menu.configure(values=list(self.exams_dict.keys()) or [""])
                v_ex.set("")
                v_pr.set("")
                refresh_ex()
            except Exception as e:
                messagebox.showerror("خطأ", "قد يكون الاسم مكرراً:\n{}".format(e))

        def del_ex():
            sel = lb_ex.curselection()
            if not sel:
                return
            name = lb_ex.get(sel[0]).split(" - ")[0].strip()
            try:
                self.db.delete_exam(name)
                self.reload_catalogs()
                self.exam_menu.configure(values=list(self.exams_dict.keys()) or [""])
                refresh_ex()
            except Exception as e:
                messagebox.showerror("خطأ", str(e))

        ctk.CTkButton(f1, text="إضافة", fg_color=SUCCESS_COLOR, text_color="#000",
                      height=35, command=add_ex).pack(side="right", padx=5)
        ctk.CTkButton(self.tab_ex, text="حذف", fg_color=DANGER_COLOR,
                      height=35, command=del_ex).pack(pady=5)
        refresh_ex()

        # ================= Doctors & Technicians & Receptionists =================
        self._build_catalog_tab(self.tab_dc, "doctors", self.doctor_combo, "اسم الطبيب")
        self._build_catalog_tab(self.tab_tc, "technicians", self.tech_combo, "اسم الفني")
        self._build_catalog_tab(self.tab_rc, "receptionists", self.reception_combo, "اسم موظف الاستقبال")

    def _build_catalog_tab(self, tab, table, combo, placeholder):
        # السطرين دول بيمسحوا أي عناصر قديمة عشان لو الكود اتكرر بالغلط
        for widget in tab.winfo_children():
            widget.destroy()

        v_name = ctk.StringVar()
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(pady=10)
        
        ctk.CTkEntry(top, textvariable=v_name, placeholder_text=placeholder,
                     width=250, height=35, justify="center",
                     fg_color="#010A14", text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED).pack(side="right", padx=5)

        lb = tk.Listbox(tab, font=("Arial", 13), justify="center",
                        bg="#010A14", fg=TEXT_MAIN, selectbackground=ACCENT_COLOR)
        lb.pack(fill="both", expand=True, padx=60, pady=10)

        def get_list():
            if table == "doctors": return self.doctors_list
            elif table == "technicians": return self.technicians_list
            else: return self.receptionists_list

        def refresh():
            lb.delete(0, tk.END)
            for n in get_list():
                if n: lb.insert(tk.END, n)

        def add():
            name = v_name.get().strip()
            if not name: return
            try:
                if table == "doctors": self.db.add_doctor(name)
                elif table == "technicians": self.db.add_technician(name)
                else: self.db.add_receptionist(name)
                
                self.reload_catalogs()
                combo.configure(values=get_list() or [""])
                v_name.set("")
                refresh()
            except Exception as e:
                messagebox.showerror("خطأ", "قد يكون مكرراً:\n{}".format(e))

        def delete():
            sel = lb.curselection()
            if not sel: return
            name = lb.get(sel[0])
            try:
                if table == "doctors": self.db.delete_doctor(name)
                elif table == "technicians": self.db.delete_technician(name)
                else: self.db.delete_receptionist(name)
                
                self.reload_catalogs()
                combo.configure(values=get_list() or [""])
                refresh()
            except Exception as e:
                messagebox.showerror("خطأ", str(e))

        ctk.CTkButton(top, text="إضافة", fg_color=ACCENT_COLOR, text_color="#000",
                      height=35, command=add).pack(side="right", padx=5)
        ctk.CTkButton(tab, text="حذف", fg_color=DANGER_COLOR,
                      height=35, command=delete).pack(pady=5)
        refresh()

    def _force_number(self, var):
        v = var.get()
        clean = ''.join(c for c in v if c.isdigit() or c == '.')
        if clean.count('.') > 1:
            parts = clean.split('.')
            clean = parts[0] + '.' + ''.join(parts[1:])
        if v != clean:
            var.set(clean)

    def setup_admin_settings(self):
        f = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=40, pady=20)

        # Backup
        ctk.CTkLabel(f, text="💾 النسخ الاحتياطي",
                     font=ctk.CTkFont("Arial", 18, "bold"),
                     text_color=ACCENT_COLOR).pack(anchor="e", pady=(10, 5))

        last = self.db.get_setting('last_backup', 'لا يوجد')
        ctk.CTkLabel(f, text="آخر نسخة: {}".format(last[:19] if last != 'لا يوجد' else last),
                     font=self.font_small, text_color=TEXT_MUTED
                     ).pack(anchor="e", pady=(0, 8))

        def do_backup():
            path = self.db.backup()
            if path:
                messagebox.showinfo("تم", "تم إنشاء نسخة احتياطية:\n{}".format(path))
                self.setup_admin_settings()
            else:
                messagebox.showerror("خطأ", "فشل إنشاء النسخة")

        ctk.CTkButton(f, text="نسخة احتياطية الآن", font=self.font_main,
                      fg_color=SUCCESS_COLOR, text_color="#000", height=40,
                      command=do_backup).pack(anchor="e", pady=5, fill="x")

        # Change Password
        ctk.CTkLabel(f, text="🔒 تغيير كلمة المرور",
                     font=ctk.CTkFont("Arial", 18, "bold"),
                     text_color=WARNING_COLOR).pack(anchor="e", pady=(20, 5))

        old_var = ctk.StringVar()
        new_var = ctk.StringVar()
        ctk.CTkEntry(f, textvariable=old_var, placeholder_text="كلمة المرور الحالية",
                     show="*", height=38, justify="center", 
                     text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED).pack(fill="x", pady=3)
        ctk.CTkEntry(f, textvariable=new_var, placeholder_text="كلمة المرور الجديدة",
                     show="*", height=38, justify="center", 
                     text_color=TEXT_MAIN, placeholder_text_color=TEXT_MUTED).pack(fill="x", pady=3)

        def change_pw():
            if not self.db.verify_admin(self.db.get_setting('admin_user', 'admin'),
                                        old_var.get()):
                messagebox.showerror("خطأ", "كلمة المرور الحالية غير صحيحة")
                return
            if len(new_var.get()) < 4:
                messagebox.showwarning("تنبيه", "كلمة المرور قصيرة جداً")
                return
            self.db.change_admin_password(new_var.get())
            old_var.set("")
            new_var.set("")
            messagebox.showinfo("تم", "تم تغيير كلمة المرور بنجاح")

        ctk.CTkButton(f, text="تغيير", font=self.font_main,
                      fg_color=WARNING_COLOR, text_color="#000", height=38,
                      command=change_pw).pack(anchor="e", pady=5, fill="x")

        # Info
        ctk.CTkLabel(f, text="ℹ️ الإصدار: {}".format(APP_VERSION),
                     font=self.font_small, text_color=TEXT_MUTED
                     ).pack(anchor="e", pady=(30, 0))