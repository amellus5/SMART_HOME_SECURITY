
import cv2
import json
import re
from pathlib import Path
from datetime import datetime
from insightface.app import FaceAnalysis

# Camera laptop
CAMERA_INDEX = 0

# Thu muc luu du lieu khuon mat
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FACE_DIR = PROJECT_ROOT / "storage" / "faces"
FACE_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_SAMPLES = 10
WINDOW_NAME = "SMART HOME SECURITY - REGISTER FACE"


def main():
    print("=== DANG KY KHUON MAT THANH VIEN ===")

    name = input("Nhap ten thanh vien: ").strip()

    if not name:
        print("Ten khong duoc de trong!")
        return

    # Tao ten file an toan
    safe_name = re.sub(r"[^\w-]", "_", name, flags=re.UNICODE)

    if not safe_name.strip("_"):
        print("Ten khong hop le!")
        return

    file_path = FACE_DIR / f"{safe_name}.json"

    if file_path.exists():
        print("Thanh vien nay da co du lieu dang ky!")
        print("Khong ghi de du lieu cu.")
        return

    print("\nDang khoi tao InsightFace...")

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))

    print("Khoi tao AI thanh cong!")

    # Mo webcam laptop
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("KHONG THE MO WEBCAM LAPTOP!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    embeddings = []
    cancelled = False

    print("\nHUONG DAN:")
    print("- Nhin thang vao webcam.")
    print("- Xoay mat nhe sang trai, phai.")
    print("- Moi lan nhan SPACE se luu mot mau.")
    print("- Can dam bao chi co mot khuon mat.")
    print("- Nhan Q hoac ESC de huy.")
    print(f"- Can thu thap {REQUIRED_SAMPLES} mau.")

    try:
        while len(embeddings) < REQUIRED_SAMPLES:
            ret, frame = cap.read()

            if not ret:
                print("Khong doc duoc hinh anh webcam!")
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

            cv2.putText(
                frame,
                f"Samples: {len(embeddings)}/{REQUIRED_SAMPLES}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "SPACE: Capture | Q: Cancel",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Faces detected: {len(faces)}",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                print("Da huy dang ky.")
                cancelled = True
                break

            if key == 32:
                if len(faces) != 1:
                    print("Can dung truoc camera voi duy nhat mot khuon mat!")
                    continue

                embedding = faces[0].normed_embedding

                embeddings.append(
                    embedding.astype(float).tolist()
                )

                print(
                    f"Da luu mau {len(embeddings)}/{REQUIRED_SAMPLES}"
                )

            if cv2.getWindowProperty(
                WINDOW_NAME,
                cv2.WND_PROP_VISIBLE
            ) < 1:
                cancelled = True
                print("Cua so camera da dong.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    if cancelled:
        print("Dang ky da huy. Khong luu du lieu.")
        return

    if len(embeddings) != REQUIRED_SAMPLES:
        print("Chua du 10 mau. Khong luu du lieu.")
        return

    data = {
        "name": name,
        "embeddings": embeddings,
        "sample_count": len(embeddings),
        "created_at": datetime.now().isoformat()
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print("\nDANG KY THANH CONG!")
    print("Thanh vien:", name)
    print("So mau:", len(embeddings))
    print("Du lieu duoc luu tai:", file_path)


if __name__ == "__main__":
    main()
