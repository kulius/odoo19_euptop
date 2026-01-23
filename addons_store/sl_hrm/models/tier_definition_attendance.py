# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class TierDefinition(models.Model):
    _inherit = 'tier.definition'

    @api.model
    def _get_tier_validation_model_names(self):
        """註冊補卡申請模型到簽核系統"""
        res = super(TierDefinition, self)._get_tier_validation_model_names()
        res.append('sl.attendance.repair')
        return res


class StarryLordAttendanceRepairValidation(models.Model):
    """補卡申請簽核邏輯"""
    _name = 'sl.attendance.repair'
    _inherit = ['sl.attendance.repair', 'tier.validation']
    
    # 簽核狀態設定
    _state_from = ['f_approve']  # 從此狀態開始需要簽核
    _state_to = ['confirmed']  # 簽核通過後的狀態
    _cancel_state = 'refused'  # 簽核拒絕後的狀態
    _tier_validation_manual_config = False  # 自動注入簽核UI元素

    # 簽核相關欄位
    is_current_user = fields.Boolean(
        compute='_compute_is_current_user',
        string='判斷是否為自己的單據',
        store=False
    )
    is_readonly = fields.Boolean(
        compute='_compute_is_readonly',
        string='是否唯讀'
    )

    @api.depends('user_id')
    def _compute_is_current_user(self):
        """判斷當前用戶是否為申請人"""
        for record in self:
            record.is_current_user = (record.user_id.id == self.env.uid)

    def _compute_is_readonly(self):
        """計算表單是否唯讀"""
        for record in self:
            is_readonly = True
            # 草稿狀態可編輯
            if record.state == 'draft':
                is_readonly = False
            record.is_readonly = is_readonly

    def to_f_approve(self):
        """送簽：觸發簽核流程"""
        super(StarryLordAttendanceRepairValidation, self).to_f_approve()
        self.request_validation()

    def to_draft(self):
        """退回草稿：清除所有簽核記錄"""
        super(StarryLordAttendanceRepairValidation, self).restart_validation()
        super(StarryLordAttendanceRepairValidation, self).to_draft()

    def restart_validation(self):
        """重啟簽核流程"""
        super(StarryLordAttendanceRepairValidation, self).restart_validation()
        super(StarryLordAttendanceRepairValidation, self).to_draft()

    def _validate_tier(self, tiers=False):
        """簽核批准：當審批人點擊「批准」時觸發
        
        base_tier_validation 會自動記錄到 tier.review：
        - done_by: 審批人
        - reviewed_date: 審批時間  
        - status: 'approved'
        """
        super(StarryLordAttendanceRepairValidation, self)._validate_tier(tiers)
        
        if self.validated:
            self.agree()
            self._send_approval_notification()

    def _rejected_tier(self, tiers=False):
        """簽核拒絕：當審批人點擊「拒絕」時觸發
        
        base_tier_validation 會自動記錄到 tier.review：
        - done_by: 拒絕人
        - reviewed_date: 拒絕時間
        - status: 'rejected'  
        """
        super(StarryLordAttendanceRepairValidation, self)._rejected_tier(tiers)
        
        # 如果被拒絕了
        if self.rejected:
            self.to_refused()
            
            # 發送退回通知給申請人
            self._send_rejection_notification(tiers)

    def _send_approval_notification(self):
        """發送審核通過通知給申請人"""
        for rec in self:
            if not rec.user_id:
                continue
                
            # 建立收件匣通知
            notification_ids = [(0, 0, {
                'res_partner_id': rec.user_id.partner_id.id,
                'notification_type': 'inbox'
            })]
            
            # 發送訊息
            self.env['mail.message'].create({
                'message_type': 'notification',
                'body': f"出勤異常說明單 [{rec.name}] 已通過審核。",
                'subject': '補卡申請審核通過通知',
                'record_name': f'補卡申請審核通過通知 {rec.name}',
                'partner_ids': [(4, rec.user_id.partner_id.id)],
                'model': rec._name,
                'res_id': rec.id,
                'notification_ids': notification_ids,
                'author_id': self.env['res.users'].search([
                    ('active', '=', False),
                    ('login', '=', '__system__')
                ], limit=1).partner_id.id
            })

    def _send_rejection_notification(self, tiers=False):
        """發送審核退回通知給申請人"""
        for rec in self:
            if not rec.user_id:
                continue
                
            # 取得退回意見
            comment = ''
            if tiers and tiers.mapped('comment'):
                comment = tiers.mapped('comment')[0]
            
            # 建立收件匣通知
            notification_ids = [(0, 0, {
                'res_partner_id': rec.user_id.partner_id.id,
                'notification_type': 'inbox'
            })]
            
            # 發送訊息
            body = f"出勤異常說明單 [{rec.name}] 被退回"
            if comment:
                body += f"<br/>退回意見：{comment}"
            body += "。"
            
            self.env['mail.message'].create({
                'message_type': 'notification',
                'body': body,
                'subject': '補卡申請退回通知',
                'record_name': f'補卡申請退回通知 {rec.name}',
                'partner_ids': [(4, rec.user_id.partner_id.id)],
                'model': rec._name,
                'res_id': rec.id,
                'notification_ids': notification_ids,
                'author_id': self.env['res.users'].search([
                    ('active', '=', False),
                    ('login', '=', '__system__')
                ], limit=1).partner_id.id
            })

    def _notify_accepted_reviews(self):
        """覆寫以避免預設通知（我們使用自訂通知）"""
        pass

    def _notify_rejected_review(self):
        """覆寫以避免預設通知（我們使用自訂通知）"""
        pass

    def _notify_restarted_review(self):
        """覆寫以避免預設通知（我們使用自訂通知）"""
        pass

    def _notify_accepted_reviews_body(self):
        """自訂審核通過訊息內容"""
        has_comment = self.review_ids.filtered(
            lambda r: (self.env.user in r.reviewer_ids) and r.comment
        )
        if has_comment:
            comment = has_comment.mapped('comment')[0]
            return _('補卡申請簽核已通過。(%s)') % comment
        return _('補卡申請簽核已通過')

    def _allow_to_remove_reviews(self, values):
        """決定是否需要清除簽核記錄"""
        self.ensure_one()
        state_to = values.get(self._state_field)
        if not state_to:
            return False
        state_from = self[self._state_field]
        # 如果狀態改回 _state_from（例如從 confirmed 改回 f_approve）
        if state_to in self._state_from and state_from not in self._state_from:
            return True
        return False
