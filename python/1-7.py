import socket
import threading
import os
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
import win32print
import win32api
import tempfile

save_file = "received_hl7.txt"

# إعدادات الثيم
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")

# واجهة البرنامج
root = ctk.CTk()
root.title("HL7 Receiver")
root.geometry("700x500")

# صندوق النص لعرض الرسائل
textbox = ctk.CTkTextbox(root, wrap="word")
textbox.pack(fill="both", expand=True, padx=20, pady=(20, 10))

# أزرار التحكم
button_frame = ctk.CTkFrame(root)
button_frame.pack(fill="x", padx=20, pady=(0, 15))

def open_file():
    if os.path.exists(save_file):
        os.startfile(save_file)
    else:
        messagebox.showerror("Error", "File not found.")

def print_file():
    if os.path.exists(save_file):
        try:
            # قراءة محتوى الملف
            with open(save_file, "r", encoding="utf-8") as f:
                content = f.read()

            # حفظ المحتوى مؤقتًا في ملف نصي
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding="utf-8") as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            # عرض نافذة اختيار الطابعة
            printer_name = win32print.GetDefaultPrinter()
            printer_handle = win32print.OpenPrinter(printer_name)
            try:
                # هنا يمكن إضافة كود متقدم للطباعة حسب الطابعة إذا أردت
                pass
            finally:
                win32print.ClosePrinter(printer_handle)

            # استدعاء أمر الطباعة مع نافذة الطباعة (ShellExecute مع "printto")
            # يمكنك تعديل الطابعة يدويًا بعد ظهور النافذة
            win32api.ShellExecute(
                0,
                "printto",  # "printto" تعرض نافذة اختيار الطابعة (على بعض الأنظمة)
                temp_file_path,
                None,
                ".",
                1
            )
        except Exception as e:
            messagebox.showerror("Print Error", f"Cannot print file.\n{e}")
    else:
        messagebox.showerror("Error", "File not found.")

ctk.CTkButton(button_frame, text="Open Saved File", command=open_file).pack(side="left", padx=10)
ctk.CTkButton(button_frame, text="Print Message", command=print_file).pack(side="left", padx=10)

# استقبال الرسائل
def start_hl7_receiver(ip="0.0.0.0", port=8080):  # هنا استمع على كل العناوين
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(5)
    textbox.insert("end", f"Listening on {ip}:{port}...\n")

    while True:
        client_socket, addr = server.accept()
        data = client_socket.recv(4096).decode("utf-8")

        if data:
            # عرض في الواجهة
            msg = f"\n[{datetime.now()}] From {addr[0]}:\n{data}\n"
            textbox.insert("end", msg)
            textbox.see("end")

            # حفظ في ملف
            with open(save_file, "a", encoding="utf-8") as f:
                f.write(f"===== {datetime.now()} from {addr[0]} =====\n")
                f.write(data + "\n\n")

        client_socket.close()

# تشغيل استقبال الرسائل في خيط منفصل
receiver_thread = threading.Thread(target=start_hl7_receiver, args=("0.0.0.0", 8080), daemon=True)
receiver_thread.start()



root.mainloop()