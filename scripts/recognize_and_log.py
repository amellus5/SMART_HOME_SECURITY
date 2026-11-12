
import cv2
import json
import sqlite3
import time
import numpy as np

from pathlib import Path
from datetime import datetime
from insightface.app import FaceAnalysis

from backend.app.services.event_service import save_detection_event


# ==========================================
# CAU HINH HE THONG
# ==========================================

CAMERA_INDEX = 0

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FACE_DIR = PROJECT_ROOT / "storage" / "faces"

SNAPSHOT_DIR = PROJECT_ROOT / "storage" / "snapshots"

DATABASE_PATH = (
    PROJECT_ROOT / "storage" / "database" / "smart_home.db"
)

SIMILARITY_THRESHOLD = 0.45

EVENT_COOLDOWN = 30

WINDOW_NAME = "SMART HOME SECURITY - AI EVENT LOGGING"


# ==========================================
# DOC DU LIEU KHUON MAT
# ==========================================

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
                continue

            norms = np.linalg.norm(
                embeddings,
                axis=1,
                keepdims=True
            )

            embeddings = embeddings / np.maximum(norms, 1e-10)

            database[name] = embeddings

            print(f"Da nap khuon mat: {name}")

        except (OSError, ValueError, KeyError) as error:

            print(f"Loi doc file {file_path.name}: {error}")

    return database


# ==========================================
# DOC ID THANH VIEN TU SQLITE
# ==========================================

def load_member_ids():

    connection = sqlite3.connect(DATABASE_PATH)

    try:

        rows = connection.execute("""
            SELECT id, full_name
            FROM family_members
            WHERE is_active = 1
        """).fetchall()

        return {
            name: member_id
            for member_id, name in rows
        }

    finally:

        connection.close()


# ==========================================
# NHAN DIEN KHUON MAT
# ==========================================

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


# ==========================================
# LUU SU KIEN VA ANH
# ==========================================

def log_detection_event(
    event_type,
    person_name,
    similarity,
    member_ids,
    frame
):

    member_id = member_ids.get(person_name)

    snapshot_path = None

    if event_type == "UNKNOWN":

        SNAPSHOT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        snapshot_file = (
            SNAPSHOT_DIR / f"unknown_{timestamp}.jpg"
        )

        saved = cv2.imwrite(
            str(snapshot_file),
            frame
        )

        if saved:

            snapshot_path = str(
                snapshot_file.relative_to(PROJECT_ROOT)
            )

    event_id = save_detection_event(
        event_type=event_type,
        person_name=person_name,
        similarity=similarity,
        snapshot_path=snapshot_path,
        camera_id=None,
        member_id=member_id
    )

    return event_id


# ==========================================
# CHUONG TRINH CHINH
# ==========================================

def main():

    print("===================================")
    print(" SMART HOME SECURITY")
    print(" AI FACE RECOGNITION + EVENT LOG")
    print("===================================")

    database = load_registered_faces()

    if not database:

        print("CHUA CO DU LIEU KHUON MAT!")
        return

    member_ids = load_member_ids()

    print("\nDANH SACH THANH VIEN:")

    for name in database:

        print(
            name,
            "- Member ID:",
            member_ids.get(name)
        )

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    app.prepare(
        ctx_id=-1,
        det_size=(640, 640)
    )

    cap = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW
    )

    if not cap.isOpened():

        print("KHONG THE MO CAMERA LAPTOP!")
        return

    print("\nHE THONG DA SAN SANG!")
    print("Nhan Q hoac ESC de thoat.")

    last_event_times = {}

    try:

        while True:

            ret, frame = cap.read()

            if not ret:

                print("KHONG DOC DUOC HINH ANH!")
                break

            faces = app.get(frame)

            for face in faces:

                name, score = recognize_face(
                    face,
                    database
                )

                if name == "UNKNOWN":

                    event_type = "UNKNOWN"
                    color = (0, 0, 255)

                else:

                    event_type = "KNOWN"
                    color = (0, 255, 0)

                x1, y1, x2, y2 = map(
                    int,
                    face.bbox
                )

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

                # Moi nguoi quen co mot khoa rieng.
                # Nguoi chua nhan dien dung chung khoa UNKNOWN.

                event_key = (
                    name if event_type == "KNOWN"
                    else "UNKNOWN"
                )

                current_time = time.monotonic()

                previous_time = last_event_times.get(
                    event_key,
                    0
                )

                if current_time - previous_time >= EVENT_COOLDOWN:

                    try:

                        event_id = log_detection_event(
                            event_type=event_type,
                            person_name=name,
                            similarity=score,
                            member_ids=member_ids,
                            frame=frame
                        )

                        last_event_times[event_key] = current_time

                        print(
                            f"Da ghi nhan su kien #{event_id}: "
                            f"{event_type} - {name}"
                        )

                    except Exception as error:

                        print(
                            "LOI LUU SU KIEN:",
                            error
                        )

            cv2.putText(
                frame,
                f"FACE COUNT: {len(faces)}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2
            )

            cv2.imshow(
                WINDOW_NAME,
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:

                break

    finally:

        cap.release()
        cv2.destroyAllWindows()

        print("\nDA DUNG HE THONG!")


if __name__ == "__main__":

    main()
