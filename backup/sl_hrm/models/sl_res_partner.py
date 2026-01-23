from odoo import models, fields, api


class StarryLordResPartner(models.Model):
    _inherit = 'res.partner'

    full_name = fields.Char(string="全名")
    invoice_address = fields.Char(string="發票地址")
    fax = fields.Char(string="傳真")
    plant_area_line_ids = fields.One2many(comodel_name="sl.plant.area", inverse_name="res_partner_id", string="廠區列表")
    plant_area_id = fields.Many2one(comodel_name="sl.plant.area", string="廠區", ondelete="set null")



    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        self.ensure_one()
        result = {}
        docs = []
        if self.parent_id:
            # 只能選擇所屬公司的廠區
            for plant_area_id in self.env['sl.plant.area'].sudo().search(
                    [('res_partner_id', '=', self.parent_id.id)]):
                docs.append(plant_area_id.id)

        docs.sort()
        # 更新下拉選單
        result['domain'] = {'plant_area_id': [('id', 'in', docs)]}
        return result


