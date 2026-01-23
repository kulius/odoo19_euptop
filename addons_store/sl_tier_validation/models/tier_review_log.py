# Copyright 2017-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TierReviewLog(models.Model):
    _name = "tier.review.log"
    _description = "Tier Review Log"

    name = fields.Char(related="definition_id.name", readonly=True)
    status = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("pending", "Pending"),
            ("rejected", "Rejected"),
            ("approved", "Approved"),
        ],
        default="waiting",
    )
    model = fields.Char(string="Related Document Model", index=True)
    res_id = fields.Integer(string="Related Document ID", index=True)
    definition_id = fields.Many2one(comodel_name="tier.definition")
    company_id = fields.Many2one(
        related="definition_id.company_id",
        store=True,
    )
    review_type = fields.Selection(related="definition_id.review_type", readonly=True)
    reviewer_id = fields.Many2one(related="definition_id.reviewer_id", readonly=True)
    reviewer_group_id = fields.Many2one(
        related="definition_id.reviewer_group_id", readonly=True
    )
    reviewer_field_id = fields.Many2one(
        related="definition_id.reviewer_field_id", readonly=True
    )
    reviewer_ids = fields.Many2many(
        string="Reviewers",
        comodel_name="res.users",
        store=True,
    )
    sequence = fields.Integer(string="Tier")
    todo_by = fields.Char(string="Reviewers")
    done_by = fields.Many2one(comodel_name="res.users")
    requested_by = fields.Many2one(comodel_name="res.users")
    reviewed_date = fields.Datetime(string="Validation Date")
    reviewed_formated_date = fields.Char(
        string="Validation Formated Date", compute="_compute_reviewed_formated_date"
    )
    comment = fields.Char(string="Comments")

    @api.depends_context("tz")
    def _compute_reviewed_formated_date(self):
        timezone = self._context.get("tz") or self.env.user.partner_id.tz or "UTC"
        for review in self:
            if not review.reviewed_date:
                review.reviewed_formated_date = False
                continue
            reviewed_date_utc = pytz.timezone("UTC").localize(review.reviewed_date)
            reviewed_date_tz = reviewed_date_utc.astimezone(pytz.timezone(timezone))
            review.reviewed_formated_date = reviewed_date_tz.replace(tzinfo=None)
