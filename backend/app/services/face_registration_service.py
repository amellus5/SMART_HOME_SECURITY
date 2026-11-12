
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import cv2
from insightface.app import FaceAnalysis


PROJECT_ROOT = Path(__file__).resolve().parents[3]

FACE_DIR = PROJECT_ROOT / "storage" / "faces"
DATABASE_PATH = (
    PROJECT_ROOT / "storage" / "database" / "smart_home.db"
)

CAMERA_INDEX = 0
REQUIRED_SAMPLES = 10
WINDOW_NAME = "SMART HOME SECURITY - REGISTER MEMBER"


def validate_member_name(name: str) -> str:
    name = name.strip()

    if not name:
        raise ValueError("Ten thanh vien khong duoc de trong!")

    if len(name) > 100:
        raise ValueError("Ten thanh vien khong duoc vuot qua 100 ky tu!")

    safe_name = re.sub(
        r"[^\w-]",
        "_",
        name,
        flags=re.UNICODE
    )

    if not safe_name.strip("_"):
        raise ValueError("Ten thanh vien khong hop le!")

    return safe_name


def check_duplicate_member(name: str, file_path: Path):
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        member = connection.execute(
            """
            SELECT id
            FROM family_members
            WHERE full_name = ?
            """,
            (name,)
        ).fetchone()

        if member:
            raise ValueError(
                "Ten thanh vien da ton tai trong Database!"
            )

        if file_path.exists():
            raise ValueError(
                "File khuon mat da ton tai, khong ghi de du lieu cu!"
            )

    finally:
        connection.close()


def capture_face_embeddings(app) -> list:
    cap = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW
    )

    if not cap.isOpened():
        raise RuntimeError("Khong the mo webcam laptop!")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    embeddings = []
    cancelled = False

    print("\nHUONG DAN DANG KY:")
    print("- Nhin thang vao webcam.")
    print("- Xoay mat nhe sang trai, phai.")
    print("- Moi lan nhan SPACE se luu mot mau.")
    print("- Chi cho phep mot khuon mat trong khung hinh.")
    print("- Nhan Q hoac ESC de huy.")
    print(f"- Can thu thap {REQUIRED_SAMPLES} mau.")

    try:
        while len(embeddings) < REQUIRED_SAMPLES:
            ret, frame = cap.read()

            if not ret:
                raise RuntimeError(
                    "Khong doc duoc hinh anh webcam!"
                )

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
                cancelled = True
                break

            if key == 32:
                if len(faces) != 1:
                    print(
                        "Can dung truoc webcam voi duy nhat mot khuon mat!"
                    )
                    continue

                embedding = faces[0].normed_embedding

                embeddings.append(
                    embedding.astype(float).tolist()
                )

                print(
                    f"Da thu thap {len(embeddings)}/{REQUIRED_SAMPLES} mau"
                )

            if cv2.getWindowProperty(
                WINDOW_NAME,
                cv2.WND_PROP_VISIBLE
            ) < 1:
                cancelled = True
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    if cancelled:
        raise RuntimeError(
            "Da huy qua trinh dang ky khuon mat!"
        )

    if len(embeddings) != REQUIRED_SAMPLES:
        raise RuntimeError(
            "Khong thu thap du 10 mau khuon mat!"
        )

    return embeddings


def register_member(name: str) -> dict:
    name = name.strip()
    safe_name = validate_member_name(name)

    FACE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file_name = f"{safe_name}.json"
    file_path = FACE_DIR / file_name

    check_duplicate_member(name, file_path)

    print("\nDang khoi tao InsightFace...")

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    app.prepare(
        ctx_id=-1,
        det_size=(640, 640)
    )

    print("Khoi tao AI thanh cong!")

    embeddings = capture_face_embeddings(app)

    data = {
        "name": name,
        "embeddings": embeddings,
        "sample_count": len(embeddings),
        "created_at": datetime.now().isoformat()
    }

    temp_path = FACE_DIR / (
        f".{safe_name}_{uuid.uuid4().hex}.tmp"
    )

    connection = None
    final_file_created = False

    try:
        # Ghi du lieu vao file tam truoc
        with open(
            temp_path,
            "x",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

            file.flush()
            os.fsync(file.fileno())

        # Bat dau transaction va kiem tra trung lan cuoi
        connection = sqlite3.connect(DATABASE_PATH)

        connection.execute("BEGIN IMMEDIATE")

        existing_member = connection.execute(
            """
            SELECT id
            FROM family_members
            WHERE full_name = ?
            """,
            (name,)
        ).fetchone()

        if existing_member:
            raise ValueError(
                "Ten thanh vien da ton tai trong Database!"
            )

        if file_path.exists():
            raise ValueError(
                "File khuon mat da ton tai, khong ghi de du lieu cu!"
            )

        # Doi ten file tam thanh file chinh thuc.
        # os.rename tren Windows se bao loi neu dich da ton tai.
        os.rename(temp_path, file_path)
        final_file_created = True

        # Them thanh vien vao Database
        cursor = connection.execute(
            """
            INSERT INTO family_members (
                full_name,
                face_file
            )
            VALUES (?, ?)
            """,
            (name, file_name)
        )

        member_id = cursor.lastrowid

        # Chi commit sau khi ca file va Database da san sang
        connection.commit()

        print("\nDANG KY THANH CONG!")

        return {
            "id": member_id,
            "full_name": name,
            "face_file": file_name,
            "sample_count": len(embeddings)
        }

    except Exception:
        if connection:
            connection.rollback()

        # Chi xoa file do chinh lan dang ky nay tao ra
        if final_file_created and file_path.exists():
            file_path.unlink()

        raise

    finally:
        if temp_path.exists():
            temp_path.unlink()

        if connection:
            connection.close()
