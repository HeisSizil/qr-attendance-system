import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"


def get_connection():
    """Opens a connection to our local SQLite database file."""
    return sqlite3.connect(DB_NAME)


def create_tables():
    """Creates the Students and Attendance tables if they don't exist yet."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            matric_no TEXT PRIMARY KEY,
            full_name TEXT NOT NULL
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


def add_student(matric_no, full_name):
    """Registers a new student in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (matric_no, full_name) VALUES (?, ?)",
        (matric_no, full_name)
    )
    conn.commit()
    conn.close()


def student_exists(matric_no):
    """Checks if a scanned matric number belongs to a registered student."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM students WHERE matric_no = ?", (matric_no,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def already_scanned_today(matric_no):
    """Checks if this student has already been marked present today (duplicate-scan prevention)."""
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
    """Records a new attendance entry with the current date and time."""
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
    """Returns a list of (matric_no, full_name, scan_time) for everyone marked present today."""
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