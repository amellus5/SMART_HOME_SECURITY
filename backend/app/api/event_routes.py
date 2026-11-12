
from sqlite3 import Error, connect
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(
    prefix="/api/events",
    tags=["Detection Events"]
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = (
    PROJECT_ROOT / "storage" / "database" / "smart_home.db"
)


@router.get("/")
def get_detection_events(
    event_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100)
):
    """Lay lich su phat hien khuon mat."""

    if event_type is not None:
        event_type = event_type.upper()

        if event_type not in ("KNOWN", "UNKNOWN"):
            raise HTTPException(
                status_code=400,
                detail="event_type phai la KNOWN hoac UNKNOWN"
            )

    connection = None

    try:
        connection = connect(DATABASE_PATH)
        connection.row_factory = __import__("sqlite3").Row

        cursor = connection.cursor()

        if event_type:
            cursor.execute("""
                SELECT
                    id,
                    camera_id,
                    member_id,
                    event_type,
                    person_name,
                    similarity,
                    snapshot_path,
                    detected_at,
                    notification_status
                FROM detection_events
                WHERE event_type = ?
                ORDER BY detected_at DESC, id DESC
                LIMIT ?
            """, (event_type, limit))
        else:
            cursor.execute("""
                SELECT
                    id,
                    camera_id,
                    member_id,
                    event_type,
                    person_name,
                    similarity,
                    snapshot_path,
                    detected_at,
                    notification_status
                FROM detection_events
                ORDER BY detected_at DESC, id DESC
                LIMIT ?
            """, (limit,))

        events = cursor.fetchall()

        return {
            "status": "success",
            "total": len(events),
            "events": [dict(event) for event in events]
        }

    except Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    finally:
        if connection:
            connection.close()
