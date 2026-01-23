# sl_hrm wizards
from . import wizard_dependents_add
from . import wizard_labor_insurance_change
from . import wizard_health_insurance_change
from . import wizard_labor_pension_change
from . import wizard_labor_harm_insurance_change

# 從 sl_hrm_holiday 合併
from . import wizard_holiday_batch_allocation
from . import holiday_used_record_wizard

# 從 sl_hrm_overtime 合併
from . import overtime_apply_record_wizard

# 從 sl_hr_attendance 合併
from . import wizard_hr_attendance_check
