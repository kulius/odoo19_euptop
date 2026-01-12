# Starry Lord HRM Overtime Module

## Module Information
- **Name**: Starry Lord HRM 加班 (Overtime)
- **Version**: 19.0.0.1
- **License**: LGPL-3
- **Author**: Starry Lord
- **Category**: HRM

## Purpose
Comprehensive overtime management system for employees. Handles overtime applications, approval workflows, and conversion to either cash payment or compensation leave. Includes Taiwan Labor Standards Act compliance checks.

## Dependencies
- `base`
- `hr`
- `sl_tier_validation` (approval workflow)
- `sl_hrm_holiday` (compensation leave integration)

## Key Models

### starrylord.overtime.apply
**File**: `models/starrylord_overtime_apply.py`

Main overtime application model. Inherits from `mail.thread`.

**Key Fields**:
- `employee_id`: Applicant (hr.employee.public)
- `overtime_type_id`: Overtime type (starrylord.overtime.type)
- `state`: Workflow state (draft, f_approve, agree, refused)
- `start_day`: Overtime date
- `hour_from`, `hour_to`, `min_from`, `min_to`: Time selection
- `duration_time`: Calculated overtime hours
- `type`: Payout type (cash or holiday/compensation)
- `has_overtime_meal_allowance`: Meal allowance flag
- `without_rest_time`: Continuous work without rest flag
- `hr_confirm_state`: HR confirmation status (pending, confirmed, invalid)
- `allocation_validity_end`: Compensation leave expiry date

**Key Methods**:
- `calc_duration_time()`: Calculate overtime hours based on schedule
- `check_labor_law_overtime_limit()`: Taiwan Labor Standards Act validation
- `check_duty_over_6days()`: 7-day continuous work check
- `check_overtime()`: Monthly/quarterly limits validation
- `to_f_approve()`: Submit for approval
- `agree()`: Manager approval
- `action_hr_confirm()`: HR confirmation and compensation leave creation

### starrylord.overtime.type
**File**: `models/starrylord_overtime_type.py`

Overtime type definitions by day type:
- `schedule`: Weekday overtime
- `day_off`: Rest day overtime (Saturday)
- `regular_holiday`: Regular holiday overtime (Sunday)
- `holiday`: National holiday overtime

### overtime.exchange.consent
**File**: `models/overtime_exchange_consent.py`

Overtime exchange consent records.

## Labor Law Compliance

### Taiwan Labor Standards Act Rules
1. **Weekday Overtime**: Maximum 4 hours per day
2. **Holiday Overtime**: Maximum 12 hours per day
3. **7-Day Rule**: Cannot work 7 consecutive days
4. **Monthly Limit**: Configurable via `max_overtime_month`
5. **Quarterly Limit**: Configurable via `max_overtime_three_month`

### Overtime Calculation Logic
- **Weekday**: Hours beyond work_end time
- **Rest Day**: Total hours minus 1 hour rest (if >= 5 hours)
- **Holiday/Regular Holiday**: 8 hours minimum (work 1 hour = get 8 hours), beyond 8 hours = actual - 1

## System Parameters
- `max_overtime_month`: Monthly overtime hour limit
- `max_overtime_three_month`: Quarterly overtime hour limit
- `min_overtime_unit`: Minimum overtime unit (hour/half/quarter)
- `sl_hrm_payroll.regular_holiday_exclude_payroll`: Force cash for regular holiday overtime

## Workflow
1. **Draft**: Employee creates application
2. **F_Approve**: Submitted for manager approval
3. **Agree**: Manager approved
4. **HR Confirmation**: HR validates and creates compensation allocation (if holiday type)

## Compensation Leave Creation
When `type = 'holiday'` and HR confirms:
- Creates `starrylord.holiday.allocation` record
- Validity: From overtime month start to 6 months later
- Links to `sl_overtime_apply_id`

## Reports
- `report/overtime_exchange_consent_templates.xml`: Consent form template
- `report/overtime_exchange_consent_report.py`: Report controller

## Odoo 19 Compliance
- Upgraded from Odoo 17 to Odoo 19
- Uses direct view attributes (no deprecated `attrs`)
- Proper license field in manifest

## Integration Points
- Creates `hr.personal.calendar` entries for overtime
- Creates `starrylord.holiday.allocation` for compensation leave
- Integrates with tier validation for approval workflow
