import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import pydicom
import os
import numpy as np
from datetime import datetime
from datetime import datetime, timedelta
from pydicom.errors import InvalidDicomError
import re
from rapidfuzz import fuzz  
import socket
import pytesseract
import os
from tkinter import filedialog, messagebox
import pandas as pd
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")
CSV_FILE = "rad.csv"
HL7_DIR = "hl7_messages"
os.makedirs(HL7_DIR, exist_ok=True)
all_data = []
selected_cases = []
check_vars = []
COMMON_VARIANTS = {
    "sara": "sarah",
    "mena": "mina",
    "meena": "mina",
    "shawkia": "shawkya",
    "usama": "osama",
    "latif": "lateef",
    "allateef": "lateef",
    "awaad": "awad"
}
# def convert_to_hl7(data):


def send_hl7_message(ip, port, message):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        sock.sendall(message.encode('utf-8'))
        sock.close()
        messagebox.showinfo("Success", f"HL7 message sent to {ip}:{port}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send HL7 message.\n{e}")

def convert_to_hl7_from_table(data):
    accumulated_dose = data.get("AccumulatedDose", 0)
    dose_per_year = data.get("DosePerYear", 0)
    return f"""MSH|^~\\&|RadiologySystem|Hospital|PACS|Hospital|{datetime.now().strftime('%Y%m%d%H%M%S')}||ORM^O01|{data.get("PatientID", "")}|P|2.3
PID|||{data.get("PatientID", "")}||{data.get("Name", "")}|||{data.get("DOB", "")}|{data.get("Sex", "")}
OBR|||{data.get("PatientID", "")}||{data.get("Modality", "")}|||||{data.get("Date").strftime('%Y%m%d')}
OBX|1|NM|CTDIvol||{data.get("CTDIvol", 0):.5f}|mGy
OBX|2|NM|DLP||{data.get("DLP", 0):.5f}|mGy*cm
OBX|3|NM|Dose_mSv||{data.get("mSv", 0):.5f}|mSv
OBX|4|NM|AccumulatedDose||{accumulated_dose:.5f}|mSv
OBX|5|NM|DosePerYear||{dose_per_year:.5f}|mSv
"""

def send_hl7_message(ip, port, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))  # يتصل بالسيرفر
            s.sendall(message.encode('utf-8'))  # يبعت الرسالة
            messagebox.showinfo("Success", f"Message sent to {ip}:{port}")
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to send message.\n\n{e}")

def show_hl7_for_selected():
    selected = [data for var, data in check_vars if var.get()]

    if len(selected) != 1:
        messagebox.showerror("Error", "Please select exactly one case to view HL7 message.")
        return

    # التحقق من كلمة السر
    password = simpledialog.askstring("Password", "Enter password to view HL7 message:", show='*')
    if password != "admin123":
        messagebox.showerror("Unauthorized", "Incorrect password.")
        return

    data = selected[0]
    hl7_message = convert_to_hl7_from_table(data)

    # نافذة HL7
    hl7_window = ctk.CTkToplevel()
    hl7_window.title("HL7 Message")
    hl7_window.geometry("700x450")
    hl7_window.attributes("-topmost", True)

    textbox = ctk.CTkTextbox(hl7_window, wrap="word")
    textbox.insert("1.0", hl7_message)
    textbox.configure(state="disabled")
    textbox.pack(fill="both", expand=True, padx=10, pady=(10, 5))

    # إدخال IP و Port
    ip_var = ctk.StringVar()
    port_var = ctk.StringVar()

    frame_send = ctk.CTkFrame(hl7_window)
    frame_send.pack(fill="x", padx=10, pady=5)

    ctk.CTkLabel(frame_send, text="IP Address:").pack(side="left")
    ip_entry = ctk.CTkEntry(frame_send, textvariable=ip_var, width=150)
    ip_entry.pack(side="left", padx=5)

    ctk.CTkLabel(frame_send, text="Port:").pack(side="left")
    port_entry = ctk.CTkEntry(frame_send, textvariable=port_var, width=80)
    port_entry.pack(side="left", padx=5)

    def on_send():
        ip = ip_var.get().strip()
        port_text = port_var.get().strip()

        if not ip or not port_text:
            messagebox.showerror("Input Error", "Please enter both IP address and port.")
            return
        try:
            port = int(port_text)
        except:
            messagebox.showerror("Input Error", "Port must be a number.")
            return
        
        send_hl7_message(ip, port, hl7_message)

    send_btn = ctk.CTkButton(frame_send, text="Send HL7 Message", command=on_send)
    send_btn.pack(side="left", padx=10)

def normalize_name(name):
    name = re.sub(r"[^a-zA-Z ]", " ", name)
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name

def is_same_person(name1, name2, threshold=85):
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    # تطابق شامل سريع
    if fuzz.token_set_ratio(n1, n2) >= threshold:
        return True

    # مقارنة كل مقطع اسمي على حدة (ذكية)
    n1_parts = n1.split()
    n2_parts = n2.split()

    shorter, longer = (n1_parts, n2_parts) if len(n1_parts) <= len(n2_parts) else (n2_parts, n1_parts)

    matches = 0
    for part in shorter:
        # نحاول نلاقي أي تطابق مقبول في الاسم الأطول
        if any(fuzz.partial_ratio(part, lp) >= threshold for lp in longer):
            matches += 1

    # نعتبرهم متشابهين لو تطابق كافي
    return matches >= len(shorter) - 1  # يسمح باختلاف بسيط




import os
from datetime import datetime
from tkinter import filedialog, messagebox, BooleanVar, Label


# متغيرات عامة
all_data = []
check_vars = []
selected_cases = []
content_frame = None  # لازم تربطه بالإطار اللي هتعرض فيه البيانات
name_filter_var = None  # لازم تربطه بـ Entry أو غيره
sort_var = None  # لو هتستخدم فلترة/ترتيب

# 1. دالة التحقق من امتداد إكسيل

def convert_to_hl7_from_table(data):
    return f"""MSH|^~\\&|VitalSignsSystem|Hospital|Lab|Hospital|{datetime.now().strftime('%Y%m%d%H%M%S')}||ORU^R01|{data.get("Name", "")}|P|2.3
PID|||{data.get("Name", "")}||{data.get("Name", "")}|||
OBX|1|TX|Blood Pressure||{data.get("Blood Pressure", "")}
OBX|2|TX|SpO2||{data.get("SpO2", "")}
OBX|3|TX|Pulse||{data.get("Pulse", "")}
OBX|4|TX|RR||{data.get("RR", "")}

OBX|5|TX|Temperature||{data.get("Temperature", "")}
OBX|6|TX|Weight||{data.get("Weight", "")}
OBX|7|TX|Length||{data.get("Length", "")}
OBX|8|TX|Disease||{data.get("Disease", "")}
"""

def is_excel(file_path):
    return file_path.lower().endswith(('.xls', '.xlsx'))

# 2. دالة قراءة ملفات Excel من فولدر
def read_excel_folder():
    global all_data
    folder = filedialog.askdirectory()
    if not folder:
        return
    excel_files = []
    for root_dir, dirs, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root_dir, file)
            if not os.path.isfile(file_path):
                continue

            if is_excel(file_path):
                try:
                    df = pd.read_excel(file_path)
                    excel_files.append(file_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Error reading Excel file {file_path}:\n{e}")


    if not excel_files:
        messagebox.showinfo("No Excel Files", "No valid Excel files found in the selected folder.")
        return

    process_excel_files(excel_files)

# 3. دالة معالجة ملفات Excel (استخراج البيانات المطلوبة)
def process_excel_files(files):
    global all_data
    all_data.clear()

    for path in files:
        try:
            df = pd.read_excel(path)

            required_cols = ['Name', 'Blood Pressure', 'SpO2','Pulse','RR', 'Temperature', 'Weight', 'Length', 'Disease']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")

            for idx, row in df.iterrows():
                case = {
                    "Name": row['Name'],
                    "Blood Pressure": row['Blood Pressure'],
                    "SpO2": row['SpO2'],
                    "Pulse": row['Pulse'],
                    "RR": row['RR'],
                    "Temperature": row['Temperature'],
                    "Weight": row['Weight'],
                    "Length": row['Length'],
                    "Disease": row['Disease'],
                }
                all_data.append(case)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process Excel file {path}.\nError: {e}")
            return

    display_text_data()

# 4. دالة عرض البيانات في جدول باستخدام customtkinter

def open_add_patient_window():
    add_window = ctk.CTkToplevel()
    add_window.title("Add New Patient")
    add_window.geometry("400x800")
    add_window.lift()
    add_window.attributes("-topmost", True)
    add_window.after(100, lambda: add_window.attributes("-topmost", False))

    entries = {}

    fields = [
        ("Name", "Name"),
        ("Blood Pressure", "Blood Pressure"),
        ("SpO2", "SpO2"),
        ("Pulse", "Pulse"),
        ("RR", "RR"),
        ("Temperature", "Temperature"),
        ("Weight", "Weight"),
        ("Length", "Length"),
        ("Disease", "Disease"),
    ]

    for idx, (key, label_text) in enumerate(fields):
        lbl = ctk.CTkLabel(add_window, text=label_text, anchor="w", font=("Arial", 14))
        lbl.pack(pady=(10 if idx == 0 else 5, 0), padx=20, anchor="w")

        entry = ctk.CTkEntry(add_window, width=300)
        entry.pack(pady=5, padx=20)
        entries[key] = entry

    def save_patient():
        patient_data = {}
        for key, entry in entries.items():
            value = entry.get().strip()
            if not value:
                messagebox.showwarning("تحذير", f"برجاء إدخال {key}")
                return
            patient_data[key] = value

        all_data.append(patient_data)
        add_window.destroy()
        display_text_data()

    save_btn = ctk.CTkButton(add_window, text="💾 Save", command=save_patient, fg_color="#4caf50", hover_color="#388e3c")
    save_btn.pack(pady=20)




def display_text_data():
    global check_vars
    for widget in content_frame.winfo_children():
        widget.destroy()

    filtered = []
    name_filter = name_filter_var.get().strip().lower() if name_filter_var else ""

    for data in all_data:
        if name_filter in data["Name"].lower():
            filtered.append(data)

    headers = ["Select", "Name", "Blood Pressure", "SpO2","Pulse","RR", "Temperature", "Weight", "Length", "Disease"]
    col_indices = {h.lower().replace(" ", "_"): i for i, h in enumerate(headers)}

    scroll_frame = ctk.CTkScrollableFrame(content_frame, corner_radius=10, fg_color="#ffffff")
    scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

    for col, header in enumerate(headers):
        lbl = ctk.CTkLabel(scroll_frame, text=header, font=ctk.CTkFont(size=14, weight="bold"), anchor="center")
        lbl.grid(row=0, column=col, padx=5, pady=10, sticky="nsew")

    check_vars.clear()

    for row, data in enumerate(filtered, start=1):
        var = BooleanVar(value=data in selected_cases)
        check_vars.append((var, data))
        chk = ctk.CTkCheckBox(scroll_frame, variable=var)
        chk.grid(row=row, column=col_indices["select"], padx=5, pady=5, sticky="nsew")

        def add_label(r, c, text):
            lbl = ctk.CTkLabel(scroll_frame, text=text, anchor="center")
            lbl.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

        add_label(row, col_indices["name"], str(data.get("Name", "")))
        add_label(row, col_indices["blood_pressure"], str(data.get("Blood Pressure", "")))
        add_label(row, col_indices["spo2"], str(data.get("SpO2", "")))
        add_label(row, col_indices["pulse"], str(data.get("Pulse", "")))
        add_label(row, col_indices["rr"], str(data.get("RR", "")))
        add_label(row, col_indices["temperature"], str(data.get("Temperature", "")))
        add_label(row, col_indices["weight"], str(data.get("Weight", "")))
        add_label(row, col_indices["length"], str(data.get("Length", "")))
        add_label(row, col_indices["disease"], str(data.get("Disease", "")))

    for col in range(len(headers)):
        scroll_frame.grid_columnconfigure(col, weight=1)
    scroll_frame.grid_columnconfigure(col_indices["select"], weight=0, minsize=40)





def update_selected_cases():
    selected_cases.clear()
    for var, data in check_vars:
        if var.get():
            selected_cases.append(data)

def show_hl7_message():
    update_selected_cases()
    if len(selected_cases) != 1:
        messagebox.showwarning("Selection Error", "Please select exactly ONE case to view its HL7 message.")
        return

    password = simpledialog.askstring("Password", "Enter password to view HL7 message:", show='*')
    if password != "admin123":
        messagebox.showerror("Unauthorized", "Incorrect password.")
        return

    data = selected_cases[0]  # لأن في حالة واحدة فقط
    hl7_filename = f"{HL7_DIR}/{data['Name']}_{data['Date'].strftime('%Y%m%d')}_{data['PatientID']}.hl7"
    if os.path.exists(hl7_filename):
        with open(hl7_filename, "r") as f:
            hl7 = f.read()
        messagebox.showinfo("HL7 Message", hl7)
    else:
        messagebox.showerror("Not Found", "HL7 message not found.")


def delete_selected():
    update_selected_cases()
    if not selected_cases:
        messagebox.showwarning("No Selection", "Please select cases to delete.")
        return

    # طلب كلمة المرور الأولى
    password = simpledialog.askstring("Password", "Enter password to delete selected cases:", show='*')
    if password != "admin123":
        messagebox.showerror("Unauthorized", "Incorrect password.")
        return

    # طلب التأكيد بكتابة كلمة المرور مجددًا
    confirm_pass = simpledialog.askstring("Confirm Delete", "To confirm deletion, please type password again:", show='*', parent=root)
    if confirm_pass != "admin123":
        messagebox.showerror("Unauthorized", "Password confirmation failed.", parent=root)
        return  # <== فقط لو غلط

    # رسالة تأكيد نهائية
    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_cases)} selected case(s)? This action cannot be undone.")
    if not confirm:
        return

    # تنفيذ الحذف
    for sel in selected_cases:
        if sel in all_data:
            all_data.remove(sel)

    selected_cases.clear()
    display_text_data()


def resize_bg(event):
    global bg_img_resized, bg_label
    new_width = event.width
    new_height = event.height
    resized = bg_img_orig.resize((new_width, new_height), Image.ANTIALIAS)
    bg_img_resized = ImageTk.PhotoImage(resized)
    bg_label.configure(image=bg_img_resized)

# واجهة المستخدم
root = ctk.CTk()
root.title(" Vital Signs App ")
root.geometry("1300x900")
root.configure(bg="white")  # خلفية بيضاء


bg_img_orig = Image.open("g.jpg")
bg_img_resized = ImageTk.PhotoImage(bg_img_orig)
bg_label = ctk.CTkLabel(root, image=bg_img_resized, text="")
bg_label.place(x=0, y=0, relwidth=1, relheight=1)
root.bind("<Configure>", resize_bg)


# ألوان موحدة للأزرار – Flat modern look
BUTTON_COLOR = "#3b89d3"        # أزرق هادئ
BUTTON_HOVER = "#071A50"        # أزرق داكن
DELETE_COLOR = "#dc2626"        # أحمر خفيف
DELETE_HOVER = "#991b1b"        # أحمر داكن
SHOW_COLOR = "#3BB2C7"
SHOW_HOVER = "#16575F"
SELECT_COLOR = "#589cfc"
SELECT_HOVER = "#475569"
# لازم تعرّف دالة وسيطة أو تستخدم lambda عشان تمرر الملفات
excel_files = []  # لازم تكون معرفة ومعبّاه قبل هنا
# زر فتح ملف Excel (ممكن تستعمل دالة load_excel_file بدل process_excel_files مباشرة)


# زر فتح مجلد Excel (تأكد ان read_excel_folder بدون أقواس هنا)
btn_excel_folder = ctk.CTkButton(root, text="📁 Excel Folder",
    command=read_excel_folder,
    width=140, height=40,
    fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
    corner_radius=10, font=("Arial", 16, "bold"))
btn_excel_folder.place(relx=0.01, rely=0.28)
ctk.CTkButton(root, text="💬 HL7 Message", command=show_hl7_for_selected,
              width=140, height=40, fg_color=SHOW_COLOR, hover_color=SHOW_HOVER,
              corner_radius=10, font=("Arial", 16, "bold")).place(relx=0.01, rely=0.34)




ctk.CTkButton(root, text="❌ Delete Cases", command=delete_selected,
              width=140, height=40, fg_color=DELETE_COLOR, hover_color=DELETE_HOVER,
              corner_radius=10, font=("Arial", 16, "bold")).place(relx=0.01, rely=0.40)



add_patient_btn = ctk.CTkButton(root, text="➕Add Patient", command=open_add_patient_window,
    width=140, height=40, fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
    corner_radius=10, font=("Arial", 16, "bold"))
add_patient_btn.place(relx=0.01, rely=0.46)



# إطار لصف الفلاتر الثلاثة (في منتصف الواجهة)
filters_frame = ctk.CTkFrame(root, fg_color="white")
filters_frame.place(relx=0.5, rely=0.08, anchor="n")  # في منتصف العرض

# فلتر الاسم
name_filter_var = ctk.StringVar()
ctk.CTkLabel(filters_frame, text="Filter By Patient Name:", text_color="black").pack(side="left", padx=(0, 5))
ctk.CTkEntry(filters_frame, placeholder_text="Filter by Name", textvariable=name_filter_var, width=140).pack(side="left", padx=(0, 20))
name_filter_var.trace_add("write", lambda *args: display_text_data())


# محتوى البيانات
# shadow frame (أسود فاتح كخلفية خفيفة)
shadow_frame = ctk.CTkFrame(root, fg_color="#416dcc", corner_radius=12)
shadow_frame.place(relx=0.14, rely=0.15, relwidth=0.80, relheight=0.70)
# frame الأساسي فوق الـ shadow
content_frame = ctk.CTkFrame(root, fg_color="#ffffff", corner_radius=10)
content_frame.place(relx=0.15, rely=0.16, relwidth=0.78, relheight=0.68)
# رسالة ترحيبية
welcome_label = ctk.CTkLabel(content_frame, text="Click here to select DICOM files",
text_color="blue", font=ctk.CTkFont(size=20, weight="bold"), cursor="hand2")
welcome_label.pack(expand=True)
root.mainloop()

