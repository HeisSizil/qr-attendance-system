import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import csv

import database as db
from qr_generator import generate_qr_for_student
from scanner import start_scanning


def register_student():
    """Asks the lecturer for a matric number and name, then registers the student and generates their QR code."""
    matric_no = simpledialog.askstring("Register Student", "Enter Matric Number:")
    if not matric_no:
        return

    full_name = simpledialog.askstring("Register Student", "Enter Full Name:")
    if not full_name:
        return

    try:
        db.add_student(matric_no.strip(), full_name.strip())
        generate_qr_for_student(matric_no.strip())
        messagebox.showinfo("Success", f"{full_name} registered and QR code generated.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not register student:\n{e}")


def launch_scanner():
    """Opens the webcam scanning window for an attendance session."""
    messagebox.showinfo("Scanner", "The scanner window will open now. Press 'q' in that window to close it when done.")
    start_scanning()


def view_report():
    """Displays today's attendance in a new window, with an option to export to CSV."""
    rows = db.get_today_report()

    report_window = tk.Toplevel(root)
    report_window.title("Today's Attendance Report")
    report_window.geometry("500x400")

    tree = ttk.Treeview(report_window, columns=("matric", "name", "time"), show="headings")
    tree.heading("matric", text="Matric No")
    tree.heading("name", text="Full Name")
    tree.heading("time", text="Time")
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    for row in rows:
        tree.insert("", "end", values=row)

    def export_csv():
        if not rows:
            messagebox.showwarning("No Data", "There is no attendance data to export yet.")
            return
        filename = "attendance_report.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Matric No", "Full Name", "Time"])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Report saved as {filename}")

    export_btn = tk.Button(report_window, text="Export to CSV", command=export_csv)
    export_btn.pack(pady=10)


# ---- Main Dashboard Window ----
root = tk.Tk()
root.title("QR Code Attendance System")
root.geometry("400x350")

title_label = tk.Label(root, text="Attendance Dashboard", font=("Arial", 16, "bold"))
title_label.pack(pady=20)

register_btn = tk.Button(root, text="Register New Student", width=30, height=2, command=register_student)
register_btn.pack(pady=10)

scan_btn = tk.Button(root, text="Start Attendance Scan", width=30, height=2, command=launch_scanner)
scan_btn.pack(pady=10)

report_btn = tk.Button(root, text="View Today's Report", width=30, height=2, command=view_report)
report_btn.pack(pady=10)

root.mainloop()