
import json
import os
import sqlite3
import uuid
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

FACE_DIR = PROJECT_ROOT / "storage" / "faces"


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

    except HTTPException:
        raise

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
    """Cap nhat ten thanh vien va dong bo file khuon mat."""

    full_name = member_data.full_name.strip()

    if not full_name:
        raise HTTPException(
            status_code=400,
            detail="Ten thanh vien khong duoc de trong!"
        )

    connection = None
    face_path = None
    temp_path = None
    original_content = None
    json_updated = False
    transaction_started = False
    committed = False

    try:
        connection = get_connection()

        connection.execute("BEGIN IMMEDIATE")
        transaction_started = True

        # Lay thong tin thanh vien hien tai
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

        old_name = member["full_name"]
        face_file = member["face_file"]

        # Kiem tra ten moi co bi trung hay khong
        duplicate = connection.execute("""
            SELECT id
            FROM family_members
            WHERE full_name = ?
              AND id != ?
        """, (full_name, member_id)).fetchone()

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Ten thanh vien da ton tai!"
            )

        # Neu ten khong thay doi thi khong can cap nhat
        if old_name == full_name:
            connection.rollback()
            transaction_started = False

            return {
                "status": "success",
                "message": "Ten thanh vien khong thay doi!",
                "member": dict(member)
            }

        if not face_file:
            raise HTTPException(
                status_code=409,
                detail="Thanh vien chua co file khuon mat!"
            )

        # Xac dinh file khuon mat tu Database
        face_path = FACE_DIR / face_file

        if face_path.parent.resolve() != FACE_DIR.resolve():
            raise HTTPException(
                status_code=400,
                detail="Duong dan file khuon mat khong hop le!"
            )

        if not face_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Khong tim thay file khuon mat!"
            )

        # Doc file JSON hien tai
        with open(
            face_path,
            "r",
            encoding="utf-8"
        ) as file:
            face_data = json.load(file)

        # Dam bao JSON va Database dang dong bo
        if face_data.get("name") != old_name:
            raise HTTPException(
                status_code=409,
                detail="Ten trong file khuon mat khong khop Database!"
            )

        # Chi thay doi ten, giu nguyen embeddings
        face_data["name"] = full_name

        # Sao luu noi dung JSON goc trong bo nho
        with open(face_path, "rb") as file:
            original_content = file.read()

        # Tao file tam de ghi du lieu moi
        temp_path = face_path.with_name(
            f".{face_path.name}.{uuid.uuid4().hex}.tmp"
        )

        with open(
            temp_path,
            "x",
            encoding="utf-8"
        ) as file:
            json.dump(
                face_data,
                file,
                ensure_ascii=False,
                indent=4
            )

            file.flush()
            os.fsync(file.fileno())

        # Thay the file JSON bang file tam
        os.replace(temp_path, face_path)
        json_updated = True

        # Cap nhat ten trong Database
        connection.execute("""
            UPDATE family_members
            SET full_name = ?
            WHERE id = ?
        """, (full_name, member_id))

        # Doc lai thong tin truoc khi commit
        updated_member = connection.execute("""
            SELECT
                id,
                full_name,
                face_file,
                created_at,
                is_active
            FROM family_members
            WHERE id = ?
        """, (member_id,)).fetchone()

        # Hoan tat transaction
        connection.commit()
        transaction_started = False
        committed = True

        return {
            "status": "success",
            "message": "Cap nhat thanh vien va file khuon mat thanh cong!",
            "member": dict(updated_member)
        }

    except HTTPException:
        if transaction_started and connection:
            connection.rollback()

        if json_updated and not committed and original_content is not None:
            face_path.write_bytes(original_content)

        raise

    except sqlite3.IntegrityError:
        if transaction_started and connection:
            connection.rollback()

        if json_updated and not committed and original_content is not None:
            face_path.write_bytes(original_content)

        raise HTTPException(
            status_code=409,
            detail="Ten thanh vien da ton tai!"
        )

    except (sqlite3.Error, OSError, ValueError, TypeError) as error:
        if transaction_started and connection:
            connection.rollback()

        if json_updated and not committed and original_content is not None:
            face_path.write_bytes(original_content)

        raise HTTPException(
            status_code=500,
            detail=f"Loi cap nhat thanh vien: {error}"
        )

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()

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
            SELECT
                id,
                full_name,
                created_at,
                is_active
            FROM family_members
            WHERE id = ?
        """, (member_id,)).fetchone()

        return {
            "status": "success",
            "message": "Cap nhat trang thai thanh vien thanh cong!",
            "member": dict(member)
        }

    except HTTPException:
        raise

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}"
        )

    finally:
        if connection:
            connection.close()
