import sqlite3

conn = sqlite3.connect('backend/data/monitoring.db')
cursor = conn.cursor()

print("=== programs 테이블 구조 ===")
cursor.execute('PRAGMA table_info(programs)')
for row in cursor.fetchall():
    print(f"  {row[1]}: {row[2]}")

print("\n=== 프로그램 데이터 ===")
cursor.execute('SELECT id, name, shutdown_start, shutdown_end FROM programs')
for row in cursor.fetchall():
    print(f"  ID: {row[0]}, Name: {row[1]}, shutdown_start: {row[2]}, shutdown_end: {row[3]}")

conn.close()
