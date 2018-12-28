# -*- coding: utf-8 -*-

from odoo import fields, models, api

class Meeting(models.Model):
    _inherit = 'calendar.event'
    
    number = fields.Char(
        string="Appointment ID",
        readonly=True
    )
    customer_name = fields.Many2one(
        'res.partner',
        string='Name',
        copy=False,
    )
    email = fields.Char(
        string='Email',
        copy=False,
    )
    phone = fields.Char(
        string='Phone',
        copy=False,
    )
    slot = fields.Char(
        string='Time Slot',
        copy=False,
    )

    @api.model
    def create(self, vals):
        result = super(Meeting, self).create(vals)
        for record in result:
            record.number = self.env['ir.sequence'].next_by_code('calendar.event')
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
