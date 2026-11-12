
import sqlite3
from pathlib import Path

database_path = (
    Path(__file__).resolve().parent.parent
    / "storage"
    / "database"
    / "smart_home.db"
)

connection = sqlite3.connect(database_path)

cursor = connection.cursor()

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
""")

tables = cursor.fetchall()

print("CAC BANG TRONG DATABASE:")

for table in tables:
    print("-", table[0])

connection.close()
