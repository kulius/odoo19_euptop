from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrEmployeeWorking(models.Model):
    _name = "hr.employee.working"
    _description = '在離職異動歷程明細'
    _order = "start_date desc"

    employee_id = fields.Many2one('hr.employee', string='員工')
    start_date = fields.Date(string='生效日期', required=True)
    change_reason_selection = fields.Selection([('on_board', '到職'), ('resign', '離職'), ('furlough', '留職停薪'), ('reinstatement', '復職')], string='異動原因', required=True)
    comment = fields.Text(string='備註')
    # 必須先離職才能再到職
    @api.model
    def create(self, vals):
        # 檢查較早的資料
        check_after = self.env['hr.employee.working'].search([('employee_id', '=', vals['employee_id']),
                                                              ('start_date', '<=', vals['start_date'])],
                                                             order="start_date desc", limit=1)
        # 檢查較晚的資料
        check_front = self.env['hr.employee.working'].search([('employee_id', '=', vals['employee_id']),
                                                              ('start_date', '>=', vals['start_date'])],
                                                             order="start_date desc", limit=1)
        if vals['change_reason_selection'] in ['on_board', 'reinstatement']:
            vals_reason = True
        else:
            vals_reason = False
        if check_after.change_reason_selection in ['on_board', 'reinstatement']:
            check_after_reason = True
        else:
            check_after_reason = False
        if check_front.change_reason_selection in ['on_board', 'reinstatement']:
            check_front_reason = True
        else:
            check_front_reason = False
        if not check_front:
            check_front_reason = 'no_data'
        if (vals_reason == check_after_reason or vals_reason == check_front_reason
                or check_after_reason == check_front_reason):
            if check_after_reason or check_front_reason:
                raise UserError('請先離職再復職')
            else:
                if check_after and check_front:
                    raise UserError('不可重複到離職')
        return super(HrEmployeeWorking, self).create(vals)

    def add_insurance_history(self):
        """在人員離職的時候自動新增勞健退災退保紀錄"""        
        models = [
            {"model": "hr.labor.pension.history", "field": "employee_id"},
            {"model": "hr.labor.insurance.history", "field": "labor_insurance_history_id"},
            {"model": "hr.health.insurance.history", "field": "health_insurance_history_id"},
            {"model": "hr.labor.harm.insurance.history", "field": "employee_id"}
        ]
        
        for model_info in models:
            try:
                # 使用exists()確保我們有有效的記錄集
                existing = self.env[model_info['model']].search([
                    (model_info['field'], '=', self.employee_id.id),
                    ('start_date', '=', self.employee_id.resignation_date)
                ], limit=1)
                
                if not existing:
                    self.env[model_info['model']].sudo().create({
                        model_info['field']: self.employee_id.id,
                        'start_date': self.employee_id.resignation_date,
                        'change_reason_selection': 'off',
                    })
                    
            except Exception as e:
                _logger.error(
                    "Error creating %s record for employee %s (ID:%s). Error: %s",
                    model_info['model'],
                    self.employee_id.name,
                    self.employee_id,
                    str(e)
                )
                continue
