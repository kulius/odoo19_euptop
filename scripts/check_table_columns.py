#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check table columns in Odoo 17 database"""
import psycopg2

ODOO17_DB = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'odoo',
    'password': 'odoo',
    'database': 'odoo17_yc_hrtest'
}

def check_columns(table_name):
    conn = psycopg2.connect(**ODOO17_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    print(f"\n=== {table_name} ===")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cur.close()
    conn.close()

# Check key tables
tables = [
    'hr_employee',
    'hr_department',
    'starrylord_holiday_type',
    'starrylord_overtime_type',
    'starrylord_overtime_type_rule',
    'starrylord_holiday_apply',
    'starrylord_overtime_apply',
    'starrylord_holiday_allocation',
    'hr_schedule',
    'hr_schedule_worktime',
]

for t in tables:
    check_columns(t)
