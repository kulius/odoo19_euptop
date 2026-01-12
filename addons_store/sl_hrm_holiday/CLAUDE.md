# Starry Lord HRM Holiday Module

## Module Information
- **Name**: Starry Lord HRM 請休假 (Leave/Holiday)
- **Version**: 19.0.0.1
- **License**: LGPL-3
- **Author**: Starry Lord
- **Category**: HRM

## Purpose
Comprehensive leave/holiday management system for employees. Handles leave applications, allocations, approval workflows, and tracking of various leave types including annual leave, sick leave, compensation leave, and more.

## Dependencies
- `base`
- `hr`
- `sl_tier_validation` (approval workflow)
- `sl_hrm_personal_calendar` (calendar integration)

## Key Models

### starrylord.holiday.apply
**File**: `models/starrylord_holiday_apply.py`

Main leave application model. Inherits from `mail.thread`.

**Key Fields**:
- `employee_id`: Applicant (hr.employee.public)
- `holiday_allocation_id`: Leave type (starrylord.holiday.type)
- `substitute_id`: Deputy/substitute employee
- `state`: Workflow state (draft, f_approve, agree, refused)
- `start_day`, `end_day`: Leave period
- `hour_from_m`, `min_from_m`, `hour_to_m`, `min_to_m`: Time selection fields
- `holiday_time_total`: Total leave hours
- `time_type`: Leave unit (day, hour, half, quarter)
- `used_record_ids`: Link to usage records
- `holiday_allocation_id_comp`: Compensation leave allocation selector

**Key Methods**:
- `to_f_approve()`: Submit for approval with validations
- `agree()`: Approve and create calendar entry
- `to_refused()`: Reject application
- `to_draft()`: Reset to draft
- `create_and_check_allocation()`: Allocate leave hours from available balance
- `compute_last_time()`: Calculate remaining leave balance
- `retrieve_dashboard()`: Get dashboard data for leave balances

### starrylord.holiday.type
**File**: `models/starrylord_holiday_type.py`

Leave type definitions (annual, sick, compensation, etc.)

### starrylord.holiday.allocation
**File**: `models/starrylord_holiday_allocation.py`

Leave allocation records for employees with validity periods.

### starrylord.holiday.used.record
**File**: `models/starrylord_holiday_used_record.py`

Tracks leave usage against allocations.

### hr.public.holiday
**File**: `models/hr_public_holiday.py`

Public/national holiday definitions.

### starrylord.annual.leave.setting
**File**: `models/starrylord_annual_leave_setting.py`

Annual leave policy configuration.

## Wizards
- `wizard/wizard_holiday_batch_allocation.py`: Batch leave allocation
- `wizard/holiday_used_record_wizard.py`: Leave usage record wizard

## System Parameters
The module uses several system parameters (ir.config_parameter):
- `holiday_special_id`: Annual leave type ID
- `holiday_sick_id`: Sick leave type ID
- `holiday_leave_id`: Personal leave type ID
- `holiday_menstrual_id`: Menstrual leave type ID
- `holiday_comp_id`: Compensation leave type ID
- `can_self_as_substitute_id`: Allow self as substitute flag

## Business Rules
1. **Menstrual Leave**: Limited to 8 hours per month
2. **Leave Unit Validation**: Validates against time_type (hour/half/quarter)
3. **Substitute Validation**: Checks if substitute is on leave during same period
4. **Time Overlap**: Prevents overlapping leave applications
5. **Leave Balance**: Validates against allocated leave balance

## Frontend Assets
```javascript
'web.assets_backend': [
    'sl_hrm_holiday/static/src/views/*.js',
    'sl_hrm_holiday/static/src/**/*.xml',
]
```

## Odoo 19 Compliance
- Upgraded from Odoo 17 to Odoo 19
- Uses direct view attributes (no deprecated `attrs`)
- Proper license field in manifest

## Integration Points
- Creates `hr.personal.calendar` entries when leave is approved
- Integrates with tier validation for approval workflow
- Dashboard API for leave balance display
