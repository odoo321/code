# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InventoryCheck(models.Model):
    _inherit = 'inventory.check'

    cost_price = fields.Float('Cost Price')

    @api.model
    def add_inventory_check_lines(self, product_id, state, cost_price):

        ProductTemplate = self.env['product.template']
        stock_quant_list = []
        purchase_order_income_list = []
        last_sold_list = []
        last_purchase_list = []
        mrp_product_list = []
        mrp_scheduled_date = []
        po_scheduled_date = []
        product_list = [ProductTemplate.browse(product_id).id]

        product_product_id = \
            self.env['product.product'].search([('name', '=', ProductTemplate.browse(product_id).name)])[0]

        stock_quant_ids = self.env['stock.quant'].search(
            [('product_id', '=', product_product_id.id), ('location_id.usage', '=', 'internal')])

        total = 0
        for stock_quant_id in stock_quant_ids:
            total = total + stock_quant_id.qty

        stock_name = {}
        array_stock_name = []

        if stock_quant_ids:

            for sq in stock_quant_ids:
                location_name = sq.location_id.name_get()[0][1]
                qty = sq.qty

                if stock_name.get(location_name, False):
                    st_qty = stock_name.get(location_name)
                    stock_name.update({location_name: qty + st_qty})
                else:
                    stock_name.update({location_name: qty})
        for key, val in stock_name.iteritems():
            array_stock_name.append(str(val) + ' - ' + key)

        purchase_order_ids = self.env['purchase.order.line'].search(
            [('product_id', '=', product_id), ('state', '=', 'purchase')]).mapped('order_id')

        if purchase_order_ids:
            for po in purchase_order_ids:
                if po.picking_ids[0].state != 'done':
                    po_scheduled_date.append(po.date_planned)
                    purchase_order_income_list.append(po.id)
            purchase_order_income_list = list(set(purchase_order_income_list))
        purchase_order_last = self.env['purchase.order.line'].search(
            [('product_id', '=', product_id), ('state', '=', 'purchase')]).sorted('confirm_date', reverse=True)
        if purchase_order_last:
            last_purchase_list.append(
                (purchase_order_last[0].currency_id.symbol, str(purchase_order_last[0].price_unit)))
        sale_order_last = self.env['sale.order.line'].search(
            [('product_id', '=', product_id), ('state', '=', 'sale')]).sorted('confirm_date', reverse=True)
        if sale_order_last:
            last_sold_list.append((sale_order_last[0].currency_id.symbol, str(sale_order_last[0].price_unit)))
        mrp_production_id = self.env['mrp.production'].search(
            [('product_id', '=', product_id), ('state', '=', 'progress')])
        if mrp_production_id:
            for mo in mrp_production_id:
                mrp_scheduled_date.append(mo.date_planned_start)
                mrp_product_list.append(mo.id)
        status = []
        if state:
            status.append(state)
        max_length = max(len(last_sold_list), len(last_purchase_list), len(product_list), len(array_stock_name),
                         len(purchase_order_income_list), len(mrp_product_list), len(status), len(mrp_scheduled_date),len(po_scheduled_date))
        for count in range(max_length):
            name = stock_quant_id = purchase_order_id = last_sold_price = last_purchase_price = incomming_qty = mr_product_list = mrp_scheduled = state = total_qty = scheduled_date =False
            if count < len(product_list):
                name = product_list[count]
            if count < len(array_stock_name):
                stock_quant_id = array_stock_name[count]
            if count < len(purchase_order_income_list):
                purchase_order_id = purchase_order_income_list[count]
                incomming_quantity = self.env['purchase.order.line'].search([('order_id', '=', purchase_order_id)])
                for line in incomming_quantity:
                    if line.product_id.id == product_id:
                        incomming_qty = line.product_qty
            if count < len(last_sold_list):
                last_sold_price = last_sold_list[count]
            if count < len(last_purchase_list):
                last_purchase_price = last_purchase_list[count]
            if count < len(mrp_product_list):
                mr_product_list = mrp_product_list[count]
            if count < len(mrp_scheduled_date):
                mrp_scheduled = mrp_scheduled_date[count]
            if count < len(status):
                state = status[count]
            if count < 1:
                total_qty = total
            if count < len(po_scheduled_date):
                scheduled_date = po_scheduled_date[count]

            vals = {
                'name': name,
                'string_stock_quant': stock_quant_id,
                'purchase_order_id': purchase_order_id,
                'incomming_quantity': incomming_qty,
                'last_sold_price': last_sold_price and last_sold_price[0] + " " + last_sold_price[1] or '',
                'last_purchase_price': last_purchase_price and last_purchase_price[0] + " " + last_purchase_price[
                    1] or '',
                'cost_price': cost_price,
                'mo_scheduled_date': mrp_scheduled,
                'mrp_production_id': mr_product_list,
                'status': state,
                'qty_on_hand': total_qty,
                'scheduled_date': scheduled_date,
            }
            self.create(vals)

    @api.model
    def create_new_inventory(self, qty, product_id, is_bom):
        self.search([]).unlink()
        if product_id:
            product_id = int(product_id)

        product = self.env['product.template'].browse(product_id)
        if qty:
            total_qty = float(qty)
        if product:
            boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_id)])
            product_template_ids = [{'product_id': product_id}]
            available_bom = []
            total_cost = 0
            if is_bom:
                for bom in boms:
                    for line in bom.bom_line_ids:

                        if line.product_id.qty_available < line.product_qty * total_qty:
                            status = 'not_available'
                            available_bom.append('not_available')
                        else:
                            status = 'available'
                            available_bom.append('available')

                        product_template_id = line.product_id.product_tmpl_id and line.product_id.product_tmpl_id.id
                        if product_template_id not in product_template_ids:
                            cost_price = line.product_id.product_tmpl_id.standard_price
                            product_template_ids.append({'product_id': product_template_id, 'state_name': status ,'cost_price': cost_price})
                            total_cost += cost_price * line.product_qty

            for product_template_id in product_template_ids:

                if product.id == product_template_id.get('product_id'):
                    if available_bom:
                        if 'not_available' in available_bom:
                            product_template_id.update({'state_name': 'insufficient _to_produce', 'cost_price' : total_cost})

                        elif available_bom[-1] == 'None':
                            product_template_id.update({'state_name': '', 'cost_price' : total_cost})
                        else:
                            product_template_id.update({'state_name': 'sufficient_to_produce', 'cost_price' : total_cost})
                        self.add_inventory_check_lines(product_template_id.get('product_id'),
                                                       product_template_id.get('state_name'), product_template_id.get('cost_price'))
                    else:
                        product_template_id.update({'state_name': '','cost_price' : total_cost})
                        self.add_inventory_check_lines(product_template_id.get('product_id'),
                                                       product_template_id.get('state_name'), product_template_id.get('cost_price'))
                else:
                    self.add_inventory_check_lines(product_template_id.get('product_id'),
                                                   product_template_id.get('state_name'), product_template_id.get('cost_price'))

        return True

InventoryCheck()
