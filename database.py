import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            matric_no TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            photo_path TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matric_no TEXT NOT NULL,
            scan_date TEXT NOT NULL,
            scan_time TEXT NOT NULL,
            FOREIGN KEY (matric_no) REFERENCES students (matric_no)
        )
    """)

    conn.commit()
    conn.close()


def add_student(matric_no, full_name, photo_path=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (matric_no, full_name, photo_path) VALUES (?, ?, ?)",
        (matric_no, full_name, photo_path)
    )
    conn.commit()
    conn.close()


def student_exists(matric_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM students WHERE matric_no = ?", (matric_no,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_student_photo(matric_no):
    """Returns the saved photo file path for a student, or None if they have no photo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT photo_path FROM students WHERE matric_no = ?", (matric_no,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else None


def get_all_students():
    """Returns a list of (matric_no, full_name, photo_path) for every registered student."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT matric_no, full_name, photo_path FROM students ORDER BY full_name")
    rows = cursor.fetchall()
    conn.close()
    return rows


def remove_student(matric_no):
    """Deletes a student and their attendance history from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE matric_no = ?", (matric_no,))
    cursor.execute("DELETE FROM students WHERE matric_no = ?", (matric_no,))
    conn.commit()
    conn.close()


def already_scanned_today(matric_no):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM attendance WHERE matric_no = ? AND scan_date = ?",
        (matric_no, today)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def log_attendance(matric_no):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attendance (matric_no, scan_date, scan_time) VALUES (?, ?, ?)",
        (matric_no, date_str, time_str)
    )
    conn.commit()
    conn.close()


def get_today_report():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT attendance.matric_no, students.full_name, attendance.scan_time
        FROM attendance
        JOIN students ON attendance.matric_no = students.matric_no
        WHERE attendance.scan_date = ?
        ORDER BY attendance.scan_time
    """, (today,))
    rows = cursor.fetchall()
    conn.close()
    return rows