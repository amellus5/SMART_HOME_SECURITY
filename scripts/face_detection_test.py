
import cv2
from getpass import getpass
from urllib.parse import quote
from insightface.app import FaceAnalysis

CAMERA_IP = "192.168.1.8"
RTSP_PORT = 554
WINDOW_NAME = "SMART HOME SECURITY - FACE DETECTION"


def main():
    username = input("Username camera: ")
    password = getpass("Password camera: ")

    user = quote(username, safe="")
    pwd = quote(password, safe="")

    rtsp_url = (
        f"rtsp://{user}:{pwd}"
        f"@{CAMERA_IP}:{RTSP_PORT}/cam/realmonitor?channel=1&subtype=0"
    )

    print("Dang khoi tao InsightFace...")

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))

    print("Khoi tao AI thanh cong!")
    print("Dang ket noi camera...")

    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        print("KHONG THE KET NOI CAMERA")
        return

    print("DA KET NOI CAMERA!")
    print("Nhan Q hoac ESC de thoat.")

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Khong doc duoc khung hinh.")
                break

            faces = app.get(frame)

            for face in faces:
                x1, y1, x2, y2 = face.bbox.astype(int)

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                score = float(face.det_score)

                cv2.putText(
                    frame,
                    f"Face: {score:.2f}",
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

            cv2.putText(
                frame,
                f"Detected faces: {len(faces)}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                print("Dang dong chuong trinh...")
                break

            if cv2.getWindowProperty(
                WINDOW_NAME,
                cv2.WND_PROP_VISIBLE
            ) < 1:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Da dong chuong trinh.")


if __name__ == "__main__":
    main()
