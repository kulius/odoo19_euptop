#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migrate HR test data from Odoo 17 to Odoo 19
"""
import psycopg2
import json
from datetime import datetime, date
from decimal import Decimal

# Database connections
ODOO17_DB = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'odoo',
    'password': 'odoo',
    'database': 'odoo17_yc_hrtest'
}

ODOO19_DB = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'odoo',
    'password': 'odoo',
    'database': 'odoo19_sanoc'
}


def get_connection(db_config):
    conn = psycopg2.connect(**db_config)
    conn.set_client_encoding('UTF8')
    return conn


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def export_table_data(cur, table_name, columns=None, where_clause=None):
    """Export data from a table"""
    if columns:
        cols = ', '.join(columns)
    else:
        # Get all columns
        cur.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        cols = ', '.join([r[0] for r in cur.fetchall()])

    sql = f"SELECT {cols} FROM {table_name}"
    if where_clause:
        sql += f" WHERE {where_clause}"

    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    return columns, rows


def print_table_structure(cur, table_name):
    """Print table structure"""
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))

    print(f"\n{'='*60}")
    print(f"Table: {table_name}")
    print(f"{'='*60}")
    print(f"{'Column':<30} {'Type':<20} {'Nullable':<10}")
    print(f"{'-'*60}")
    for row in cur.fetchall():
        print(f"{row[0]:<30} {row[1]:<20} {row[2]:<10}")


def export_employees():
    """Export employee data"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出員工資料")
    print("="*60)

    # Get employee data
    cur.execute("""
        SELECT id, name, work_email, work_phone, mobile_phone,
               department_id, job_title, parent_id, coach_id,
               company_id, active, gender, birthday, identification_id,
               marital, address_home_id
        FROM hr_employee
        WHERE active = true OR active = false
        ORDER BY id
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆員工資料:")
    for row in rows:
        emp_dict = dict(zip(columns, row))
        print(f"  ID: {emp_dict['id']}, Name: {emp_dict['name']}, Dept: {emp_dict['department_id']}")

    cur.close()
    conn.close()

    return columns, rows


def export_departments():
    """Export department data"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出部門資料")
    print("="*60)

    cur.execute("""
        SELECT id, name, complete_name, parent_id, manager_id,
               company_id, active
        FROM hr_department
        ORDER BY id
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆部門資料:")
    for row in rows:
        dept_dict = dict(zip(columns, row))
        print(f"  ID: {dept_dict['id']}, Name: {dept_dict['name']}")

    cur.close()
    conn.close()

    return columns, rows


def export_holiday_types():
    """Export holiday types"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出假別類型")
    print("="*60)

    cur.execute("""
        SELECT id, name, code, unit, status, male, female,
               is_default, create_uid, write_uid
        FROM starrylord_holiday_type
        ORDER BY id
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆假別:")
    for row in rows:
        ht_dict = dict(zip(columns, row))
        print(f"  ID: {ht_dict['id']}, Code: {ht_dict['code']}, Name: {ht_dict['name']}")

    cur.close()
    conn.close()

    return columns, rows


def export_overtime_types():
    """Export overtime types"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出加班類型")
    print("="*60)

    cur.execute("""
        SELECT id, name, code, active, create_uid, write_uid
        FROM starrylord_overtime_type
        ORDER BY id
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆加班類型:")
    for row in rows:
        ot_dict = dict(zip(columns, row))
        print(f"  ID: {ot_dict['id']}, Code: {ot_dict['code']}, Name: {ot_dict['name']}")

    cur.close()
    conn.close()

    return columns, rows


def export_overtime_type_rules():
    """Export overtime type rules"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出加班類型規則")
    print("="*60)

    cur.execute("""
        SELECT id, overtime_type_id, sequence, start_hour, end_hour, multiplier
        FROM starrylord_overtime_type_rule
        ORDER BY overtime_type_id, sequence
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆加班規則:")
    for row in rows:
        rule_dict = dict(zip(columns, row))
        print(f"  Type: {rule_dict['overtime_type_id']}, Seq: {rule_dict['sequence']}, "
              f"Hours: {rule_dict['start_hour']}-{rule_dict['end_hour']}, "
              f"Multiplier: {rule_dict['multiplier']}")

    cur.close()
    conn.close()

    return columns, rows


def export_schedules():
    """Export schedule data"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出排班資料")
    print("="*60)

    # Schedule
    cur.execute("""
        SELECT id, name, active, create_uid, write_uid
        FROM hr_schedule
        ORDER BY id
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆排班:")
    for row in rows:
        s_dict = dict(zip(columns, row))
        print(f"  ID: {s_dict['id']}, Name: {s_dict['name']}")

    schedule_data = (columns, rows)

    # Schedule worktime
    cur.execute("""
        SELECT id, schedule_id, day_of_week, am_start, am_end, pm_start, pm_end,
               hours, name
        FROM hr_schedule_worktime
        ORDER BY schedule_id, day_of_week
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆排班時段:")
    for row in rows:
        sw_dict = dict(zip(columns, row))
        print(f"  Schedule: {sw_dict['schedule_id']}, Day: {sw_dict['day_of_week']}, "
              f"AM: {sw_dict['am_start']}-{sw_dict['am_end']}, "
              f"PM: {sw_dict['pm_start']}-{sw_dict['pm_end']}")

    worktime_data = (columns, rows)

    cur.close()
    conn.close()

    return schedule_data, worktime_data


def export_public_holidays():
    """Export public holidays"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出國定假日")
    print("="*60)

    cur.execute("""
        SELECT id, name, date, create_uid, write_uid
        FROM hr_public_holiday
        ORDER BY date
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆國定假日:")
    for row in rows:
        ph_dict = dict(zip(columns, row))
        print(f"  Date: {ph_dict['date']}, Name: {ph_dict['name']}")

    cur.close()
    conn.close()

    return columns, rows


def export_annual_leave_settings():
    """Export annual leave settings"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出特休設定")
    print("="*60)

    cur.execute("""
        SELECT id, year, days, hours, create_uid, write_uid
        FROM starrylord_annual_leave_setting
        ORDER BY year
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆特休設定:")
    for row in rows:
        al_dict = dict(zip(columns, row))
        print(f"  Year: {al_dict['year']}, Days: {al_dict['days']}, Hours: {al_dict['hours']}")

    cur.close()
    conn.close()

    return columns, rows


def export_hour_min_lists():
    """Export hour and minute lists"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出時/分列表")
    print("="*60)

    # Hour list
    cur.execute("""
        SELECT id, name, hour
        FROM starrylord_holiday_hour_list
        ORDER BY hour
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆小時選項:")
    for row in rows:
        h_dict = dict(zip(columns, row))
        print(f"  Hour: {h_dict['hour']}, Name: {h_dict['name']}")

    hour_data = (columns, rows)

    # Minute list
    cur.execute("""
        SELECT id, name, minute
        FROM starrylord_holiday_min_list
        ORDER BY minute
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆分鐘選項:")
    for row in rows:
        m_dict = dict(zip(columns, row))
        print(f"  Minute: {m_dict['minute']}, Name: {m_dict['name']}")

    min_data = (columns, rows)

    cur.close()
    conn.close()

    return hour_data, min_data


def export_holiday_allocations():
    """Export holiday allocations"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出假期配額")
    print("="*60)

    cur.execute("""
        SELECT id, employee_id, holiday_type_id, year, hours,
               used_hours, remaining_hours, effective_date, expiration_date
        FROM starrylord_holiday_allocation
        ORDER BY employee_id, holiday_type_id, year
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆假期配額:")
    for row in rows[:10]:  # Show first 10
        alloc_dict = dict(zip(columns, row))
        print(f"  Employee: {alloc_dict['employee_id']}, Type: {alloc_dict['holiday_type_id']}, "
              f"Year: {alloc_dict['year']}, Hours: {alloc_dict['hours']}")
    if len(rows) > 10:
        print(f"  ... 還有 {len(rows) - 10} 筆")

    cur.close()
    conn.close()

    return columns, rows


def export_holiday_applies():
    """Export holiday applies"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出請假單")
    print("="*60)

    cur.execute("""
        SELECT id, name, employee_id, department_id, holiday_type_id,
               start_date, end_date, hours, state, reason,
               create_uid, write_uid, create_date, write_date
        FROM starrylord_holiday_apply
        ORDER BY create_date DESC
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆請假單:")
    for row in rows[:10]:
        apply_dict = dict(zip(columns, row))
        print(f"  ID: {apply_dict['id']}, Employee: {apply_dict['employee_id']}, "
              f"Type: {apply_dict['holiday_type_id']}, State: {apply_dict['state']}")
    if len(rows) > 10:
        print(f"  ... 還有 {len(rows) - 10} 筆")

    cur.close()
    conn.close()

    return columns, rows


def export_overtime_applies():
    """Export overtime applies"""
    conn = get_connection(ODOO17_DB)
    cur = conn.cursor()

    print("\n" + "="*60)
    print("匯出加班單")
    print("="*60)

    cur.execute("""
        SELECT id, name, employee_id, department_id, overtime_type_id,
               start_date, end_date, hours, state, reason,
               create_uid, write_uid, create_date, write_date
        FROM starrylord_overtime_apply
        ORDER BY create_date DESC
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    print(f"\n找到 {len(rows)} 筆加班單:")
    for row in rows[:10]:
        apply_dict = dict(zip(columns, row))
        print(f"  ID: {apply_dict['id']}, Employee: {apply_dict['employee_id']}, "
              f"Type: {apply_dict['overtime_type_id']}, State: {apply_dict['state']}")
    if len(rows) > 10:
        print(f"  ... 還有 {len(rows) - 10} 筆")

    cur.close()
    conn.close()

    return columns, rows


def main():
    print("="*60)
    print("Odoo 17 → Odoo 19 HR 資料遷移")
    print("="*60)

    # Export all data
    dept_data = export_departments()
    emp_data = export_employees()
    schedule_data, worktime_data = export_schedules()
    holiday_type_data = export_holiday_types()
    overtime_type_data = export_overtime_types()
    overtime_rule_data = export_overtime_type_rules()
    public_holiday_data = export_public_holidays()
    annual_leave_data = export_annual_leave_settings()
    hour_data, min_data = export_hour_min_lists()
    allocation_data = export_holiday_allocations()
    holiday_apply_data = export_holiday_applies()
    overtime_apply_data = export_overtime_applies()

    print("\n" + "="*60)
    print("資料匯出完成！")
    print("="*60)


if __name__ == '__main__':
    main()
