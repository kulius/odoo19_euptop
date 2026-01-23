#!/usr/bin/env python3
"""
Fix employees without hr_version records.
This creates version records for employees that don't have one,
which is required for them to appear in hr.employee.public view.
"""
import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    user='odoo',
    password='odoo',
    database='odoo19_sanoc'
)
conn.autocommit = True
cur = conn.cursor()

# First, find NOT NULL columns without defaults
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'hr_version'
    AND is_nullable = 'NO'
    AND column_default IS NULL
    ORDER BY ordinal_position
""")
print('NOT NULL columns without defaults in hr_version:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Find employees without current_version_id
cur.execute('''
    SELECT id, name, company_id
    FROM hr_employee
    WHERE current_version_id IS NULL
''')
employees_to_fix = cur.fetchall()

print(f'\nFound {len(employees_to_fix)} employees without version records.')

now = datetime.now()

for emp in employees_to_fix:
    emp_id, name, company_id = emp
    print(f'Creating version for employee {emp_id}: {name}')

    # Insert hr_version record with all NOT NULL fields
    cur.execute('''
        INSERT INTO hr_version (
            employee_id, company_id, active,
            last_modified_uid, hr_responsible_id,
            distance_home_work_unit, marital, employee_type,
            date_version, last_modified_date,
            create_date, write_date, create_uid, write_uid
        ) VALUES (
            %s, %s, true,
            1, 1,
            'km', 'single', 'employee',
            %s, %s,
            %s, %s, 1, 1
        )
        RETURNING id
    ''', (emp_id, company_id, now.date(), now, now, now))

    version_id = cur.fetchone()[0]
    print(f'  Created hr_version ID: {version_id}')

    # Update employee's current_version_id
    cur.execute('''
        UPDATE hr_employee SET current_version_id = %s WHERE id = %s
    ''', (version_id, emp_id))
    print(f'  Updated employee {emp_id} current_version_id to {version_id}')

print('\n\nVerification:')

# Verify the fix
cur.execute('SELECT COUNT(*) FROM hr_employee WHERE current_version_id IS NULL')
result = cur.fetchone()
print(f'Employees still without current_version_id: {result[0]}')

# Check hr_employee_public now
cur.execute('SELECT id, name FROM hr_employee_public ORDER BY id LIMIT 15')
print('\nhr_employee_public records after fix:')
for row in cur.fetchall():
    print(f'  ID: {row[0]}, Name: {row[1]}')

cur.close()
conn.close()
print('\nDone!')
