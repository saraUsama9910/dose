# import cv2 as cv
# import numpy as np
# import matplotlib
# matplotlib.use('Agg')  # استخدمي backend لا يعتمد على Tkinter
# import matplotlib.pyplot as plt

# img = cv.imread(r"C:\Users\maryam\Downloads\reem.png")
# gray_image = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

# fig, ax = plt.subplots(1, 2, figsize=(16, 8))
# fig.tight_layout()

# ax[0].imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
# ax[0].set_title("Original")

# ax[1].imshow(cv.cvtColor(gray_image, cv.COLOR_BGR2RGB))
# ax[1].set_title("Grayscale")
# plt.savefig("output.png")  # احفظ الرسم في ملف




import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2 as cv
import os

def open_single_image():
    file_path = filedialog.askopenfilename(
        title="اختار صورة", 
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
    )
    if file_path:
        show_image(file_path)

def open_multiple_images():
    file_paths = filedialog.askopenfilenames(
        title="اختار صور متعددة", 
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
    )
    for path in file_paths:
        show_image(path)

def show_image(path):
    img = cv.imread(path)
    if img is None:
        messagebox.showerror("خطأ", f"فشل في فتح الصورة: {os.path.basename(path)}")
        return
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(img_pil)

    # إنشاء نافذة جديدة لكل صورة
    win = tk.Toplevel(root)
    win.title(os.path.basename(path))
    lbl = tk.Label(win, image=img_tk)
    lbl.image = img_tk  # مهم جدًا عشان الصورة ماتختفيش
    lbl.pack()

# إنشاء الواجهة الرئيسية
root = tk.Tk()
root.title("عارض الصور")

btn1 = tk.Button(root, text="اختر صورة واحدة", command=open_single_image, width=25, bg="#4CAF50", fg="white")
btn1.pack(pady=10)

btn2 = tk.Button(root, text="اختر صور متعددة", command=open_multiple_images, width=25, bg="#2196F3", fg="white")
btn2.pack(pady=10)

root.mainloop()
