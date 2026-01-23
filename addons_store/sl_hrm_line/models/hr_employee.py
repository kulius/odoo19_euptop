# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee with LINE Binding'

    # LINE 相關欄位
    line_user_id = fields.Char(
        string='LINE User ID',
        index=True,
        copy=False,
        help='LINE LIFF 登入後取得的用戶 ID'
    )
    line_display_name = fields.Char(
        string='LINE 顯示名稱',
        help='LINE 用戶的顯示名稱'
    )
    line_picture_url = fields.Char(
        string='LINE 頭像 URL',
        help='LINE 用戶的頭像網址'
    )
    line_binding_date = fields.Datetime(
        string='LINE 綁定時間',
        readonly=True
    )
    is_line_bound = fields.Boolean(
        string='已綁定 LINE',
        compute='_compute_is_line_bound',
        store=True
    )

    _sql_constraints = [
        ('line_user_id_unique', 'UNIQUE(line_user_id)',
         'LINE User ID 已被其他員工綁定！')
    ]

    @api.depends('line_user_id')
    def _compute_is_line_bound(self):
        """計算是否已綁定 LINE"""
        for employee in self:
            employee.is_line_bound = bool(employee.line_user_id)

    def action_unbind_line(self):
        """解除 LINE 綁定"""
        self.ensure_one()
        self.write({
            'line_user_id': False,
            'line_display_name': False,
            'line_picture_url': False,
            'line_binding_date': False,
        })
        return True

    @api.model
    def get_employee_by_line_user_id(self, line_user_id):
        """
        透過 LINE User ID 取得員工資料
        :param line_user_id: LINE User ID
        :return: hr.employee recordset
        """
        if not line_user_id:
            return self.browse()
        employee = self.search([('line_user_id', '=', line_user_id)], limit=1)
        return employee

    def _get_employee_data(self):
        """
        取得員工資料（供 API 回傳）
        :return: dict
        """
        self.ensure_one()
        return {
            'id': self.id,
            'employee_id': self.id,
            'name': self.name,
            'department': self.department_id.name if self.department_id else None,
            'department_id': self.department_id.id if self.department_id else None,
            'job_title': self.job_title or None,
            'work_email': self.work_email or None,
            'work_phone': self.work_phone or None,
            'line_user_id': self.line_user_id,
            'line_display_name': self.line_display_name,
            'picture_url': self.line_picture_url or (
                f'/web/image/hr.employee/{self.id}/image_128' if self.image_128 else None
            ),
        }
