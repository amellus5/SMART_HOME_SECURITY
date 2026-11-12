
from sqlite3 import Error, connect, Row
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(
    prefix="/api/events",
    tags=["Detection Events"]
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = (
    PROJECT_ROOT / "storage" / "database" / "smart_home.db"
)

SNAPSHOT_DIR = (
    PROJECT_ROOT / "storage" / "snapshots"
).resolve()


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
        connection.row_factory = Row

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


@router.get("/stats")
def get_event_statistics():
    """Lay thong ke tong quan cac su kien phat hien."""

    connection = None

    try:
        connection = connect(DATABASE_PATH)
        connection.row_factory = Row

        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_events,
                SUM(
                    CASE WHEN event_type = 'KNOWN'
                    THEN 1 ELSE 0 END
                ) AS known_events,
                SUM(
                    CASE WHEN event_type = 'UNKNOWN'
                    THEN 1 ELSE 0 END
                ) AS unknown_events
            FROM detection_events
        """)

        statistics = cursor.fetchone()

        cursor.execute("""
            SELECT
                id,
                event_type,
                person_name,
                similarity,
                snapshot_path,
                detected_at
            FROM detection_events
            ORDER BY detected_at DESC, id DESC
            LIMIT 1
        """)

        latest_event = cursor.fetchone()

        return {
            "status": "success",
            "statistics": {
                "total_events": statistics["total_events"] or 0,
                "known_events": statistics["known_events"] or 0,
                "unknown_events": statistics["unknown_events"] or 0
            },
            "latest_event": (
                dict(latest_event)
                if latest_event else None
            )
        }

    except Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    finally:
        if connection:
            connection.close()


@router.get("/{event_id}/snapshot")
def get_event_snapshot(event_id: int):
    """Lay anh chup cua mot su kien phat hien."""

    connection = None

    try:
        connection = connect(DATABASE_PATH)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT snapshot_path
            FROM detection_events
            WHERE id = ?
        """, (event_id,))

        event = cursor.fetchone()

    except Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    finally:
        if connection:
            connection.close()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay su kien."
        )

    snapshot_path = event[0]

    if not snapshot_path:
        raise HTTPException(
            status_code=404,
            detail="Su kien nay khong co anh chup."
        )

    try:
        image_path = (
            PROJECT_ROOT / snapshot_path
        ).resolve()

        image_path.relative_to(SNAPSHOT_DIR)

    except (ValueError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Duong dan anh khong hop le."
        )

    if not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay file anh."
        )

    return FileResponse(
        path=image_path,
        media_type="image/jpeg",
        filename=image_path.name
    )
