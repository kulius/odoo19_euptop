# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CustomerVisit(models.Model):
    _name = 'customer.visit'
    _description = '客戶訪談登錄'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'register_date desc, id desc'

    name = fields.Char(
        string='單據單號',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
    )
    register_date = fields.Date(
        string='登錄日期',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    salesperson_id = fields.Many2one(
        'hr.employee',
        string='業務員',
        required=True,
        tracking=True,
        default=lambda self: self._get_default_employee(),
    )
    employee_name = fields.Char(
        string='員工姓名',
        related='salesperson_id.name',
        store=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        required=True,
        default=lambda self: self.env.company,
    )
    line_ids = fields.One2many(
        'customer.visit.line',
        'visit_id',
        string='訪談明細',
        copy=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'customer_visit_attachment_rel',
        'visit_id',
        'attachment_id',
        string='附加檔案',
    )
    note = fields.Html(string='備註')

    # 統計欄位
    line_count = fields.Integer(
        string='訪談筆數',
        compute='_compute_line_count',
        store=True,
    )

    @api.depends('line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    def _get_default_employee(self):
        """取得當前使用者的員工記錄"""
        return self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'customer.visit'
                ) or 'New'
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.line_ids:
                # 允許刪除，但給予提示
                pass
        return super().unlink()

    def action_view_lines(self):
        """查看訪談明細"""
        self.ensure_one()
        return {
            'name': _('訪談明細'),
            'type': 'ir.actions.act_window',
            'res_model': 'customer.visit.line',
            'view_mode': 'list,form',
            'domain': [('visit_id', '=', self.id)],
            'context': {'default_visit_id': self.id},
        }


class CustomerVisitLine(models.Model):
    _name = 'customer.visit.line'
    _description = '客戶訪談明細'
    _order = 'visit_date desc, id desc'

    visit_id = fields.Many2one(
        'customer.visit',
        string='訪談主檔',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='序號', default=10)

    # 客戶資訊
    partner_id = fields.Many2one(
        'res.partner',
        string='客戶代號',
        required=True,
        domain="[('is_company', '=', True)]",
    )
    partner_name = fields.Char(
        string='客戶簡稱',
        related='partner_id.name',
        store=True,
    )

    # 拜訪資訊
    visit_date = fields.Date(
        string='拜訪日期',
        required=True,
        default=fields.Date.context_today,
    )
    project_id = fields.Many2one(
        'project.project',
        string='專案代號',
        required=True,
    )
    goal = fields.Text(string='目標')

    # 拜訪對象
    contact_name = fields.Char(
        string='拜訪對象',
        required=True,
    )
    department = fields.Char(string='部門')
    job_title = fields.Char(string='職稱')

    # 訪談內容
    content = fields.Text(
        string='訪談內容',
        required=True,
    )
    follow_up = fields.Text(
        string='後續動作',
        required=True,
    )
    countermeasure = fields.Text(string='對策')

    # 關聯欄位
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        related='visit_id.company_id',
        store=True,
    )
    salesperson_id = fields.Many2one(
        'hr.employee',
        string='業務員',
        related='visit_id.salesperson_id',
        store=True,
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """當選擇客戶時，可以自動帶入相關資訊"""
        if self.partner_id:
            # 可以在此處添加自動帶入客戶相關資訊的邏輯
            pass
