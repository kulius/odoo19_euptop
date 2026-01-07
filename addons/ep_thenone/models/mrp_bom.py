# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    old_product_code = fields.Char(
        string='舊產品編號',
        related='product_id.old_product_code',
        store=True,
        readonly=True,
        help='產品的舊編號'
    )
    supplier_code = fields.Char(
        string='供應商編號',
        related='product_id.supplier_code',
        store=True,
        readonly=True,
        help='供應商提供的產品編號'
    )
