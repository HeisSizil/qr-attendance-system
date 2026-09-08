import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import csv
import cv2
import os
from datetime import datetime
from PIL import Image, ImageTk

import database as db
from qr_generator import generate_qr_for_student
from scanner import start_scanning

PHOTOS_FOLDER = "photos"

def take_photo(matric_no):
    if not os.path.exists(PHOTOS_FOLDER):
        os.makedirs(PHOTOS_FOLDER)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Could not access webcam.")
        return None
    messagebox.showinfo("Take Photo", "Click OK then look at the camera. Photo will be taken in 3 seconds.")
    import time
    time.sleep(3)
    success, frame = cap.read()
    cap.release()
    if not success:
        messagebox.showerror("Error", "Could not capture photo.")
        return None
    safe_name = matric_no.replace("/", "_")
    photo_path = os.path.join(PHOTOS_FOLDER, f"{safe_name}.png")
    cv2.imwrite(photo_path, frame)
    return photo_path


def register_student():
    matric_no = simpledialog.askstring("Register Student", "Enter Matric Number:")
    if not matric_no:
        return
    matric_no = matric_no.strip()
    full_name = simpledialog.askstring("Register Student", "Enter Full Name:")
    if not full_name:
        return
    full_name = full_name.strip()
    take = messagebox.askyesno("Take Photo", f"Do you want to take a photo of {full_name} now?")
    photo_path = None
    if take:
        photo_path = take_photo(matric_no)
        if photo_path:
            messagebox.showinfo("Photo", "Photo captured successfully.")
    try:
        db.add_student(matric_no, full_name, photo_path)
        generate_qr_for_student(matric_no)
        update_stats()
        messagebox.showinfo("Success", f"{full_name} registered and QR code generated.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not register student:\n{e}")


def show_photo_window(title, name, matric, photo_path, extra_info=""):
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry("320x400")
    win.resizable(False, False)
    tk.Label(win, text=name, font=("Arial", 13, "bold")).pack(pady=(16, 2))
    tk.Label(win, text=matric, font=("Arial", 11), fg="gray").pack()
    if extra_info:
        tk.Label(win, text=extra_info, font=("Arial", 11)).pack(pady=4)
    if photo_path and os.path.exists(photo_path):
        img = Image.open(photo_path)
        img = img.resize((240, 240))
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(win, image=photo)
        lbl.image = photo
        lbl.pack(pady=10)
    else:
        tk.Label(win, text="No photo available", font=("Arial", 11), fg="gray").pack(pady=40)
    tk.Button(win, text="Close", command=win.destroy, width=20).pack(pady=10)


def launch_scanner():
    messagebox.showinfo("Scanner", "Scanner window will open now. Press 'q' to close it when done.")
    start_scanning()
    update_stats()


def view_report():
    rows = db.get_today_report()
    report_window = tk.Toplevel(root)
    report_window.title("Today's Attendance Report")
    report_window.geometry("520x400")
    tree = ttk.Treeview(report_window, columns=("matric", "name", "time"), show="headings")
    tree.heading("matric", text="Matric No")
    tree.heading("name", text="Full Name")
    tree.heading("time", text="Time")
    tree.column("matric", width=140)
    tree.column("name", width=220)
    tree.column("time", width=100)
    tree.pack(fill="both", expand=True, padx=10, pady=10)
    for row in rows:
        tree.insert("", "end", values=row)

    def export_csv():
        if not rows:
            messagebox.showwarning("No Data", "No attendance data to export yet.")
            return
        filename = "attendance_report.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Matric No", "Full Name", "Time"])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Report saved as {filename}")

    tk.Button(report_window, text="Export to CSV", command=export_csv, width=20).pack(pady=10)


def view_all_students():
    rows = db.get_all_students()
    win = tk.Toplevel(root)
    win.title("All Registered Students")
    win.geometry("520x400")
    tree = ttk.Treeview(win, columns=("matric", "name"), show="headings")
    tree.heading("matric", text="Matric No")
    tree.heading("name", text="Full Name")
    tree.column("matric", width=160)
    tree.column("name", width=300)
    tree.pack(fill="both", expand=True, padx=10, pady=10)
    for row in rows:
        tree.insert("", "end", values=(row[0], row[1]))

    def on_select(event):
        selected = tree.focus()
        if not selected:
            return
        values = tree.item(selected, "values")
        if values:
            matric = values[0]
            name = values[1]
            photo = db.get_student_photo(matric)
            show_photo_window("Student Profile", name, matric, photo)

    tree.bind("<Double-1>", on_select)
    tk.Label(win, text="Double-click a student to view their profile",
             font=("Arial", 10), fg="gray").pack()


def search_student():
    matric_no = simpledialog.askstring("Search Student", "Enter Matric Number:")
    if not matric_no:
        return
    matric_no = matric_no.strip()
    name = db.student_exists(matric_no)
    if not name:
        messagebox.showwarning("Not Found", f"No student found with matric number {matric_no}.")
        return
    photo = db.get_student_photo(matric_no)
    scanned_today = db.already_scanned_today(matric_no)
    status = "Present today" if scanned_today else "Not yet scanned today"
    show_photo_window("Student Profile", name, matric_no, photo, status)


def remove_student():
    matric_no = simpledialog.askstring("Remove Student", "Enter Matric Number to remove:")
    if not matric_no:
        return
    matric_no = matric_no.strip()
    name = db.student_exists(matric_no)
    if not name:
        messagebox.showwarning("Not Found", f"No student found with matric number {matric_no}.")
        return
    confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove {name} ({matric_no})?\nThis will also delete their attendance history.")
    if not confirm:
        return
    db.remove_student(matric_no)
    update_stats()
    messagebox.showinfo("Removed", f"{name} has been removed from the system.")


def view_qr_codes():
    rows = db.get_all_students()
    win = tk.Toplevel(root)
    win.title("Student QR Codes")
    win.geometry("600x500")

    canvas = tk.Canvas(win)
    scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    qr_images = []

    for matric, name, _ in rows:
        card = tk.Frame(scroll_frame, bd=1, relief="solid", padx=10, pady=10, bg="white")
        card.pack(fill="x", padx=10, pady=6)

        safe_name = matric.replace("/", "_")
        qr_path = os.path.join("qr_codes", f"{safe_name}.png")

        left = tk.Frame(card, bg="white")
        left.pack(side="left", padx=(0, 10))
        tk.Label(left, text=name, font=("Arial", 11, "bold"), bg="white").pack(anchor="w")
        tk.Label(left, text=matric, font=("Arial", 10), fg="gray", bg="white").pack(anchor="w")

        if os.path.exists(qr_path):
            img = Image.open(qr_path)
            img = img.resize((100, 100))
            photo = ImageTk.PhotoImage(img)
            qr_label = tk.Label(card, image=photo, bg="white")
            qr_label.image = photo
            qr_label.pack(side="right")
            qr_images.append(photo)
        else:
            tk.Label(card, text="QR not found", fg="red", bg="white").pack(side="right")


def update_stats():
    all_students = db.get_all_students()
    today_report = db.get_today_report()
    registered_label.config(text=str(len(all_students)))
    present_label.config(text=str(len(today_report)))


def update_clock():
    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")
    time_str = now.strftime("%H:%M:%S")
    date_label.config(text=date_str)
    time_label.config(text=time_str)
    root.after(1000, update_clock)


# ===== MAIN WINDOW =====
root = tk.Tk()
root.title("QR Attendance System — University of Maiduguri")
root.geometry("480x720")
root.resizable(False, False)

# Header
header = tk.Frame(root, bg="#003366", pady=14)
header.pack(fill="x")

try:
    logo_img = Image.open("logo.png")
    logo_img = logo_img.resize((60, 60))
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(header, image=logo_photo, bg="#003366")
    logo_label.image = logo_photo
    logo_label.pack(pady=(0, 6))
except:
    pass

tk.Label(header, text="UNIVERSITY OF MAIDUGURI", bg="#003366", fg="white",
         font=("Arial", 12, "bold")).pack()
tk.Label(header, text="Department of Computer Science", bg="#003366", fg="#aaccff",
         font=("Arial", 10)).pack()
tk.Label(header, text="QR Code Attendance System", bg="#003366", fg="#aaccff",
         font=("Arial", 9)).pack()

# Date and time
time_frame = tk.Frame(root, pady=6, bg="#f0f0f0")
time_frame.pack(fill="x")
date_label = tk.Label(time_frame, text="", font=("Arial", 10), bg="#f0f0f0", fg="#333")
date_label.pack()
time_label = tk.Label(time_frame, text="", font=("Arial", 10, "bold"), bg="#f0f0f0", fg="#003366")
time_label.pack()

# Stats
stats_frame = tk.Frame(root, pady=10)
stats_frame.pack(fill="x", padx=20)

reg_card = tk.Frame(stats_frame, bd=1, relief="solid", padx=20, pady=10, bg="white")
reg_card.pack(side="left", expand=True, fill="both", padx=(0, 8))
tk.Label(reg_card, text="Registered Students", font=("Arial", 9), fg="gray", bg="white").pack()
registered_label = tk.Label(reg_card, text="0", font=("Arial", 20, "bold"), bg="white", fg="#003366")
registered_label.pack()

pres_card = tk.Frame(stats_frame, bd=1, relief="solid", padx=20, pady=10, bg="white")
pres_card.pack(side="left", expand=True, fill="both", padx=(8, 0))
tk.Label(pres_card, text="Present Today", font=("Arial", 9), fg="gray", bg="white").pack()
present_label = tk.Label(pres_card, text="0", font=("Arial", 20, "bold"), bg="white", fg="#28a745")
present_label.pack()

# Divider
tk.Frame(root, height=1, bg="#dddddd").pack(fill="x", padx=20, pady=6)

# Buttons
btn_frame = tk.Frame(root, padx=20)
btn_frame.pack(fill="x")

buttons = [
    ("Register New Student", register_student),
    ("Start Attendance Scan", launch_scanner),
    ("View Today's Report", view_report),
    ("View All Registered Students", view_all_students),
    ("Search Student", search_student),
    ("Remove Student", remove_student),
    ("View Student QR Codes", view_qr_codes),
]

for label, cmd in buttons:
    tk.Button(btn_frame, text=label, command=cmd, width=36, height=2,
              font=("Arial", 10), bg="white", relief="solid", bd=1,
              activebackground="#e8f0fe").pack(pady=4)

# Status bar
status_frame = tk.Frame(root, bg="#e8f5e9", pady=6)
status_frame.pack(fill="x", side="bottom")
tk.Label(status_frame, text="System ready", font=("Arial", 9),
         bg="#e8f5e9", fg="#2e7d32").pack()

update_clock()
update_stats()
root.mainloop()