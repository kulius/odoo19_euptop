import datetime
import re

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class StarryLordResBankInherit(models.Model):
    _inherit = 'res.bank'

    attachment_ids = fields.Many2many('ir.attachment', string='銀行存摺封面', relation='m2m_res_bank_rel',
                                      column1='res_bank_id', column2='attachment_id', inverse_name='res_bank_ids')
