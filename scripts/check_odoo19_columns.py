#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check table columns in Odoo 19 database"""
import psycopg2

ODOO19_DB = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'odoo',
    'password': 'odoo',
    'database': 'odoo19_sanoc'
}

def check_columns(table_name):
    conn = psycopg2.connect(**ODOO19_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    result = cur.fetchall()
    print(f"\n=== {table_name} ({len(result)} columns) ===")
    for row in result:
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
    'starrylord_holiday_allocation',
    'hr_schedule',
    'hr_schedule_worktime',
    'hr_public_holiday',
    'starrylord_annual_leave_setting',
    'starrylord_holiday_hour_list',
    'starrylord_holiday_min_list',
]

for t in tables:
    try:
        check_columns(t)
    except Exception as e:
        print(f"\n=== {t} === ERROR: {e}")
