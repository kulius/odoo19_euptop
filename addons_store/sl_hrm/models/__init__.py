from . import hr_dependents_information
from . import hr_employee
from . import hr_employee_public
from . import res_config_settings
from . import hr_employee_working
from . import hr_health_insurance_history
from . import hr_health_insurance_gap
from . import hr_labor_harm_insurance_gap
from . import hr_labor_harm_insurance_history
from . import hr_labor_insurance_gap
from . import hr_labor_insurance_history
from . import hr_batch_operation
from . import res_users
from . import hr_department
from . import sl_res_company
from . import sl_res_partner
from . import sl_plant_area
from . import hr_health_report_line
from . import sl_health_report_check_setting
from . import sl_license_check_setting
from . import sl_license_line
from . import hr_labor_pension_gap
from . import hr_labor_pension_history
from . import hr_insurance_doc
from . import hr_salary_tax_gap
from . import sl_res_bank

# 從 sl_hrm_personal_calendar 合併
from . import hr_personal_calendar
from . import hr_schedule
from . import hr_shchedule_time_type
from . import starrylord_holiday_hour_list
from . import starrylord_holiday_min_list

# 從 sl_hrm_holiday 合併
from . import starrylord_holiday_type
from . import starrylord_holiday_allocation
from . import starrylord_holiday_apply
from . import starrylord_holiday_personal
from . import starrylord_annual_leave_setting
from . import hr_public_holiday
from . import starrylord_holiday_used_record
from . import starrylord_tier_definition
from . import starrylord_holiday_job
from . import starrylord_holiday_cancel

# 從 sl_hr_attendance 合併 (必須在 sl_hrm_overtime 之前，因為 overtime 繼承 hr.attendance.check)
from . import starrylord_hr_attendance
from . import starrylord_hr_attendance_check  # 定義 hr.attendance.check
from . import sl_hr_attendance_job
from . import sl_attendance_repair
from . import sl_attendance_import
from . import hr_attendance_raw
from . import tier_definition_attendance

# 從 sl_hrm_overtime 合併 (依賴 hr.attendance.check)
from . import starrylord_overtime_apply  # 繼承 hr.attendance.check
from . import starrylord_overtime_type
from . import starrylord_overtime_tier_definition
from . import overtime_exchange_consent
