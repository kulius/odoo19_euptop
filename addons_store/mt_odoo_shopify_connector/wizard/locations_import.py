# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, _, api, fields


class ShopifyLocationsImport(models.Model):
    _name = 'shopify.locations.import'
    _description = 'Shopify Locations Import'

    shopify_instance_id = fields.Many2one('shopify.instance')

    def import_shopify_locations(self):
        self.env['shopify.location'].import_locations(self.shopify_instance_id)
        return self.env['ir.actions.act_window']._for_xml_id("mt_odoo_shopify_connector.action_shopify_location_view")

    def view_shopify_locations(self):
        return self.env['ir.actions.act_window']._for_xml_id("mt_odoo_shopify_connector.action_shopify_location_view")
    
    @api.model
    def default_get(self, fields):
        res = super(ShopifyLocationsImport, self).default_get(fields)
        try:
            instance = self.env['shopify.instance'].search([])[0]
        except Exception as error:
            raise UserError(_("Please set up and configure a Shopify instance."))

        if instance:
            res['shopify_instance_id'] = instance.id

        return res
