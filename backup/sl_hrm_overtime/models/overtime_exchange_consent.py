from datetime import date, datetime, timedelta
from PyPDF2 import PdfFileWriter, PdfFileReader
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import io


class StarryLordOvertimeExchangeConsent(models.Model):
    _name = 'starrylord.overtime.exchange.consent'
    _description = '例假日與休息日調移同意書'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='單號', readonly=True, copy=False)
    overtime_id = fields.Many2one('starrylord.overtime.apply', string='加班申請單', required=True, ondelete='cascade')
    employee_id = fields.Many2one(related='overtime_id.employee_id', store=True, readonly=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True, readonly=True)

    regular_holiday_date = fields.Date(string='原例假日', required=True)
    day_off_date = fields.Date(string='原休息日', required=True)
    moved_day_off_date = fields.Date(string='調整後休息日', required=True)
    moved_regular_holiday_date = fields.Date(string='調整後例假日', required=True)

    note = fields.Char(string='備註')
    
    # PDF附件相關欄位
    exchange_consent_attachment_ids = fields.Many2many(
        comodel_name='ir.attachment', 
        string='例休調移同意書PDF檔案', 
        relation="m2m_ir_exchange_consent_attachment_rel",
        column1="m2m_id",
        column2="attachment_id"
    )
    
    _sql_constraints = [
        ('unique_overtime_id', 'unique(overtime_id)', '每個加班申請只能建立一份例休調移同意書！'),
    ]

    @api.model
    def create(self, vals):
        overtime = self.env['starrylord.overtime.apply'].browse(vals.get('overtime_id'))
        employee_name = overtime.employee_id.name or ''
        overtime_name = overtime.name or ''
        vals['name'] = f"{employee_name} {overtime_name} 例假日與休息日調移同意書"
        # 預設調整後例假日與原例假日相同（可手動調整）
        if not vals.get('moved_regular_holiday_date') and vals.get('regular_holiday_date'):
            vals['moved_regular_holiday_date'] = vals['regular_holiday_date']
        return super().create(vals)

    @api.model
    def default_get(self, fields_list):
        """設定預設值，特別是從 context 取得 overtime_id"""
        defaults = super().default_get(fields_list)
        if self.env.context.get('default_overtime_id'):
            defaults['overtime_id'] = self.env.context['default_overtime_id']
        return defaults

    def action_generate_exchange_consent_pdf(self):
        """生成同意書PDF附件"""
        self.ensure_one()
        template_id = self.env.ref('sl_hrm_overtime.action_overtime_exchange_consent_report')
        pdf = template_id._render_qweb_pdf(template_id.id, [self.id])[0]
        
        output_buffer = io.BytesIO()
        pdf_writer = PdfFileWriter()
        pdf_reader = PdfFileReader(io.BytesIO(pdf))
        pdf_writer.appendPagesFromReader(pdf_reader)
        
        pdf_writer.write(output_buffer)
        data_record = base64.b64encode(output_buffer.getvalue())
        attach_name = _('例休調移同意書-%s.pdf') % (self.overtime_id.name or self.name)
        attachment = self.env['ir.attachment'].create({
            'name': attach_name,
            'datas': data_record,
            'res_model': 'starrylord.overtime.exchange.consent',
            'res_id': self.id,
            'type': 'binary',
            'mimetype': 'application/pdf',
            'public': True
        })
        
        self.write({'exchange_consent_attachment_ids': [(6, 0, [attachment.id])]})
     
class StarryLordOvertimeApplyExtend(models.Model):
    _inherit = 'starrylord.overtime.apply'

    regular_holiday_exchange_required = fields.Boolean(
        string='需例休調移同意', compute='_compute_exchange_required', store=True)
    regular_holiday_exchange_agree = fields.Boolean(string='本人同意例休調移')
    exchange_consent_id = fields.Many2one('starrylord.overtime.exchange.consent', string='例休調移同意書', copy=False)

    @api.depends('overtime_type_id')
    def _compute_exchange_required(self):
        for rec in self:
            rec.regular_holiday_exchange_required = bool(rec.overtime_type_id and rec.overtime_type_id.date_type == 'regular_holiday')

    def _get_week_dates(self, base_day: date):
        # 取得該週的周一日期，再加上 0..6 得到本週所有日期
        monday = base_day - timedelta(days=base_day.weekday())
        return [monday + timedelta(days=i) for i in range(7)]

    def _guess_day_off_for_week(self, base_day: date):
        self.ensure_one()
        schedule = self.employee_id.schedule_id
        if not schedule:
            return False
        # 找出班表上標記為休息日的星期
        day_off_entries = schedule.worktime_ids.filtered(lambda w: w.date_type == 'day_off')
        if not day_off_entries:
            return False
        # 取第一個休息日定義
        dayofweek = int(day_off_entries[0].dayofweek)
        week_days = self._get_week_dates(base_day)
        return week_days[dayofweek]

    def action_generate_exchange_consent(self):
        for rec in self:
            if not rec.regular_holiday_exchange_required:
                raise UserError(_('此加班單非例假日，不需建立同意書'))
            if not rec.regular_holiday_exchange_agree:
                raise UserError(_('請先勾選「本人同意例休調移」'))
            if rec.exchange_consent_id:
                # 已存在則直接開啟
                action = rec._action_open_consent(rec.exchange_consent_id.id)
                return action
            # 推測本週休息日
            day_off = rec._guess_day_off_for_week(rec.start_day)
            if not day_off:
                raise UserError(_('無法依班表判斷本週的休息日，請先於班表設定休息日(day_off)'))
            consent = self.env['starrylord.overtime.exchange.consent'].create({
                'overtime_id': rec.id,
                'regular_holiday_date': rec.start_day,
                'day_off_date': day_off,
                'moved_day_off_date': rec.start_day,
                'moved_regular_holiday_date': day_off,
            })
            rec.exchange_consent_id = consent.id
            return rec._action_open_consent(consent.id)

    def action_print_exchange_consent(self):
        self.ensure_one()
        if not (self.regular_holiday_exchange_required and self.exchange_consent_id):
            raise UserError(_('沒有可列印的同意書，請先建立同意書'))
        
        # 直接開啟同意書的預覽功能
        return self.exchange_consent_id.action_preview_exchange_consent()

    def _action_open_consent(self, consent_id):
        return {
            'type': 'ir.actions.act_window',
            'name': _('例假日與休息日調移同意書'),
            'res_model': 'starrylord.overtime.exchange.consent',
            'view_mode': 'form',
            'target': 'new',
            'res_id': consent_id,
            'context': {'default_overtime_id': self.id},  # 預設加班申請單
        }

    def to_f_approve(self):
        for rec in self:
            if rec.regular_holiday_exchange_required and not (rec.regular_holiday_exchange_agree and rec.exchange_consent_id):
                raise UserError(_('例假日加班需勾選同意並建立「例休調移同意書」'))
        return super().to_f_approve()

    def agree(self):
        for rec in self:
            if rec.regular_holiday_exchange_required and not (rec.regular_holiday_exchange_agree and rec.exchange_consent_id):
                raise UserError(_('例假日加班需勾選同意並建立「例休調移同意書」'))
        return super().agree()
