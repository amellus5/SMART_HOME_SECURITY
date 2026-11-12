
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "storage" / "database" / "smart_home.db"

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

cursor.execute("""
    SELECT id, full_name, face_file, is_active, created_at
    FROM family_members
""")

members = cursor.fetchall()

print("=== DANH SACH THANH VIEN GIA DINH ===")

for member in members:
    print("ID:", member[0])
    print("Ho ten:", member[1])
    print("File khuon mat:", member[2])
    print("Trang thai:", "Hoat dong" if member[3] else "Da vo hieu hoa")
    print("Ngay tao:", member[4])
    print("------------------------------")

print("Tong so thanh vien:", len(members))

connection.close()
