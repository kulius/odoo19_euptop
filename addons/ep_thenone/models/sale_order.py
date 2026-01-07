# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    old_product_code = fields.Char(
        string='舊產品編號',
        related='product_id.old_product_code',
        store=True,
        readonly=True,
        help='產品的舊編號'
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """當選擇產品時，自動帶出舊產品編號"""
        result = super()._onchange_product_id()
        if self.product_id:
            self.old_product_code = self.product_id.old_product_code
        else:
            self.old_product_code = False
        return result
