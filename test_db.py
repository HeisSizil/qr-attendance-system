import database as db

db.create_tables()
print("Tables created.")

db.add_student("MDU/CSC/001", "Samuel Chukwubunna")
print("Student added.")

name = db.student_exists("MDU/CSC/001")
print("Lookup result:", name)

print("Already scanned today?", db.already_scanned_today("MDU/CSC/001"))

db.log_attendance("MDU/CSC/001")
print("Attendance logged.")

print("Already scanned today (after logging)?", db.already_scanned_today("MDU/CSC/001"))