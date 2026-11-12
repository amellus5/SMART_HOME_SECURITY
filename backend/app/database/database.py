
import sqlite3
from pathlib import Path

# Xac dinh thu muc goc cua du an
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Thu muc luu Database
DATABASE_DIR = PROJECT_ROOT / "storage" / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "smart_home.db"


def get_connection():
    """Tao ket noi den SQLite Database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Khoi tao cac bang trong Database."""
    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Bang thanh vien gia dinh
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                face_file TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Bang camera
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                location TEXT,
                status TEXT DEFAULT 'offline',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Bang su kien phat hien
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id INTEGER,
                member_id INTEGER,
                event_type TEXT NOT NULL
                    CHECK(event_type IN ('KNOWN', 'UNKNOWN')),
                person_name TEXT,
                similarity REAL,
                snapshot_path TEXT,
                detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                notification_status TEXT DEFAULT 'pending',

                FOREIGN KEY (camera_id)
                    REFERENCES cameras(id),

                FOREIGN KEY (member_id)
                    REFERENCES family_members(id)
            )
        """)

        connection.commit()

        print("KHOI TAO DATABASE THANH CONG!")
        print("Database:", DATABASE_PATH)

    except sqlite3.Error as error:
        connection.rollback()
        print("LOI DATABASE:", error)
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
