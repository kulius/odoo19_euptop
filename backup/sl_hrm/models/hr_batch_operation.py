from odoo import models, fields
from datetime import datetime


class HrBatchOperation(models.TransientModel):
    _name = "hr.batch.operation"
    _description = "勞健保級距批次操作"

    def action_update_all_labor_current_year_insurance_interval(self):
        """更新所有員工當年的勞健保級距，若已存在則不做任何事"""
        insurance_type = [
            {
                'type': 'health',
                'charge_list': 'hr.health.insurance.gap',
                'history': 'hr.health.insurance.history',
                'create': 'create_health_insurance_history',
            },
            {
                'type': 'labor',
                'charge_list': 'hr.labor.insurance.gap',
                'history': 'hr.labor.insurance.history',
                'create': 'create_labor_insurance_history',
            },
        ]
        current_year = datetime.today().year

        employees = self.env['hr.employee'].search([])

        for employee in employees:
            for insurance in insurance_type:
                type = insurance['type']
                existing_current_year_record = self.env[insurance['history']].search([
                    (f"{type}_insurance_history_id", '=', employee.id),
                    ('start_date', '>=', datetime(current_year, 1, 1)),
                    ('start_date', '<=', datetime(current_year, 12, 31)),
                ])
                if existing_current_year_record:
                    continue
                
                insurance_history = self.env[insurance['history']].search([
                    (f"{type}_insurance_history_id", '=', employee.id),
                    ('start_date', '<', datetime(current_year, 1, 1)),
                    ('change_reason_selection', '!=', 'off'),
                ], order="start_date DESC", limit=1)

                if insurance_history:
                    interval = insurance_history[f"{type}_insurance_gap"]
                    charge_list_record = self.env[insurance['charge_list']].search([
                        ('insurance_salary', '=', interval),
                    ], limit=1)

                    if charge_list_record:
                        create_fn = getattr(self, insurance['create'])
                        create_fn(employee.id, insurance_history, current_year, charge_list_record)

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def create_health_insurance_history(self, employee_id, pre_data,  current_year, list_data):
        self.env['hr.health.insurance.history'].create({
            'health_insurance_history_id': employee_id,
            'start_date': datetime(current_year, 1, 1),
            'change_date': datetime.today(),
            'change_reason_selection': 'add',
            'health_rate': pre_data.health_rate,
            'heath_rate_type': pre_data.heath_rate_type,
            'health_insurance_gap_id': list_data.id,
        })

    def create_labor_insurance_history(self, employee_id, pre_data, current_year, list_data):
        self.env['hr.labor.insurance.history'].create({
            'labor_insurance_history_id': employee_id,
            'start_date': datetime(current_year, 1, 1),
            'change_date': datetime.today(),
            'change_reason_selection': 'add',
            'labor_rate': pre_data.labor_rate,
            'labor_identity': pre_data.labor_identity,
            'labor_insurance_gap_id': list_data.id,
        })
