
import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FACE_DIR = PROJECT_ROOT / "storage" / "faces"
DATABASE_PATH = PROJECT_ROOT / "storage" / "database" / "smart_home.db"


def sync_faces():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        json_files = list(FACE_DIR.glob("*.json"))

        if not json_files:
            print("CHUA CO DU LIEU KHUON MAT!")
            return

        for file_path in json_files:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            name = data.get("name", "").strip()

            if not name:
                print("Bo qua file:", file_path.name)
                continue

            connection.execute(
                """
                INSERT INTO family_members (full_name, face_file)
                VALUES (?, ?)
                ON CONFLICT(full_name)
                DO UPDATE SET
                    face_file = excluded.face_file,
                    is_active = 1
                """,
                (name, file_path.name)
            )

            print("Da dong bo thanh vien:", name)

        connection.commit()
        print("\nDONG BO DATABASE THANH CONG!")

    except Exception as error:
        connection.rollback()
        print("LOI:", error)
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    sync_faces()
