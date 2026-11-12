
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.face_registration_service import register_member


router = APIRouter(
    prefix="/api/members",
    tags=["Family Members"]
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = (
    PROJECT_ROOT / "storage" / "database" / "smart_home.db"
)


class MemberCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)


class MemberUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)


class MemberStatusUpdate(BaseModel):
    is_active: bool


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@router.get("/")
def get_family_members():
    """Lay danh sach thanh vien gia dinh."""

    connection = None

    try:
        connection = get_connection()

        members = connection.execute("""
            SELECT
                id,
                full_name,
                created_at,
                is_active
            FROM family_members
            ORDER BY id ASC
        """).fetchall()

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


@router.get("/{member_id}")
def get_family_member(member_id: int):
    """Lay thong tin chi tiet thanh vien."""

    connection = None

    try:
        connection = get_connection()

        member = connection.execute("""
            SELECT
                id,
                full_name,
                face_file,
                created_at,
                is_active
            FROM family_members
            WHERE id = ?
        """, (member_id,)).fetchone()

        if member is None:
            raise HTTPException(
                status_code=404,
                detail="Khong tim thay thanh vien!"
            )

        return {
            "status": "success",
            "member": dict(member)
        }

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    finally:
        if connection:
            connection.close()


@router.post("/register", status_code=201)
def create_family_member(member_data: MemberCreate):
    """Dang ky thanh vien moi bang nhan dien khuon mat."""

    full_name = member_data.full_name.strip()

    if not full_name:
        raise HTTPException(
            status_code=400,
            detail="Ten thanh vien khong duoc de trong!"
        )

    try:
        member = register_member(full_name)

        return {
            "status": "success",
            "message": "Dang ky thanh vien thanh cong!",
            "member": member
        }

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ten thanh vien da ton tai!"
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Loi dang ky thanh vien: {error}"
        )


@router.put("/{member_id}")
def update_family_member(
    member_id: int,
    member_data: MemberUpdate
):
    """Cap nhat ten thanh vien."""

    full_name = member_data.full_name.strip()

    if not full_name:
        raise HTTPException(
            status_code=400,
            detail="Ten thanh vien khong duoc de trong!"
        )

    connection = None

    try:
        connection = get_connection()

        cursor = connection.execute("""
            UPDATE family_members
            SET full_name = ?
            WHERE id = ?
        """, (full_name, member_id))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Khong tim thay thanh vien!"
            )

        connection.commit()

        member = connection.execute("""
            SELECT id, full_name, created_at, is_active
            FROM family_members
            WHERE id = ?
        """, (member_id,)).fetchone()

        return {
            "status": "success",
            "message": "Cap nhat thanh vien thanh cong!",
            "member": dict(member)
        }

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ten thanh vien da ton tai!"
        )

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    finally:
        if connection:
            connection.close()


@router.patch("/{member_id}/status")
def update_member_status(
    member_id: int,
    status_data: MemberStatusUpdate
):
    """Kich hoat hoac vo hieu hoa thanh vien."""

    connection = None

    try:
        connection = get_connection()

        cursor = connection.execute("""
            UPDATE family_members
            SET is_active = ?
            WHERE id = ?
        """, (
            1 if status_data.is_active else 0,
            member_id
        ))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Khong tim thay thanh vien!"
            )

        connection.commit()

        member = connection.execute("""
            SELECT id, full_name, created_at, is_active
            FROM family_members
            WHERE id = ?
        """, (member_id,)).fetchone()

        return {
            "status": "success",
            "message": "Cap nhat trang thai thanh vien thanh cong!",
            "member": dict(member)
        }

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    finally:
        if connection:
            connection.close()
