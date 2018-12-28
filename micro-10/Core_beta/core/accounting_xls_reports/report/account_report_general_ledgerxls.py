# -*- coding: utf-8 -*-
import re
import StringIO
import cStringIO
import base64
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
import xlwt
from xlwt import *
from odoo import fields, api, models
from odoo.tools.translate import _
from odoo.tools.misc import formatLang               
from odoo.exceptions import UserError

class account_report_general_ledger(models.TransientModel):
    
    _inherit="account.report.general.ledger"

    xls_theme_id = fields.Many2one('color.xls.theme','XLS Theme')
    
    @api.multi    
    def print_ledgerreport_xls(self):
        current_obj = self

        data = {}
        init_balance = self.initial_balance
        sortby = self.sortby
        display_account = self.display_account
        target_move = self.target_move
      
        codes = []
       
        if self.journal_ids:
            codes = [journal.code for journal in self.env['account.journal'].search([('id', 'in', self.journal_ids.ids)])]
        
        accounts = self.env['account.account'].search([])
        
        data['form'] = self.read(['date_from',  'date_to',  'journal_ids','target_move'])[0]
        if self.initial_balance and not self.date_from:
           raise UserError(_("You must define a Start Date"))  
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        accounts_res = self.env['report.account.report_generalledger'].with_context(data['form'].get('used_context',{}))._get_account_move_entry(accounts, init_balance, sortby, display_account)
        target_move = dict(self.env['account.report.general.ledger'].fields_get(allfields=['target_move'])['target_move']['selection'])[current_obj.target_move]
        sortby = dict(self.env['account.report.general.ledger'].fields_get(allfields=['sortby'])['sortby']['selection'])[current_obj.sortby]
        display_account = dict(self.env['account.report.general.ledger'].fields_get(allfields=['display_account'])['display_account']['selection'])[current_obj.display_account]        
       
        fp = cStringIO.StringIO()
        wb = xlwt.Workbook(encoding='utf-8')

        header_style = xlwt.XFStyle()
        font = xlwt.Font()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        bg_color = current_obj.xls_theme_id.bg_color or 'black'
        pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
        font.height = int(current_obj.xls_theme_id.font_size)
        font.bold = current_obj.xls_theme_id.font_bold
        font.italic = current_obj.xls_theme_id.font_italic
        font_color = current_obj.xls_theme_id.font_color or 'white'
        font.colour_index = xlwt.Style.colour_map[font_color]
        header_style.pattern = pattern
        header_style.font = font
        al3 = Alignment()
        al3.horz = current_obj.xls_theme_id.header_alignment or 0x02
        header_style.alignment = al3

       
        column_header_style = xlwt.XFStyle()
        font = xlwt.Font()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        bg_color = current_obj.xls_theme_id.column_bg_color or 'red'
        pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
        font.height = int(current_obj.xls_theme_id.column_font_size)
        font.bold = current_obj.xls_theme_id.column_font_bold
        font.italic = current_obj.xls_theme_id.column_font_italic
        font_color = current_obj.xls_theme_id.column_font_color or 'white'
        font.colour_index = xlwt.Style.colour_map[font_color]
        column_header_style.pattern = pattern
        column_header_style.font = font
        al3 = Alignment()
        al3.horz = current_obj.xls_theme_id.column_header_alignment
        column_header_style.alignment = al3


        body_header_style = xlwt.XFStyle()
        font = xlwt.Font()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        bg_color = current_obj.xls_theme_id.body_bg_color or 'gold'
        pattern.pattern_fore_colour = xlwt.Style.colour_map[bg_color]
        font.height = int(current_obj.xls_theme_id.body_font_size)
        font.bold = current_obj.xls_theme_id.body_font_bold
        font.italic = current_obj.xls_theme_id.body_font_italic
        font_color = current_obj.xls_theme_id.body_font_color or 'white'
        font.colour_index = xlwt.Style.colour_map[font_color]
        body_header_style.pattern = pattern
        body_header_style.font = font
        al3 = Alignment()
        al3.horz = current_obj.xls_theme_id.body_header_alignment
        body_header_style.alignment = al3


        final_arr_data = {}
        filename = 'General-Ledger-Report.xls'
        ledger_obj = self.pool.get("account.report.general.ledger")
        worksheet = wb.add_sheet("GENERAL-LEDGER" + ".xls")
        header = current_obj.company_id.name+':'+'General Ledger'
        worksheet.write_merge(0, 0, 0, 8, header, header_style)
        journal_names = []
        journal_string = ''
        for journal_name in self.env['account.journal'].browse(data['form']['journal_ids']):
                journal_names.append(journal_name.code)
                journal_string += journal_name.code + ','
        

        header_header_list = ["Journals:", "Display Account:", "Sorted By:", "Target Moves:"]
        header_data_list = [journal_string, display_account, sortby, target_move]
       
        header_data = dict(zip(header_header_list, header_data_list))
        row = col = 1
        for key in header_header_list:
            worksheet.write(row, col, key, column_header_style)
            row+=1
            worksheet.write(row, col, header_data[key], body_header_style)
            #if key == 'Filter By:' and header_data[key] in ['Filtered by date', 'Filtered by period']:
            #    per_row = row+1
            #    for per in period:
            #        worksheet.write(per_row, col, per, body_header_style)
            #        per_row+=1
            row-=1
            col+=1
        # sending row cursor after 3 new rows            
        row +=6
        col = 1
        
        body_header_list = ["DATE", "JRNL", "Partner", "Ref", "Move", "Entry Label", "Debit", "Credit", "Balance"]
        for header in body_header_list:
            worksheet.write(row, col, header, column_header_style)
            col+=1
   
        row+=1
        col=1
                        
        tot_currency = 0.0
        company_name = self.company_id.name
        
        for i in range(1,15):
              column = worksheet.col(i)
              column.width = 225 * 30
        body_body_list = ['ldate', 'lcode', 'partner_name', 'lref', 'move_name', 'lname', 'debit', 'credit', 'balance']
		
        for account in accounts_res:
            
            col = 1
            row+=1
            worksheet.write(row, col, account['code'], body_header_style)
            col+=1
            worksheet.write(row, col, account['name'], body_header_style)
            col+=5
            worksheet.write(row, col, formatLang(self.env, account['debit'], currency_obj=current_obj.company_id.currency_id), body_header_style)
            col+=1 
            worksheet.write(row, col, formatLang(self.env, account['credit'], currency_obj=current_obj.company_id.currency_id), body_header_style)
            col+=1
            worksheet.write(row, col, formatLang(self.env, account['balance'], currency_obj=current_obj.company_id.currency_id), body_header_style)
          
            for line in account['move_lines']:
                    col =1
                    row+=1
                    for item in body_body_list:
                        if item == 'debit':
                           line[item] = formatLang(self.env, line[item], currency_obj=current_obj.company_id.currency_id)
                        elif item == 'credit':
                           line[item] = formatLang(self.env, line[item], currency_obj=current_obj.company_id.currency_id)
                        elif item == 'balance':
                           line[item] = formatLang(self.env, line[item], currency_obj=current_obj.company_id.currency_id)

                        worksheet.write(row, col, line[item], body_header_style)

                        col += 1
        wb.save(fp)
        out = base64.encodestring(fp.getvalue())
        final_arr_data = {}
        final_arr_data['file_stream'] = out
        final_arr_data['name'] = filename
    
        create_id = self.env['account.report.view'].create(final_arr_data)
        return {
                'nodestroy': True,
                'res_id': create_id.id,
                'name': filename,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.report.view',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }
       
        
