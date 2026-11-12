
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_PATH = (
    PROJECT_ROOT / "storage" / "database" / "smart_home.db"
)


def save_detection_event(
    event_type,
    person_name=None,
    similarity=None,
    snapshot_path=None,
    camera_id=None,
    member_id=None
):
    """
    Luu su kien phat hien khuon mat vao Database.
    
    event_type:
        KNOWN   - Nguoi da dang ky
        UNKNOWN - Nguoi chua duoc nhan dien
    """

    event_type = event_type.upper()

    if event_type not in ("KNOWN", "UNKNOWN"):
        raise ValueError("Loai su kien khong hop le!")

    if event_type == "UNKNOWN":
        member_id = None

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO detection_events (
                camera_id,
                member_id,
                event_type,
                person_name,
                similarity,
                snapshot_path
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            camera_id,
            member_id,
            event_type,
            person_name,
            similarity,
            snapshot_path
        ))

        connection.commit()

        event_id = cursor.lastrowid

        print("DA LUU SU KIEN PHAT HIEN!")
        print("Event ID:", event_id)
        print("Loai su kien:", event_type)

        return event_id

    except sqlite3.Error as error:
        connection.rollback()
        print("LOI LUU SU KIEN:", error)
        raise

    finally:
        connection.close()
