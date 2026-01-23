from odoo import api, fields, models
from odoo.exceptions import UserError


class StarryLordHolidayType(models.Model):
    _name = 'starrylord.holiday.type'
    _description = '假別'

    name = fields.Char(string='名稱')
    request_unit = fields.Selection([('day', '日'), ('hour', '小時'), ('half', '半小時'), ("quarter", "十五分鐘")],
                                    string='請假最小單位')
    salary_calculation = fields.Selection([('full_pay', '全薪計算'), ('half_pay', '半薪計算'), ('no_pay', '不支薪')],
                                          string='薪資計算方式')
    is_distribute = fields.Boolean(string='是否需要分配')
    is_com_allocation = fields.Boolean(string='是否為系統分配', compute='compute_is_com_allocation')
    # leave_validation_type = fields.Selection([('no_validation', '無須核准'), ('hr', '由人資單位'), ('manager', '由該員工經理'),
    #                                          ('both', '由該員工經理與人資單位')], string='核准方式')
    is_holiday_comp = fields.Boolean(string='是否為加班補休', compute='compute_is_holiday_comp')

    note = fields.Text(string='備註')
    
    def compute_is_holiday_comp(self):
        for rec in self:
            setting = rec.env['ir.config_parameter'].sudo()
            holiday_comp_id = int(setting.get_param('sl_hrm_holiday.holiday_comp_id', default=False))
            if rec.id == holiday_comp_id:
                rec.is_holiday_comp = True
            else:
                rec.is_holiday_comp = False

    @api.constrains('request_unit')
    def check_request_unit(self):
        for rec in self:
            # 當變更加班補休最小單位時所有加班單位低於該單位便要以最新單位為準
            if rec.is_holiday_comp:
                if rec.request_unit == 'half':
                    request_num = 0.5
                elif rec.request_unit == 'quarter':
                    request_num = 0.25
                else:
                    request_num = 1
                for overtime_type in rec.env['starrylord.overtime.type'].search([]):
                    if overtime_type.time_type == 'half':
                        check_num = 0.5
                    elif overtime_type.time_type == 'quarter':
                        check_num = 0.25
                    else:
                        check_num = 1
                    if request_num > check_num:
                        overtime_type.time_type = rec.request_unit
                if rec.request_unit == 'day':
                    raise UserError('加班補休最小單位不可為日')

    @api.constrains('is_distribute')
    def check_is_distribute(self):
        for rec in self:
            if rec.is_com_allocation:
                if not rec.is_distribute:
                    raise UserError('系統分配之假別必須使用分配')

    def compute_is_com_allocation(self):
        for rec in self:
            setting = self.env['ir.config_parameter'].sudo()
            holiday_special_id = int(setting.get_param('sl_hrm_holiday.holiday_special_id', default=False))  # 特休
            holiday_sick_id = int(setting.get_param('sl_hrm_holiday.holiday_sick_id', default=False))  # 病假
            holiday_leave_id = int(setting.get_param('sl_hrm_holiday.holiday_leave_id', default=False))  # 事假
            holiday_menstrual_id = int(setting.get_param('sl_hrm_holiday.holiday_menstrual_id', default=False))  # 生理假
            holiday_comp_id = int(setting.get_param('sl_hrm_holiday.holiday_comp_id', default=False))  # 補休
            all_com = [holiday_special_id, holiday_sick_id, holiday_leave_id, holiday_menstrual_id, holiday_comp_id]
            if rec.id in all_com:
                rec.is_com_allocation = True
            else:
                rec.is_com_allocation = False
