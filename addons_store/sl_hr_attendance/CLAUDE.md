# Starry Lord HRM Attendance Module

## Module Information
- **Name**: Starry Lord HRM 考勤 (Attendance)
- **Version**: 19.0.0.1
- **License**: LGPL-3
- **Author**: Starry Lord
- **Category**: HRM

## Purpose
Comprehensive attendance management system extending Odoo's standard hr_attendance module. Provides raw attendance data import, attendance repair, anomaly detection, and integration with personal calendars.

## Dependencies
- `base`
- `hr`
- `sl_hrm_personal_calendar` (schedule integration)
- `hr_attendance` (base attendance functionality)

## External Python Dependencies
```python
'external_dependencies': {
    'python': ['pandas', 'openpyxl'],
}
```

## Key Models

### hr.attendance (inherited)
**File**: `models/starrylord_hr_attendance.py`

Extends standard attendance with additional fields and modified behavior.

**Key Changes**:
- `active`: Boolean field for soft delete
- `employee_number`: Related field from employee
- `employee_department_id`: Related department field
- `_check_validity()`: Overridden to always return True (removes overlap check)
- `_compute_attendance_state()`: Modified to handle date change detection

**Date Change Logic**:
```python
# If check_in date differs from current date, treat as checked out
is_change_date = att and att.check_in and check_in_date != now_date
if is_change_date:
    employee.attendance_state = 'checked_out'
```

### hr.employee (inherited)
**File**: `models/starrylord_hr_attendance.py`

Extended employee model with custom attendance compute methods.

### hr.attendance.raw
**File**: `models/hr_attendance_raw.py`

Raw attendance data storage for import processing.

### sl.attendance.import
**File**: `models/sl_attendance_import.py`

Attendance data import functionality from external sources.

### sl.attendance.repair
**File**: `models/sl_attendance_repair.py`

Manual attendance correction/repair records.

### starrylord.hr.attendance.check
**File**: `models/starrylord_hr_attendance_check.py`

Attendance anomaly checking and reporting.

### sl.hr.attendance.job
**File**: `models/sl_hr_attendance_job.py`

Scheduled job for attendance processing.

### tier.definition (inherited)
**File**: `models/tier_definition.py`

Integration with tier validation framework.

## Wizards
- `wizard/wizard_hr_attendance_check.py`: Attendance verification wizard

## Scheduled Jobs (Cron)
- `data/cron_attendance_anomaly.xml`: Automated anomaly detection

## Email Templates
- `data/email_template_attendance_anomaly.xml`: Anomaly notification emails

## Views
- `views/hr_attendance_view.xml`: Main attendance views
- `views/hr_attendance_raw_view.xml`: Raw data views
- `views/sl_attendance_repair.xml`: Repair/correction views
- `views/sl_attendance_import_view.xml`: Import interface

## Frontend Assets
```python
'web.assets_backend': [
    'sl_hr_attendance/static/src/**/*',
],
'sl_hr_attendance.assets_public_attendance': [
    # Bootstrap and core web assets for public attendance kiosk
]
```

## Technical Notes

### Timezone Handling
Uses UTC+8 timezone for Taiwan:
```python
check_in_date = (att.check_in + relativedelta(hours=+8)).date()
now_date = (datetime.datetime.now() + relativedelta(hours=+8)).date()
```

### Overlap Validation Disabled
The standard attendance overlap validation is disabled:
```python
@api.constrains('check_in', 'check_out', 'employee_id')
def _check_validity(self):
    return True
```

## Odoo 19 Compliance
- Upgraded from Odoo 17 to Odoo 19
- Uses direct view attributes (no deprecated `attrs`)
- Proper license field in manifest

## Integration Points
- Uses `hr.personal.calendar` for schedule reference
- Extends standard `hr.attendance` model
- Integrates with tier validation for repairs
- Email notifications for anomalies
