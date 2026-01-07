# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    old_product_code = fields.Char(
        string='舊產品編號',
        related='product_id.old_product_code',
        store=True,
    )
    supplier_code = fields.Char(
        string='供應商編號',
        related='product_id.supplier_code',
        store=True,
    )

