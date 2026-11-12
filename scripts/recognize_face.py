
import cv2
import json
import numpy as np
from pathlib import Path
from insightface.app import FaceAnalysis

# Cau hinh
CAMERA_INDEX = 0

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FACE_DIR = PROJECT_ROOT / "storage" / "faces"

# Nguong nhan dien ban dau, can kiem thu de hieu chinh
SIMILARITY_THRESHOLD = 0.45

WINDOW_NAME = "SMART HOME SECURITY - FACE RECOGNITION"


def load_registered_faces():
    database = {}

    for file_path in FACE_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            name = data["name"]
            embeddings = np.array(
                data["embeddings"],
                dtype=np.float32
            )

            if embeddings.ndim != 2 or len(embeddings) == 0:
                print(f"Du lieu khong hop le: {file_path.name}")
                continue

            # Chuan hoa embedding
            norms = np.linalg.norm(
                embeddings,
                axis=1,
                keepdims=True
            )
            embeddings = embeddings / np.maximum(norms, 1e-10)

            database[name] = embeddings

            print(
                f"Da nap: {name} - {len(embeddings)} mau"
            )

        except (OSError, ValueError, KeyError) as error:
            print(f"Loi doc {file_path.name}: {error}")

    return database


def recognize_face(face, database):
    current_embedding = face.normed_embedding.astype(
        np.float32
    )

    best_name = "UNKNOWN"
    best_score = -1.0

    for name, registered_embeddings in database.items():
        similarities = np.dot(
            registered_embeddings,
            current_embedding
        )

        score = float(np.max(similarities))

        if score > best_score:
            best_score = score
            best_name = name

    if best_score >= SIMILARITY_THRESHOLD:
        return best_name, best_score

    return "UNKNOWN", best_score


def main():
    print("=== SMART HOME SECURITY ===")
    print("DANG KHOI TAO HE THONG NHAN DIEN...")

    database = load_registered_faces()

    if not database:
        print("Chua co du lieu khuon mat!")
        return

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )
    app.prepare(
        ctx_id=-1,
        det_size=(640, 640)
    )

    print("AI da san sang!")

    cap = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW
    )

    if not cap.isOpened():
        print("KHONG THE MO WEBCAM!")
        return

    print("WEBCAM DA KET NOI!")
    print("Nhan Q hoac ESC de thoat.")

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("Khong doc duoc hinh anh!")
                break

            faces = app.get(frame)

            for face in faces:
                x1, y1, x2, y2 = face.bbox.astype(int)

                name, score = recognize_face(
                    face,
                    database
                )

                if name == "UNKNOWN":
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

                label = f"{name} - {score:.2f}"

                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

            cv2.putText(
                frame,
                f"Faces detected: {len(faces)}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                break

            if cv2.getWindowProperty(
                WINDOW_NAME,
                cv2.WND_PROP_VISIBLE
            ) < 1:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Da dong he thong nhan dien.")


if __name__ == "__main__":
    main()
