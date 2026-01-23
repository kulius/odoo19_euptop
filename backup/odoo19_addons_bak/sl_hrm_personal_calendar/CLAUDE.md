# Starry Lord HRM Personal Calendar Module

## Module Information
- **Name**: Starry Lord 個人行事曆 (Personal Calendar)
- **Version**: 19.0.0.1
- **License**: LGPL-3
- **Author**: Starry Lord
- **Category**: HRM

## Purpose
This module provides personal calendar and scheduling functionality for employees in an HRM system. It allows management of employee work schedules, shifts, and various calendar events including overtime, leave, holidays, and regular working days.

## Dependencies
- `base`
- `hr`

## Key Models

### hr.personal.calendar
**File**: `models/hr_personal_calendar.py`

Main model for managing personal calendar entries. Inherits from `mail.thread`.

**Key Fields**:
- `employee_id`: Link to employee (hr.employee.public)
- `department_id`: Related department
- `date_type`: Selection field with types: schedule, overtime, leave, no_work, holiday, day_off, regular_holiday
- `schedule_id`: Link to hr.schedule
- `time_type_id`: Link to hr.schedule.time.type
- `calendar_date`: Date of the calendar entry
- `start_date`, `end_date`: Datetime range for the entry
- `am_start`, `am_end`, `pm_start`, `pm_end`: Morning/afternoon time slots

**Key Methods**:
- `merge_date_time()`: Combines date and float time into datetime with timezone correction (UTC+8)
- `onchange_calendar_date()`: Updates time fields based on schedule time type

### hr.schedule
**File**: `models/hr_schedule.py`

Model for defining work schedules/shifts.

### hr.schedule.time.type
**File**: `models/hr_shchedule_time_type.py`

Model for schedule time type codes.

### hr.employee (inherited)
**File**: `models/hr_employee.py`

Extends hr.employee with schedule-related fields.

## Views
- `views/hr_schedule.xml`: Schedule management views
- `views/hr_schedule_time_type.xml`: Time type configuration views
- `views/hr_personal_calendar.xml`: Personal calendar views
- `views/hr_employee.xml`: Extended employee views
- `views/menu.xml`: Menu structure

## Security
- `security/hr_personal_calendar_security.xml`: Security rules
- `security/ir.model.access.csv`: Access control list

## Technical Notes

### Timezone Handling
The module uses UTC+8 timezone correction. All datetime conversions subtract 8 hours for storage:
```python
datetime_obj -= dt.timedelta(hours=8)
```

### Odoo 19 Compliance
- Module upgraded from Odoo 17 to Odoo 19
- Uses direct `invisible`, `readonly`, `required` attributes in views (no deprecated `attrs`)
- Includes proper `license` field in manifest

## Integration Points
This module serves as a foundation for other HRM modules:
- `sl_hrm_holiday`: Depends on this module for leave calendar integration
- `sl_hrm_overtime`: Depends on this module for overtime calendar integration
- `sl_hr_attendance`: Depends on this module for attendance scheduling
