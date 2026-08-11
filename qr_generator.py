import qrcode
import os

QR_FOLDER = "qr_codes"


def generate_qr_for_student(matric_no):
    """
    Creates a QR code image that encodes a student's matric number,
    and saves it as a PNG file inside the qr_codes folder.
    """
    if not os.path.exists(QR_FOLDER):
        os.makedirs(QR_FOLDER)

    qr_img = qrcode.make(matric_no)

    safe_filename = matric_no.replace("/", "_")
    file_path = os.path.join(QR_FOLDER, f"{safe_filename}.png")

    qr_img.save(file_path)
    print(f"QR code saved to: {file_path}")

    return file_path