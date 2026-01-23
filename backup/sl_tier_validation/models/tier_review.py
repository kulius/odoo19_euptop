# Copyright 2017-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TierReview(models.Model):
    _inherit = "tier.review"

    # model_id = fields.Many2one(string="所屬表單", related="definition_id.model_id", store="True", readonly=True)
    # model_note = fields.Char(string="審核單號", compute="_compute_can_sign", store="True")
    # update_data = fields.Boolean(string="執行compute", compute="_compute_can_sign")

    def _compute_can_sign(self):
        for record in self:
            print(record.model)
            resource = self.env[record.model].browse(record.res_id)
            record.model_note = resource.name
