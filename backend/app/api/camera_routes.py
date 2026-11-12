
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/api/cameras",
    tags=["Camera Management"]
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = (
    PROJECT_ROOT / "storage" / "database" / "smart_home.db"
)


class CameraCreate(BaseModel):
    camera_name: str = Field(min_length=1, max_length=100)
    source_type: str = Field(default="RTSP")
    location: str | None = None


class CameraUpdate(BaseModel):
    camera_name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = None
    status: str | None = None


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@router.get("/")
def get_cameras():
    connection = get_db_connection()

    try:
        cameras = connection.execute("""
            SELECT
                id,
                camera_name,
                source_type,
                location,
                status,
                created_at
            FROM cameras
            ORDER BY id DESC
        """).fetchall()

        return {
            "status": "success",
            "total": len(cameras),
            "cameras": [dict(camera) for camera in cameras]
        }

    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        connection.close()


@router.post("/")
def create_camera(camera: CameraCreate):
    connection = get_db_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO cameras (
                camera_name,
                source_type,
                location,
                status
            )
            VALUES (?, ?, ?, 'offline')
        """, (
            camera.camera_name.strip(),
            camera.source_type.strip(),
            camera.location
        ))

        connection.commit()

        return {
            "status": "success",
            "message": "Them camera thanh cong!",
            "camera_id": cursor.lastrowid
        }

    except sqlite3.Error as error:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        connection.close()


@router.put("/{camera_id}")
def update_camera(camera_id: int, camera: CameraUpdate):
    connection = get_db_connection()

    try:
        existing = connection.execute(
            "SELECT * FROM cameras WHERE id = ?",
            (camera_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Khong tim thay camera!"
            )

        if camera.status is not None:
            if camera.status not in ("online", "offline"):
                raise HTTPException(
                    status_code=400,
                    detail="Trang thai phai la online hoac offline!"
                )

        camera_name = (
            camera.camera_name.strip()
            if camera.camera_name is not None
            else existing["camera_name"]
        )

        location = (
            camera.location
            if camera.location is not None
            else existing["location"]
        )

        status = (
            camera.status
            if camera.status is not None
            else existing["status"]
        )

        connection.execute("""
            UPDATE cameras
            SET camera_name = ?, location = ?, status = ?
            WHERE id = ?
        """, (camera_name, location, status, camera_id))

        connection.commit()

        return {
            "status": "success",
            "message": "Cap nhat camera thanh cong!"
        }

    except HTTPException:
        raise

    except sqlite3.Error as error:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        connection.close()


@router.delete("/{camera_id}")
def delete_camera(camera_id: int):
    connection = get_db_connection()

    try:
        existing = connection.execute(
            "SELECT id FROM cameras WHERE id = ?",
            (camera_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Khong tim thay camera!"
            )

        connection.execute(
            "DELETE FROM cameras WHERE id = ?",
            (camera_id,)
        )

        connection.commit()

        return {
            "status": "success",
            "message": "Xoa camera thanh cong!"
        }

    except HTTPException:
        raise

    except sqlite3.Error as error:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        connection.close()
