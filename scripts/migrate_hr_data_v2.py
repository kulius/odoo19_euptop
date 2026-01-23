#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migrate HR test data from Odoo 17 to Odoo 19
Version 2 - Based on actual table structure
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


def get_or_create_company(cur19):
    """Get default company ID from Odoo 19"""
    cur19.execute("SELECT id FROM res_company ORDER BY id LIMIT 1")
    result = cur19.fetchone()
    return result[0] if result else 1


def migrate_departments(conn17, conn19):
    """Migrate departments"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移部門資料")
    print("="*60)

    # Get source data
    cur17.execute("""
        SELECT id, name, complete_name, parent_id, manager_id, active
        FROM hr_department
        ORDER BY id
    """)
    depts = cur17.fetchall()

    company_id = get_or_create_company(cur19)

    # Check if departments exist
    cur19.execute("SELECT id, name FROM hr_department")
    existing = {row[0]: row[1] for row in cur19.fetchall()}

    id_mapping = {}
    for dept in depts:
        old_id, name_json, complete_name, parent_id, manager_id, active = dept

        # Handle jsonb name
        if isinstance(name_json, dict):
            name = name_json.get('zh_TW') or name_json.get('en_US') or str(name_json)
        else:
            name = str(name_json) if name_json else f'Department {old_id}'

        print(f"  處理部門: {name} (原ID: {old_id})")

        # Check if exists by name
        cur19.execute("SELECT id FROM hr_department WHERE name = %s", (name,))
        existing_row = cur19.fetchone()

        if existing_row:
            id_mapping[old_id] = existing_row[0]
            print(f"    -> 已存在 (新ID: {existing_row[0]})")
        else:
            cur19.execute("""
                INSERT INTO hr_department (name, complete_name, company_id, active, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, 1, 1, NOW(), NOW())
                RETURNING id
            """, (name, complete_name or name, company_id, active if active is not None else True))
            new_id = cur19.fetchone()[0]
            id_mapping[old_id] = new_id
            print(f"    -> 新建 (新ID: {new_id})")

    conn19.commit()
    print(f"\n部門遷移完成: {len(id_mapping)} 筆")
    return id_mapping


def migrate_employees(conn17, conn19, dept_mapping):
    """Migrate employees"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移員工資料")
    print("="*60)

    company_id = get_or_create_company(cur19)

    # Get source data
    cur17.execute("""
        SELECT id, name, employee_number, work_email, work_phone, mobile_phone,
               department_id, job_title, parent_id, gender, birthday,
               identification_id, marital, active, schedule_id
        FROM hr_employee
        ORDER BY id
    """)
    employees = cur17.fetchall()

    id_mapping = {}
    for emp in employees:
        (old_id, name, emp_number, work_email, work_phone, mobile_phone,
         department_id, job_title, parent_id, gender, birthday,
         identification_id, marital, active, schedule_id) = emp

        print(f"  處理員工: {name} ({emp_number or 'N/A'}) (原ID: {old_id})")

        # Map department
        new_dept_id = dept_mapping.get(department_id) if department_id else None

        # Check if exists by name or employee_number
        cur19.execute("""
            SELECT id FROM hr_employee WHERE name = %s OR employee_number = %s
        """, (name, emp_number))
        existing_row = cur19.fetchone()

        if existing_row:
            id_mapping[old_id] = existing_row[0]
            # Update existing
            cur19.execute("""
                UPDATE hr_employee SET
                    employee_number = COALESCE(%s, employee_number),
                    work_email = COALESCE(%s, work_email),
                    work_phone = COALESCE(%s, work_phone),
                    mobile_phone = COALESCE(%s, mobile_phone),
                    department_id = COALESCE(%s, department_id),
                    job_title = COALESCE(%s, job_title),
                    gender = COALESCE(%s, gender),
                    birthday = COALESCE(%s, birthday),
                    identification_id = COALESCE(%s, identification_id),
                    marital = COALESCE(%s, marital),
                    write_date = NOW()
                WHERE id = %s
            """, (emp_number, work_email, work_phone, mobile_phone,
                  new_dept_id, job_title, gender, birthday,
                  identification_id, marital, existing_row[0]))
            print(f"    -> 更新 (ID: {existing_row[0]})")
        else:
            # Need to create resource first
            cur19.execute("""
                INSERT INTO resource_resource (name, company_id, resource_type, active, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 'user', %s, 1, 1, NOW(), NOW())
                RETURNING id
            """, (name, company_id, active if active is not None else True))
            resource_id = cur19.fetchone()[0]

            cur19.execute("""
                INSERT INTO hr_employee (
                    name, employee_number, resource_id, company_id,
                    work_email, work_phone, mobile_phone, department_id,
                    job_title, gender, birthday, identification_id, marital,
                    active, create_uid, write_uid, create_date, write_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, NOW(), NOW())
                RETURNING id
            """, (name, emp_number, resource_id, company_id,
                  work_email, work_phone, mobile_phone, new_dept_id,
                  job_title, gender, birthday, identification_id, marital,
                  active if active is not None else True))
            new_id = cur19.fetchone()[0]
            id_mapping[old_id] = new_id
            print(f"    -> 新建 (ID: {new_id})")

    conn19.commit()
    print(f"\n員工遷移完成: {len(id_mapping)} 筆")
    return id_mapping


def migrate_holiday_types(conn17, conn19):
    """Migrate holiday types"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移假別類型")
    print("="*60)

    cur17.execute("""
        SELECT id, name, request_unit, salary_calculation, note, is_distribute
        FROM starrylord_holiday_type
        ORDER BY id
    """)
    types = cur17.fetchall()

    id_mapping = {}
    for ht in types:
        old_id, name, request_unit, salary_calculation, note, is_distribute = ht
        print(f"  處理假別: {name} (原ID: {old_id})")

        # Check if exists
        cur19.execute("SELECT id FROM starrylord_holiday_type WHERE name = %s", (name,))
        existing = cur19.fetchone()

        if existing:
            id_mapping[old_id] = existing[0]
            print(f"    -> 已存在 (ID: {existing[0]})")
        else:
            cur19.execute("""
                INSERT INTO starrylord_holiday_type (name, request_unit, salary_calculation, note, is_distribute, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, %s, 1, 1, NOW(), NOW())
                RETURNING id
            """, (name, request_unit, salary_calculation, note, is_distribute))
            new_id = cur19.fetchone()[0]
            id_mapping[old_id] = new_id
            print(f"    -> 新建 (ID: {new_id})")

    conn19.commit()
    print(f"\n假別類型遷移完成: {len(id_mapping)} 筆")
    return id_mapping


def migrate_overtime_types(conn17, conn19):
    """Migrate overtime types and rules"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移加班類型")
    print("="*60)

    cur17.execute("""
        SELECT id, name, time_type, date_type, eight_hours
        FROM starrylord_overtime_type
        ORDER BY id
    """)
    types = cur17.fetchall()

    id_mapping = {}
    for ot in types:
        old_id, name, time_type, date_type, eight_hours = ot
        print(f"  處理加班類型: {name} (原ID: {old_id})")

        cur19.execute("SELECT id FROM starrylord_overtime_type WHERE name = %s", (name,))
        existing = cur19.fetchone()

        if existing:
            id_mapping[old_id] = existing[0]
            print(f"    -> 已存在 (ID: {existing[0]})")
        else:
            cur19.execute("""
                INSERT INTO starrylord_overtime_type (name, time_type, date_type, eight_hours, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, 1, 1, NOW(), NOW())
                RETURNING id
            """, (name, time_type, date_type, eight_hours))
            new_id = cur19.fetchone()[0]
            id_mapping[old_id] = new_id
            print(f"    -> 新建 (ID: {new_id})")

    conn19.commit()

    # Migrate rules
    print("\n遷移加班規則...")
    cur17.execute("""
        SELECT id, rule_id, name, time, rate
        FROM starrylord_overtime_type_rule
        ORDER BY rule_id, time
    """)
    rules = cur17.fetchall()

    for rule in rules:
        old_id, rule_id, name, time_val, rate = rule
        new_rule_id = id_mapping.get(rule_id)

        if new_rule_id:
            cur19.execute("SELECT id FROM starrylord_overtime_type_rule WHERE rule_id = %s AND time = %s", (new_rule_id, time_val))
            if not cur19.fetchone():
                cur19.execute("""
                    INSERT INTO starrylord_overtime_type_rule (rule_id, name, time, rate, create_uid, write_uid, create_date, write_date)
                    VALUES (%s, %s, %s, %s, 1, 1, NOW(), NOW())
                """, (new_rule_id, name, time_val, rate))
                print(f"    規則: Type {new_rule_id}, Time {time_val}, Rate {rate}")

    conn19.commit()
    print(f"\n加班類型遷移完成: {len(id_mapping)} 筆")
    return id_mapping


def migrate_schedules(conn17, conn19):
    """Migrate schedules"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移排班資料")
    print("="*60)

    cur17.execute("""
        SELECT id, name, is_user_personal_calendar, is_control_personal_calendar
        FROM hr_schedule
        ORDER BY id
    """)
    schedules = cur17.fetchall()

    id_mapping = {}
    for sch in schedules:
        old_id, name, is_user_pc, is_control_pc = sch
        print(f"  處理排班: {name} (原ID: {old_id})")

        cur19.execute("SELECT id FROM hr_schedule WHERE name = %s", (name,))
        existing = cur19.fetchone()

        if existing:
            id_mapping[old_id] = existing[0]
            print(f"    -> 已存在 (ID: {existing[0]})")
        else:
            cur19.execute("""
                INSERT INTO hr_schedule (name, is_user_personal_calendar, is_control_personal_calendar, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, 1, 1, NOW(), NOW())
                RETURNING id
            """, (name, is_user_pc, is_control_pc))
            new_id = cur19.fetchone()[0]
            id_mapping[old_id] = new_id
            print(f"    -> 新建 (ID: {new_id})")

    conn19.commit()

    # Migrate worktime
    print("\n遷移排班時段...")
    cur17.execute("""
        SELECT worktime_id, name, dayofweek, date_type, type,
               work_start, work_end, am_start, am_end, pm_start, pm_end, sequence
        FROM hr_schedule_worktime
        ORDER BY worktime_id, sequence
    """)
    worktimes = cur17.fetchall()

    for wt in worktimes:
        (worktime_id, name, dayofweek, date_type, wtype,
         work_start, work_end, am_start, am_end, pm_start, pm_end, sequence) = wt
        new_worktime_id = id_mapping.get(worktime_id)

        if new_worktime_id:
            cur19.execute("""
                SELECT id FROM hr_schedule_worktime
                WHERE worktime_id = %s AND dayofweek = %s
            """, (new_worktime_id, dayofweek))
            if not cur19.fetchone():
                cur19.execute("""
                    INSERT INTO hr_schedule_worktime (
                        worktime_id, name, dayofweek, date_type, type,
                        work_start, work_end, am_start, am_end, pm_start, pm_end, sequence,
                        create_uid, write_uid, create_date, write_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, NOW(), NOW())
                """, (new_worktime_id, name, dayofweek, date_type, wtype,
                      work_start, work_end, am_start, am_end, pm_start, pm_end, sequence))
                print(f"    時段: {name} ({dayofweek})")

    conn19.commit()
    print(f"\n排班遷移完成: {len(id_mapping)} 筆")
    return id_mapping


def migrate_public_holidays(conn17, conn19):
    """Migrate public holidays"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移國定假日")
    print("="*60)

    cur17.execute("""
        SELECT id, name, date
        FROM hr_public_holiday
        ORDER BY date
    """)
    holidays = cur17.fetchall()

    count = 0
    for ph in holidays:
        old_id, name, holiday_date = ph
        print(f"  處理假日: {holiday_date} - {name}")

        cur19.execute("SELECT id FROM hr_public_holiday WHERE date = %s", (holiday_date,))
        if not cur19.fetchone():
            cur19.execute("""
                INSERT INTO hr_public_holiday (name, date, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 1, 1, NOW(), NOW())
            """, (name, holiday_date))
            count += 1

    conn19.commit()
    print(f"\n國定假日遷移完成: {count} 筆新增")


def migrate_annual_leave_settings(conn17, conn19):
    """Migrate annual leave settings"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移特休設定")
    print("="*60)

    cur17.execute("""
        SELECT id, year, duration_time, duration_date
        FROM starrylord_annual_leave_setting
        ORDER BY year
    """)
    settings = cur17.fetchall()

    count = 0
    for s in settings:
        old_id, year, duration_time, duration_date = s
        print(f"  處理特休: 年資 {year}, 時數 {duration_time}, 天數 {duration_date}")

        cur19.execute("SELECT id FROM starrylord_annual_leave_setting WHERE year = %s", (year,))
        if not cur19.fetchone():
            cur19.execute("""
                INSERT INTO starrylord_annual_leave_setting (year, duration_time, duration_date, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, 1, 1, NOW(), NOW())
            """, (year, duration_time, duration_date))
            count += 1

    conn19.commit()
    print(f"\n特休設定遷移完成: {count} 筆新增")


def migrate_holiday_allocations(conn17, conn19, emp_mapping, type_mapping):
    """Migrate holiday allocations"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移假期配額")
    print("="*60)

    cur17.execute("""
        SELECT id, employee_id, holiday_type_id, year, time_type,
               distribute_time, duration_time, duration_date, duration_min,
               validity_start, validity_end, note
        FROM starrylord_holiday_allocation
        ORDER BY employee_id, holiday_type_id, year
    """)
    allocations = cur17.fetchall()

    count = 0
    for alloc in allocations:
        (old_id, emp_id, type_id, year, time_type, distribute_time,
         duration_time, duration_date, duration_min, validity_start, validity_end, note) = alloc

        new_emp_id = emp_mapping.get(emp_id)
        new_type_id = type_mapping.get(type_id)

        if new_emp_id and new_type_id:
            cur19.execute("""
                SELECT id FROM starrylord_holiday_allocation
                WHERE employee_id = %s AND holiday_type_id = %s AND year = %s
            """, (new_emp_id, new_type_id, year))

            if not cur19.fetchone():
                cur19.execute("""
                    INSERT INTO starrylord_holiday_allocation (
                        employee_id, holiday_type_id, year, time_type,
                        distribute_time, duration_time, duration_date, duration_min,
                        validity_start, validity_end, note,
                        create_uid, write_uid, create_date, write_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, NOW(), NOW())
                """, (new_emp_id, new_type_id, year, time_type,
                      distribute_time, duration_time, duration_date, duration_min,
                      validity_start, validity_end, note))
                count += 1
                print(f"  配額: Emp {new_emp_id}, Type {new_type_id}, Year {year}")

    conn19.commit()
    print(f"\n假期配額遷移完成: {count} 筆新增")


def migrate_hour_min_lists(conn17, conn19):
    """Migrate hour and minute lists"""
    cur17 = conn17.cursor()
    cur19 = conn19.cursor()

    print("\n" + "="*60)
    print("遷移時/分列表")
    print("="*60)

    # Hour list
    cur17.execute("SELECT id, name, hour FROM starrylord_holiday_hour_list ORDER BY hour")
    hours = cur17.fetchall()

    for h in hours:
        old_id, name, hour = h
        cur19.execute("SELECT id FROM starrylord_holiday_hour_list WHERE hour = %s", (hour,))
        if not cur19.fetchone():
            cur19.execute("""
                INSERT INTO starrylord_holiday_hour_list (name, hour, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 1, 1, NOW(), NOW())
            """, (name, hour))
            print(f"  小時: {hour} - {name}")

    # Minute list
    cur17.execute("SELECT id, name, minute FROM starrylord_holiday_min_list ORDER BY minute")
    mins = cur17.fetchall()

    for m in mins:
        old_id, name, minute = m
        cur19.execute("SELECT id FROM starrylord_holiday_min_list WHERE minute = %s", (minute,))
        if not cur19.fetchone():
            cur19.execute("""
                INSERT INTO starrylord_holiday_min_list (name, minute, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 1, 1, NOW(), NOW())
            """, (name, minute))
            print(f"  分鐘: {minute} - {name}")

    conn19.commit()
    print("\n時/分列表遷移完成")


def main():
    print("="*60)
    print("Odoo 17 → Odoo 19 HR 資料遷移")
    print("="*60)

    conn17 = get_connection(ODOO17_DB)
    conn19 = get_connection(ODOO19_DB)
    conn19.autocommit = False

    try:
        # 1. Migrate departments
        dept_mapping = migrate_departments(conn17, conn19)

        # 2. Migrate employees
        emp_mapping = migrate_employees(conn17, conn19, dept_mapping)

        # 3. Migrate schedules
        schedule_mapping = migrate_schedules(conn17, conn19)

        # 4. Migrate holiday types
        holiday_type_mapping = migrate_holiday_types(conn17, conn19)

        # 5. Migrate overtime types
        overtime_type_mapping = migrate_overtime_types(conn17, conn19)

        # 6. Migrate public holidays
        migrate_public_holidays(conn17, conn19)

        # 7. Migrate annual leave settings
        migrate_annual_leave_settings(conn17, conn19)

        # 8. Migrate hour/min lists
        migrate_hour_min_lists(conn17, conn19)

        # 9. Migrate holiday allocations
        migrate_holiday_allocations(conn17, conn19, emp_mapping, holiday_type_mapping)

        print("\n" + "="*60)
        print("資料遷移完成！")
        print("="*60)

        print("\nID 對照表:")
        print(f"  部門: {dept_mapping}")
        print(f"  員工: {emp_mapping}")
        print(f"  排班: {schedule_mapping}")
        print(f"  假別: {holiday_type_mapping}")
        print(f"  加班類型: {overtime_type_mapping}")

    except Exception as e:
        conn19.rollback()
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn17.close()
        conn19.close()


if __name__ == '__main__':
    main()
