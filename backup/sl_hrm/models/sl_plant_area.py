from odoo import models, fields, api


class StarryLordPlantArea(models.Model):
    _name = 'sl.plant.area'
    _description = '廠區'

    name = fields.Char(string="名稱", required=True)
    code = fields.Char(string="代碼", required=True)
    res_partner_id = fields.Many2one(comodel_name="res.partner", inverse_name="plant_area_line_ids", string="上級公司")
