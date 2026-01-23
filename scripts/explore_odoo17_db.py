#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Explore Odoo 17 HR test database structure
"""
import psycopg2

def main():
    # Connect to Odoo 17 test database
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        user='odoo',
        password='odoo',
        database='odoo17_yc_hrtest'
    )
    conn.set_client_encoding('UTF8')
    cur = conn.cursor()

    # List all tables related to HR/SL modules
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND (table_name LIKE 'hr_%%'
             OR table_name LIKE 'sl_%%'
             OR table_name LIKE 'starrylord_%%')
        ORDER BY table_name
    """)

    tables = cur.fetchall()
    print('=' * 60)
    print('HR/SL 相關資料表:')
    print('=' * 60)
    for t in tables:
        # Get row count
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
            count = cur.fetchone()[0]
            print(f'  {t[0]}: {count} 筆')
        except Exception as e:
            print(f'  {t[0]}: Error - {e}')
            conn.rollback()

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
