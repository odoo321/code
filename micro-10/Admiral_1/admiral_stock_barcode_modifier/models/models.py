# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class admiral_stock_barcode_modifier(models.Model):
#     _name = 'admiral_stock_barcode_modifier.admiral_stock_barcode_modifier'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100