
import cv2
from getpass import getpass
from urllib.parse import quote

CAMERA_IP = "192.168.1.8"
RTSP_PORT = 554

username = input("Username camera: ")
password = getpass("Password camera: ")

user = quote(username, safe="")
pwd = quote(password, safe="")

rtsp_url = (
    f"rtsp://{user}:{pwd}"
    f"@{CAMERA_IP}:{RTSP_PORT}/cam/realmonitor?channel=1&subtype=0"
)

print("Dang ket noi camera...")

cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("KHONG THE KET NOI CAMERA")
else:
    print("DA KET NOI CAMERA!")
    print("Nhan Q de thoat.")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Khong doc duoc khung hinh.")
            break

        cv2.imshow("SMART HOME SECURITY - DAHUA H3I", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
