# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    old_product_code = fields.Char(
        string='舊產品編號',
        help='產品的舊編號，用於搜尋和識別'
    )
    supplier_code = fields.Char(
        string='供應商編號',
        help='供應商提供的產品編號'
    )

class ProductProduct(models.Model):
    _inherit = 'product.product'

    