#!/usr/bin/env python
# -*- coding: utf-8 -*-
import psycopg2

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    user='odoo',
    password='odoo',
    database='odoo17_yc_hrtest'
)
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'starrylord_annual_leave_setting'
    ORDER BY ordinal_position
""")

print("=== starrylord_annual_leave_setting columns ===")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.execute("SELECT * FROM starrylord_annual_leave_setting LIMIT 5")
columns = [desc[0] for desc in cur.description]
print("\nColumn names:", columns)

rows = cur.fetchall()
print("\nSample data:")
for row in rows:
    print(dict(zip(columns, row)))

cur.close()
conn.close()
