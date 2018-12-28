# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.workcenter'

    uom_id = fields.Many2one('product.uom', string='UOM')