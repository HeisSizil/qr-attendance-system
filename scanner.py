import cv2
from pyzbar import pyzbar
import time

import database as db

# How many seconds to wait before allowing another scan
# (prevents the same code being scanned 10+ times in one second)
COOLDOWN_SECONDS = 2

last_scan_time = 0
last_scanned_code = None


def start_scanning():
    """
    Opens the laptop webcam, continuously reads video frames,
    and checks each frame for a QR code. When one is found,
    it verifies the student and logs attendance.
    """
    global last_scan_time, last_scanned_code

    db.create_tables()

    cap = cv2.VideoCapture(0)  # 0 = default webcam

    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return

    print("Scanner started. Press 'q' to quit.")

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to read from webcam.")
            break

        decoded_objects = pyzbar.decode(frame)

        for obj in decoded_objects:
            matric_no = obj.data.decode("utf-8")
            current_time = time.time()

            # Draw a rectangle around the detected QR code on screen
            points = obj.polygon
            if len(points) == 4:
                pts = [(p.x, p.y) for p in points]
                for i in range(4):
                    cv2.line(frame, pts[i], pts[(i + 1) % 4], (0, 255, 0), 3)

            # Apply cooldown so the same code isn't processed repeatedly
            if matric_no == last_scanned_code and (current_time - last_scan_time) < COOLDOWN_SECONDS:
                continue

            last_scanned_code = matric_no
            last_scan_time = current_time

            process_scan(matric_no)

        cv2.imshow("QR Attendance Scanner - Press 'q' to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def process_scan(matric_no):
    """
    Given a decoded matric number, checks it against the database
    and logs attendance if valid and not already scanned today.
    """
    student_name = db.student_exists(matric_no)

    if student_name is None:
        print(f"❌ Unknown code scanned: {matric_no} — not a registered student.")
        return

    if db.already_scanned_today(matric_no):
        print(f"⚠️  {student_name} ({matric_no}) has already been marked present today.")
        return

    db.log_attendance(matric_no)
    print(f"✅ Attendance recorded for {student_name} ({matric_no}).")


if __name__ == "__main__":
    start_scanning()