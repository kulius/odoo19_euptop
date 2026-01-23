from odoo import api, fields, models
from odoo.exceptions import UserError


class StarryLordHolidayApplyValidation(models.Model):
    _name = 'starrylord.holiday.apply'
    _inherit = ['starrylord.holiday.apply', 'tier.validation']
    _description = '請休假申請'
    _state_from = ["f_approve"]
    _state_to = ['agree']
    _cancel_state = 'refused'
    _allow_remove_state = ['cancel']

    _tier_validation_manual_config = False

    is_current_user = fields.Boolean(compute='_compute_is_current_user', string="判斷是否為自己的單據", store=False)
    is_readonly = fields.Boolean(compute='_compute_is_readonly', string='是否唯讀')

    def _compute_is_readonly(self):
        is_readonly = True
        for record in self:
            if self.state in ['draft']:
                is_readonly = False
            # if record.create_uid.id == self.env.uid:
            #     can_edit = True
            if self.state in ['f_approve'] and self.can_review and record.create_uid.id == self.env.uid:
                is_readonly = False
            record.is_readonly = is_readonly

    @api.depends('user_id')
    def _compute_is_current_user(self):
        for record in self:
            record.is_current_user = (record.user_id.id == self.env.uid)

    def to_draft(self):
        super(StarryLordHolidayApplyValidation, self).restart_validation()
        super(StarryLordHolidayApplyValidation, self).to_draft()

    def to_f_approve(self):
        super(StarryLordHolidayApplyValidation, self).to_f_approve()
        self.request_validation()

    def to_cancel(self):
        super(StarryLordHolidayApplyValidation, self).to_cancel()

    def _validate_tier(self, tiers=False):
        super(StarryLordHolidayApplyValidation, self)._validate_tier(tiers)
        # 如果查無任何pending(待辦)的tier, 則直接同意(agree)
        if self.validated:
            self.agree()
            # 發送通知給申請人
            # group_xml_id = 'sl_account.group_sl_payment_record_manager'  # 替换为你的群组XML ID
            user_ids = self.env['res.users'].search([('id', '=', self.user_id.id)]).ids

            notification_ids = []
            for user_id in user_ids:
                user = self.env['res.users'].browse(user_id)
                notification_ids.append((0, 0, {
                    'res_partner_id': user.partner_id.id,
                    'notification_type': 'inbox'
                }))
            self.env['mail.message'].create({
                'message_type': "notification",
                'body': f"請假單 [{self.name}] 已通過審核。",
                'subject': "請假單審核通過通知",
                'record_name': '請假單審核通過通知 ' + self.name,
                'partner_ids': [(4, user.partner_id.id) for user in self.env['res.users'].browse(user_ids)],
                'model': self._name,
                'res_id': self.id,
                'notification_ids': notification_ids,
                'author_id': self.env['res.users'].search([('active', '=', False), ('login', '=', '__system__')]).partner_id.id
            })

    def _rejected_tier(self, tiers=False):
        super(StarryLordHolidayApplyValidation, self)._rejected_tier(tiers)
        # super(StarryLordHolidayApplyValidation, self).to_refused()
        if self.rejected:
            self.to_refused()

            # 發送通知給申請人
            # group_xml_id = 'sl_account.group_sl_payment_record_manager'  # 替换为你的群组XML ID
            user_ids = self.env['res.users'].search([('id', '=', self.user_id.id)]).ids

            notification_ids = []
            for user_id in user_ids:
                user = self.env['res.users'].browse(user_id)
                notification_ids.append((0, 0, {
                    'res_partner_id': user.partner_id.id,
                    'notification_type': 'inbox'
                }))
            comment = tiers.mapped('comment')[0]
            self.env['mail.message'].create({
                'message_type': "notification",
                'body': f"請假單 [{self.name}] 被退回<br/>意見：{comment if comment else ''}。",
                'subject': "請假單退回通知",
                'record_name': '請假單退回通知 ' + self.name,
                'partner_ids': [(4, user.partner_id.id) for user in self.env['res.users'].browse(user_ids)],
                'model': self._name,
                'res_id': self.id,
                'notification_ids': notification_ids,
                'author_id': self.env['res.users'].search([('active', '=', False), ('login', '=', '__system__')]).partner_id.id
            })

    def restart_validation(self):
        super(StarryLordHolidayApplyValidation, self).restart_validation()
        super(StarryLordHolidayApplyValidation, self).to_draft()

    def _notify_accepted_reviews(self):
        pass

    def _notify_rejected_review(self):
        pass

    def _notify_restarted_review(self):
        pass

    # 設定審核通過通知訊息
    def _notify_accepted_reviews_body(self):
        has_comment = self.review_ids.filtered(
            lambda r: (self.env.user in r.reviewer_ids) and r.comment
        )
        if has_comment:
            comment = has_comment.mapped("comment")[0]
            return _("請假單簽核已通過. (%s)") % comment
        return _("請假單簽核已通過")

    def _allow_to_remove_reviews(self, values):
        """Method for deciding whether the elimination of revisions is necessary."""
        self.ensure_one()
        state_to = values.get(self._state_field)
        if not state_to:
            return False
        state_from = self[self._state_field]
        # If you change to _cancel_state
        if state_to in (self._allow_remove_state):
            return True
        # If it is changed to _state_from and it was not in _state_from
        if state_to in self._state_from and state_from not in self._state_from:
            return True
        return False

class TierDefinition(models.Model):
    _inherit = "tier.definition"

    @api.model
    def _get_tier_validation_model_names(self):
        res = super(TierDefinition, self)._get_tier_validation_model_names()
        res.append("starrylord.holiday.apply")
        return res
