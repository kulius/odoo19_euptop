from odoo import models, api


class OvertimeExchangeConsentReport(models.AbstractModel):
    _name = 'report.sl_hrm.overtime_exchange_consent_document'
    _description = '例假日與休息日調移同意書報表'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        獲取報表數據
        """
        docs = self.env['starrylord.overtime.exchange.consent'].browse(docids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'starrylord.overtime.exchange.consent',
            'docs': docs,
            'data': data,
        }
