# -*- coding: utf-8 -*-
from odoo import models, fields, api

from odoo import api, fields, models

class TierPortalForm(models.Model):
    _name = "tier.portal.form"
    _description = "新增簽核表單統一界面"

    name = fields.Char(string="表單名稱")
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Referenced Model",
        domain=lambda self: [("model", "in", self.get_tier_validation_model_names())],
    )
    model = fields.Char(related="model_id.model", index=True, store=True)
    notes = fields.Text('事由說明')

    @api.model
    def get_tier_validation_model_names(self):
        res = self.env["tier.definition"]._get_tier_validation_model_names()
        return res

    def action_open_form(self):
        self.ensure_one()
        return {
            'name': '新增簽核表單',
            'type': 'ir.actions.act_window',
            'res_model': self.model_id.model,
            'view_mode': 'form',
        }

    def action_open_tree_draft(self):
        self.ensure_one()
        if self.model_id.model == 'hr.personal.calendar.repair':
            return {
                'name': '未送簽表單',
                'type': 'ir.actions.act_window',
                'res_model': self.model_id.model,
                'view_mode': 'tree,form',
                'domain': [('state', 'in', ['draft']), ('user_id', '=', self.env.user.employee_id.id)],
            }
        else:
            return {
                'name': '未送簽表單',
                'type': 'ir.actions.act_window',
                'res_model': self.model_id.model,
                'view_mode': 'tree,form',
                'domain': [('state', 'in', ['draft']),('employee_id', '=', self.env.user.employee_id.id)],
            }

    def action_open_tree_review(self):
        self.ensure_one()
        if self.model_id.model == 'hr.personal.calendar.repair':
            return {
                'name': '簽核中表單',
                'type': 'ir.actions.act_window',
                'res_model': self.model_id.model,
                'view_mode': 'tree,form',
                'domain': [('state', 'in', ['f_approve']), ('employee_id', '=', self.env.user.employee_id.id)],
            }
        else:
            return {
                'name': '簽核中表單',
                'type': 'ir.actions.act_window',
                'res_model': self.model_id.model,
                'view_mode': 'tree,form',
                'domain': [('state', 'in', ['f_approve']), ('employee_id', '=', self.env.user.employee_id.id)],
            }


