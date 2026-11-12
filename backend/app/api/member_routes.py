
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/api/members",
    tags=["Family Members"]
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = (
    PROJECT_ROOT / "storage" / "database" / "smart_home.db"
)


@router.get("/")
def get_family_members():
    """Lay danh sach thanh vien gia dinh."""

    connection = None

    try:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                full_name,
                created_at,
                is_active
            FROM family_members
            ORDER BY id ASC
        """)

        members = cursor.fetchall()

        return {
            "status": "success",
            "total": len(members),
            "members": [
                dict(member) for member in members
            ]
        }

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    finally:
        if connection:
            connection.close()
