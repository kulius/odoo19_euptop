# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StarryLordCommentWizard(models.TransientModel):
    _inherit = "comment.wizard"

    comment = fields.Char(string="Comment", required=False)
