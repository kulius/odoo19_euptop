# Copyright 2017-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from ast import literal_eval

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import frozendict


class StarryLordTierValidation(models.AbstractModel):
    _inherit = "tier.validation"
    _description = "Tier Validation (abstract)"

    review_log_ids = fields.One2many(
        comodel_name="tier.review.log",
        inverse_name="res_id",
        string="Validations",
        domain=lambda self: [("model", "=", self._name)],
        auto_join=True,
    )

    def _validate_tier(self, tiers=False):
        # print('hello this is validate tier %s' % tiers)
        # 寫一筆tier.review.log
        tier_reviews = tiers
        user_reviews = tier_reviews.filtered(
            lambda r: r.status == "pending" and (self.env.user in r.reviewer_ids)
        )
        for user_review in user_reviews:
            self.env['tier.review.log'].create({
                "definition_id": user_review.definition_id.id,
                "status": "approved",
                "model": user_review.model,
                "res_id": user_review.res_id,
                "review_type": user_review.review_type,
                "reviewer_id": user_review.reviewer_id.id,
                "reviewer_group_id": user_review.reviewer_group_id.id,
                "reviewer_field_id": user_review.reviewer_field_id.id,
                "done_by": self.env.user.id,
                "reviewed_date": fields.Datetime.now(),
                "reviewer_ids": [(4, reviewer.id) for reviewer in user_review.reviewer_ids],
                "comment": user_review.comment
            })

        super()._validate_tier(tiers)


    def _rejected_tier(self, tiers=False):
        # print('hello this is rejected tier')
        # 寫一筆tier.review.log
        tier_reviews = tiers
        user_reviews = tier_reviews.filtered(
            lambda r: r.status in ("waiting", "pending")
                      and self.env.user in r.reviewer_ids
        )
        for user_review in user_reviews:
            self.env['tier.review.log'].create({
                "definition_id": user_review.definition_id.id,
                "status": "rejected",
                "model": user_review.model,
                "res_id": user_review.res_id,
                "review_type": user_review.review_type,
                "reviewer_id": user_review.reviewer_id.id,
                "reviewer_group_id": user_review.reviewer_group_id.id,
                "reviewer_field_id": user_review.reviewer_field_id.id,
                "done_by": self.env.user.id,
                "reviewed_date": fields.Datetime.now(),
                "reviewer_ids": [(4, reviewer.id) for reviewer in user_review.reviewer_ids],
                "comment": user_review.comment
            })
        super()._rejected_tier(tiers)
    def _rejected_to_previous_tier(self, tiers=False):
        # reject to previous review
        self.ensure_one()
        # tier_reviews = tiers or self.review_ids
        # all_reviews = self.review_ids.filtered(
        #     lambda r: r.status in ("waiting", "pending")
        # )
        # my_reviews = all_reviews.filtered(lambda r: self.env.user in r.reviewer_ids)
        # my_sequence = min(my_reviews)
        # current_review = my_reviews.filtered(lambda r: r.sequence == my_sequence.sequence)
        current_review = tiers
        current_tier_reviews = []
        current_review.write({
            "status": "waiting",
            "done_by": self.env.user.id,
            "reviewed_date": fields.Datetime.now(),
        })
        current_tier_reviews.append(current_review)
        for user_review in current_tier_reviews:
            self.env['tier.review.log'].create({
                "definition_id": user_review.definition_id.id,
                "status": "rejected",
                "model": user_review.model,
                "res_id": user_review.res_id,
                "review_type": user_review.review_type,
                "reviewer_id": user_review.reviewer_id.id,
                "reviewer_group_id": user_review.reviewer_group_id.id,
                "reviewer_field_id": user_review.reviewer_field_id.id,
                "done_by": self.env.user.id,
                "reviewed_date": fields.Datetime.now(),
                "reviewer_ids": [(4, reviewer.id) for reviewer in user_review.reviewer_ids],
                "comment": user_review.comment
            })
        sequences = self._get_previous_sequences_to_reject(self.env.user)
        previous_reviews = self.review_ids.filtered(lambda x: x.sequence in sequences)
        tier_reviews = previous_reviews or self.review_ids
        tier_reviews.write(
            {
                "status": "pending",
            }
        )
        # for review in user_reviews:
        #     rec = self.env[review.model].browse(review.res_id)
        #     rec._notify_rejected_review()
        self._update_counter({"review_deleted": True})

    def reject_to_previous_review_tier(self, tiers=False):
        #  退回上一關
        all_reviews = self.review_ids.filtered(
            lambda r: r.status in ("waiting", "pending")
        )
        my_reviews = all_reviews.filtered(lambda r: self.env.user in r.reviewer_ids)
        my_sequence = min(my_reviews)
        current_review = my_reviews.filtered(lambda r: r.sequence == my_sequence.sequence)
        current_tier_reivews_ids = [current_review.id]
        if self.has_comment:
            wizard = self.env.ref("base_tier_validation.view_comment_wizard")
            return {
                "name": _("Comment"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "comment.wizard",
                "views": [(wizard.id, "form")],
                "view_id": wizard.id,
                "target": "new",
                "context": {
                    "default_res_id": self.id,
                    "default_res_model": self._name,
                    "default_review_ids": current_tier_reivews_ids,
                    "default_validate_reject": "reject_to_previous",
                },
            }
        self._rejected_to_previous_tier()


    def _get_previous_sequences_to_reject(self, user):
        all_reviews = self.review_ids.filtered(
            lambda r: r.status in ("rejected", "approved")
        )
        sequences = []
        previous_sequences = max(all_reviews.mapped("sequence"))
        sequences.append(previous_sequences)
        return sequences

    def _add_tier_validation_review_log(self, node, params):
        str_element = self.env["ir.qweb"]._render(
            "sl_tier_validation.tier_validation_review_log", params
        )
        new_node = etree.fromstring(str_element)
        return new_node

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super().get_view(view_id=view_id, view_type=view_type, **options)

        View = self.env["ir.ui.view"]
        if view_id and res.get("base_model", self._name) != self._name:
            View = View.with_context(base_model_name=res["base_model"])
        if view_type == "form" and not self._tier_validation_manual_config:
            doc = etree.XML(res["arch"])
            params = {}
            all_models = res["models"].copy()
            for node in doc.xpath("/form/sheet"):
                # _add_tier_validation_review_log process
                new_node = self._add_tier_validation_review_log(node, params)
                new_arch, new_models = View.postprocess_and_fields(new_node, self._name)
                for model in new_models:
                    if model in all_models:
                        continue
                    if model not in res["models"]:
                        all_models[model] = new_models[model]
                    else:
                        all_models[model] = res["models"][model]
                new_node = etree.fromstring(new_arch)
                node.append(new_node)
            res["arch"] = etree.tostring(doc)
            res["models"] = frozendict(all_models)
        return res