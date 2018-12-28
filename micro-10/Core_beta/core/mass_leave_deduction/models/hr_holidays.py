# -*- coding: utf-8 -*-

import pytz
import time
import datetime
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, exceptions, fields, models, _


class HrHoliday(models.Model):
    _inherit = 'hr.holidays'


    is_deducted = fields.Boolean('Deducted')

    @api.constrains('date_from', 'date_to', 'holiday_status_id')
    def _check_public_holiday_leave(self):
        for rec in self:
            if rec.type == 'remove':
                if rec.holiday_status_id and rec.holiday_status_id.id and rec.holiday_status_id.count_days_by:
                    if rec.holiday_status_id.count_days_by == 'working_days_only':
                        if rec.date_from and rec.date_to:
                            diff_day = rec._check_holiday_to_from_dates(rec.date_from, rec.date_to, rec.employee_id.id)
                            if diff_day == 0:
                                raise exceptions.ValidationError(_('You are not able to apply leave Request on Holiday.!'))

    @api.constrains('employee_id')
    def _check_cessation_date_for_leave(self):
        '''
        The method used to check cessation date before Leave request.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        for rec in self:
            if not rec.holiday_status_id.mass_leave_deduction:
                if rec.employee_id and rec.employee_id.cessation_date and rec.date_from and (
                        rec.employee_id.cessation_date < rec.date_from):
                    raise ValidationError(_('You can not request a leave over your cessation date!'))

    @api.constrains('holiday_status_id', 'employee_id', 'date_from', 'date_to')
    def _check_employee_leave(self):
        if self._context is None:
            self._context = {}
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
                qualify_date = from_date - relativedelta(days=rec.holiday_status_id.no_of_days)
                if qualify_date < datetime.datetime.today().date():
                    raise ValidationError(
                        _('You have to apply leave before  %d days!' % (rec.holiday_status_id.no_of_days)))
        return True

    @api.constrains('holiday_status_id', 'half_day')
    def _check_half_day_for_leave(self):
        '''
        The method used to Validate for Half Day Type Leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        for rec in self:
            if rec.half_day == True:
                if rec.holiday_status_id and rec.holiday_status_id.id and rec.holiday_status_id.allow_half_day == False and not rec.holiday_status_id.mass_leave_deduction:
                    raise ValidationError(_('You are not able to send half leave Request for this leave type!'))

    @api.constrains('holiday_status_id', 'employee_id')
    def _check_sg_maternity_leave_16_weeks(self):
        '''
        The method used to Validate for Maternity Leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name in ['ML16', 'ML15', 'ML8', 'ML4']:
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if rec.employee_id and rec.employee_id.id and rec.employee_id.join_date:
                        depends_ids = self.env['dependents'].search(
                            [('employee_id', '=', rec.employee_id.id), ('birth_date', '=', rec.child_birthdate),
                             ('relation_ship', 'in', ['son', 'daughter'])])
                        for depends_id in depends_ids:
                            if rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True and depends_id.nationality and depends_id.nationality.name == 'Singapore':
                                joining_date = datetime.datetime.strptime(rec.employee_id.join_date,
                                                                          DEFAULT_SERVER_DATE_FORMAT).date()
                                qualify_date = joining_date + relativedelta(months=3)
                                if datetime.datetime.today().date() < qualify_date:
                                    raise ValidationError(_(
                                        'Not Qualified in Joining date! \n Employee must have worked in the company for a continuous duration of at least 3 months!'))
                                from_date = datetime.datetime.strptime(rec.date_from,
                                                                       DEFAULT_SERVER_DATETIME_FORMAT).date()
                                two_month_date = from_date - relativedelta(months=2)
                                if two_month_date < datetime.datetime.today().date():
                                    raise ValidationError(_(
                                        'Warning! \n Maternity Leave request should be submitted 2 months prior to the requested date.!'))
                            else:
                                raise ValidationError(_('Warning! \n Child is not Singapore citizen!'))
                        else:
                            raise ValidationError(_('You are not able to apply Request for this Maternity leave!'))

    @api.constrains('holiday_status_id', 'employee_id', 'date_from', 'date_to', 'child_birthdate')
    def _check_paternity_leave(self):
        '''
        The method used to Validate for Paternity Leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        today_date = datetime.datetime.today().date()
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'PL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if not rec.employee_id.dependent_ids:
                        raise ValidationError(_(
                            'No Child Depends found! \n Please Add Child Detail in Depend list for this employee Profile !'))
                    depends_ids = self.env['dependents'].search(
                        [('employee_id', '=', rec.employee_id.id), ('birth_date', '=', rec.child_birthdate),
                         ('relation_ship', 'in', ['son', 'daughter'])])
                    if len(depends_ids.ids) == 0:
                        raise ValidationError(
                            _('No Child found! \n No Child found for the Birth date %s !' % (rec.child_birthdate)))
                    for depends_id in depends_ids:
                        if rec.employee_id and rec.employee_id.id and rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True and rec.employee_id.join_date and depends_ids.nationality and depends_id.nationality.name == 'Singapore':
                            joining_date = datetime.datetime.strptime(rec.employee_id.join_date,
                                                                      DEFAULT_SERVER_DATE_FORMAT).date()
                            qualify_date = joining_date + relativedelta(months=3)
                            if today_date >= qualify_date:
                                child_birth_date = datetime.datetime.strptime(rec.child_birthdate,
                                                                              DEFAULT_SERVER_DATE_FORMAT).date()
                                from_date = datetime.datetime.strptime(rec.date_from,
                                                                       DEFAULT_SERVER_DATETIME_FORMAT).date()
                                to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
                                qualify_date = child_birth_date + relativedelta(years=1)
                                #                         child_bd_week = child_birth_date.isocalendar()
                                sixteen_weeks_later = child_birth_date + relativedelta(weeks=16)
                                before_qualify_date = from_date - relativedelta(weeks=2)
                                if to_date > qualify_date:
                                    raise ValidationError(_(
                                        'Not Qualified in Joining date! \n Employee must have worked in the company for a continuous duration of at least 3 months!'))
                                if to_date > sixteen_weeks_later:
                                    raise ValidationError(_(
                                        'Warning! \n Paternity leave should be taken within 16 weeks of the child\'s birth date!'))
                                if before_qualify_date < today_date:
                                    raise ValidationError(_(
                                        'Warning! \n Paternity Leave request should be submitted 2 weeks prior to the requested date.!'))
                            else:
                                raise ValidationError(_(
                                    'Not Qualified in Joining date! \n Employee must have worked in the company for a continuous duration of at least 3 months!'))
                        else:
                            raise ValidationError(_('Warning! \n Child is not Singapore citizen!'))

    @api.constrains('holiday_status_id', 'employee_id', 'date_to', 'child_birthdate')
    def _check_unpaid_infant_care_leave(self):
        '''
        The method used to Validate for Unpaid Infant Care Leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        date_rec = []
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'UICL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if not rec.employee_id.dependent_ids:
                        raise ValidationError(_(
                            'No Child Depends found! \n Please Add Child Detail in Depend list for this employee Profile !'))
                    depends_ids = self.env['dependents'].search(
                        [('employee_id', '=', rec.employee_id.id), ('birth_date', '=', rec.child_birthdate),
                         ('relation_ship', 'in', ['son', 'daughter'])])
                    if len(depends_ids.ids) == 0:
                        raise ValidationError(
                            _('No Child found! \n No Child found for the Birth date %s !' % (rec.child_birthdate)))
                    for depends_id in depends_ids:
                        if rec.employee_id and rec.employee_id.id and rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True and depends_id.nationality and depends_id.nationality.name == 'Singapore':
                            if rec.employee_id.join_date:
                                joining_date = datetime.datetime.strptime(rec.employee_id.join_date,
                                                                          DEFAULT_SERVER_DATE_FORMAT).date()
                                qualify_date = joining_date + relativedelta(months=3)
                                if datetime.datetime.today().date() >= qualify_date:
                                    child_birth_date = datetime.datetime.strptime(rec.child_birthdate,
                                                                                  DEFAULT_SERVER_DATE_FORMAT).date()
                                    to_date = datetime.datetime.strptime(rec.date_to,
                                                                         DEFAULT_SERVER_DATETIME_FORMAT).date()
                                    qualify_date = child_birth_date + relativedelta(years=2)
                                    if to_date > qualify_date:
                                        raise ValidationError(_('Warning! \n Child is not Singapore citizen!'))
                                else:
                                    raise ValidationError(_(
                                        'Not Qualified in Joining date! \n Employee must have worked in the company for a continuous duration of at least 3 months!'))
                        else:
                            raise ValidationError(
                                _('You are not able to apply Request for this Unpaid Infant Care leave!'))

    @api.constrains('holiday_status_id', 'employee_id', 'date_to', 'child_birthdate')
    def _check_Paid_child_care_leave(self):
        '''
        The method used to Validate for Paid Child Care Leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        today_date = datetime.datetime.today().date()
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'CCL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if not rec.employee_id.dependent_ids:
                        raise ValidationError(_(
                            'No Child Depends found! \n Please Add Child Detail in Depend list for this employee Profile !'))
                    depends_ids = self.env['dependents'].search(
                        [('employee_id', '=', rec.employee_id.id), ('birth_date', '=', rec.child_birthdate),
                         ('relation_ship', 'in', ['son', 'daughter'])])
                    if len(depends_ids.ids) == 0:
                        raise ValidationError(
                            _('No Child found! \n No Child found for the Birth date %s !' % (rec.child_birthdate)))
                    for depends_id in depends_ids:
                        if rec.employee_id and rec.employee_id.id and rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True and rec.employee_id.join_date and depends_id.nationality and depends_id.nationality.name == 'Singapore':
                            joining_date = datetime.datetime.strptime(rec.employee_id.join_date,
                                                                      DEFAULT_SERVER_DATE_FORMAT).date()
                            qualify_date = joining_date + relativedelta(months=3)
                            if today_date >= qualify_date:
                                child_birth_date = datetime.datetime.strptime(rec.child_birthdate,
                                                                              DEFAULT_SERVER_DATE_FORMAT).date()
                                to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
                                qualify_date = child_birth_date + relativedelta(years=7)
                                if to_date > qualify_date:
                                    raise ValidationError(
                                        _('You are not able to apply Request for this Paid Child Care leave!'))
                            else:
                                raise ValidationError(
                                    _('You are not able to apply Request for this Paid Child Care leave!'))
                        else:
                            raise ValidationError(
                                _('You are not able to apply Request for this Paid Child Care leave!'))

    @api.constrains('holiday_status_id', 'employee_id', 'date_to', 'child_birthdate')
    def _check_extended_child_care_leave(self):
        '''
        The method used to Validate for Extended Child Care Leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self.context = {}
        date_rec = []
        today_date = datetime.datetime.today().date()
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'ECL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if not rec.employee_id.dependent_ids:
                        raise ValidationError(_(
                            'No Child Depends found! \n Please Add Child Detail in Depend list for this employee Profile !'))
                    depends_ids = self.env['dependents'].search(
                        [('employee_id', '=', rec.employee_id.id), ('birth_date', '=', rec.child_birthdate),
                         ('relation_ship', 'in', ['son', 'daughter'])])
                    if len(depends_ids.ids) == 0:
                        raise ValidationError(
                            _('No Child found! \n No Child found for the Birth date %s !' % (rec.child_birthdate)))
                    for depends_id in depends_ids:
                        if rec.employee_id and rec.employee_id.id and rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True and rec.employee_id.join_date and depends_id.nationality and depends_id.nationality.name == 'Singapore':
                            joining_date = datetime.datetime.strptime(rec.employee_id.join_date,
                                                                      DEFAULT_SERVER_DATE_FORMAT).date()
                            qualify_date = joining_date + relativedelta(months=3)
                            if today_date >= qualify_date:
                                child_birth_date = datetime.datetime.strptime(rec.child_birthdate,
                                                                              DEFAULT_SERVER_DATE_FORMAT).date()
                                to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
                                qualify_date_from = child_birth_date + relativedelta(years=7)
                                qualify_date_to = child_birth_date + relativedelta(years=12)
                                if to_date < qualify_date_from or to_date > qualify_date_to:
                                    raise ValidationError(
                                        _('You are not able to apply Request for this Extended Child Care leave!'))
                            else:
                                raise ValidationError(
                                    _('You are not able to apply Request for this Extended Child Care leave!'))
                        else:
                            raise ValidationError(
                                _('You are not able to apply Request for this Extended Child Care leave!'))

    @api.constrains('number_of_days_temp', 'holiday_status_id')
    def check_allocation_holidays(self):
        '''
        The method used to Validate for Pro rate type Leaves.
        @param self : Object Pointer
        @return : True or False
        ------------------------------------------------------
        '''
        if self.type == 'remove' and self.holiday_status_id.pro_rate == True and not self.holiday_status_id.mass_leave_deduction:
            date_today = datetime.datetime.today()
            default_allocation = self.holiday_status_id.default_leave_allocation
            leave = remain_month = cessation_remain_month = 0.0
            join_date = datetime.datetime.strptime(self.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT)
            after_one_year = join_date + relativedelta(years=1)
            if date_today < after_one_year:
                working_months = relativedelta(date_today, join_date)
                if working_months and working_months.months:
                    if int(join_date[8:10]) <= 15 and self.holiday_status_id.cut_off_date <= 15:
                        remain_month = working_months.months + 1
                    else:
                        remain_month = working_months.months
                    if self.employee_id.cessation_date:
                        cessation_date = datetime.datetime.strptime(self.employee_id.cessation_date,
                                                                    DEFAULT_SERVER_DATE_FORMAT)
                        if int(join_date[8:10]) >= 15 and self.holiday_status_id.cut_off_date >= 15:
                            cessation_remain_month = cessation_date.month + 1
                        else:
                            cessation_remain_month = cessation_date.month
                if default_allocation:
                    if self.employee_id.join_date and not self.employee_id.cessation_date:
                        leave = (float(default_allocation) / 12) * remain_month
                    else:
                        leave = (float(default_allocation) / 12) * cessation_remain_month
                    leave = int(round(leave))
                if self.number_of_days_temp > leave:
                    raise ValidationError(_('You can not apply leave more than %s !' % (leave)))

    @api.constrains('date_from', 'date_to', 'holiday_status_id')
    def _check_imm_compassionate_leave(self):
        '''
        The method used to Validate immediate compassionate leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'CL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if rec.number_of_days_temp and rec.number_of_days_temp > 5:
                        raise ValidationError(_(
                            'You are not able to apply leave Request more than 5 Working days For compassionate leave!'))

    @api.constrains('date_from', 'date_to', 'holiday_status_id')
    def _check_other_compassionate_leave(self):
        '''
        The method used to Validate other compassionate leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'CLO':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if rec.number_of_days_temp and rec.number_of_days_temp > 3:
                        raise ValidationError(_(
                            'You are not able to apply leave Request more than 3 Working days For compassionate leave!'))

    @api.constrains('holiday_status_id', 'date_from', 'date_to')
    def _check_off_in_leave(self):
        '''
        The method used to Validate other compassionate leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        curr_month = datetime.datetime.today().month
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'OIL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).month
                    to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).month
                    if int(from_date) != int(curr_month) or int(to_date) != int(curr_month):
                        raise ValidationError(_('You can apply off in leave Request for current month only!'))

    @api.constrains('holiday_status_id', 'date_from', 'date_to', 'employee_id')
    def _check_marriage_leave(self):
        '''
        The method used to Validate other compassionate leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name in ('MLC', 'ML'):
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
                    qualify_date = from_date - relativedelta(weeks=2)
                    if qualify_date < datetime.datetime.today().date():
                        raise ValidationError(
                            _('Marriage Leave request should be submitted 2 weeks prior to the requested date.!'))

    @api.constrains('holiday_status_id', 'employee_id', 'date_from', 'date_to')
    def _check_sg_annual_leave(self):
        '''
        The method used to Validate annual leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'AL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
                    qualify_date = from_date - relativedelta(weeks=1)
                    if qualify_date < datetime.datetime.today().date():
                        raise UserError(
                            ('Annual Leave request should be submitted 1 weeks prior to the requested date.!'))

    @api.constrains('date_from', 'date_to')
    def _check_current_month_leave_req(self):
        '''
        The method used to Validate current month leave request.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return: Return the False or True
        ----------------------------------------------------------
        '''
        date_today = datetime.datetime.today()
        first_day = datetime.datetime(date_today.year, date_today.month, 1, 0, 0, 0)
        first_date_from = first_day.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.pre_approved and not rec.holiday_status_id.mass_leave_deduction:
                rec_date_from = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
                rec_date_from1 = rec_date_from.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Singapore'))
                rec_date_from2 = rec_date_from1.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                if rec_date_from2 and rec_date_from2 < first_date_from:
                    raise ValidationError(_('You can apply leave Request only for the current month!'))

    @api.constrains('holiday_status_id', 'employee_id', 'date_from', 'date_to')
    def _check_sg_medical_opt_leave(self):
        '''
        The method used to Validate medical leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_today = datetime.datetime.today()
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'MOL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if rec.employee_id.join_date and rec.employee_id.join_date <= today:
                        join_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT)
                        one_year_day = join_date + relativedelta(months=12)
                        three_months = join_date + relativedelta(months=3)
                        if three_months < date_today and one_year_day > date_today:
                            med_rmv = 0.0
                            self._cr.execute(
                                "SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and holiday_status_id = %d and type='remove'" % (
                                rec.employee_id.id, rec.holiday_status_id.id))
                            all_datas = self._cr.fetchone()
                            if all_datas and all_datas[0]:
                                med_rmv += all_datas[0]
                            res_date = relativedelta(date_today, join_date)
                            tot_month = res_date.months
                            if tot_month == 3 and med_rmv > 5:
                                raise ValidationError(
                                    _('You can not apply medical leave more than 5 days in 3 months!'))
                            elif tot_month == 4 and med_rmv > 8:
                                raise ValidationError(
                                    _('You can not apply medical leave more than 8 days in 4 months!'))
                            elif tot_month == 5 and med_rmv > 11:
                                raise ValidationError(
                                    _('You can not apply medical leave more than 11 days in 5 months!'))
                            elif tot_month >= 6 and med_rmv > 14:
                                raise ValidationError(
                                    _('You can not apply medical leave more than 14 days in one Year!'))
                        if three_months > date_today:
                            raise ValidationError(_('You are not able to apply Medical leave Request.!'))

    @api.constrains('holiday_status_id', 'employee_id', 'date_from', 'date_to')
    def _check_sg_hospitalisation_leave(self):
        '''
        The method used to Validate hospitalisation leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        if self._context is None:
            self._context = {}
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_today = datetime.datetime.today()
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == 'HOL':
                if rec.holiday_status_id.pre_approved == True and not rec.holiday_status_id.mass_leave_deduction:
                    if rec.employee_id.join_date and rec.employee_id.join_date <= today:
                        join_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT)
                        one_year_day = join_date + relativedelta(months=12)
                        three_months = join_date + relativedelta(months=3)
                        if three_months < date_today and one_year_day > date_today:
                            med_rmv = 0.0
                            self._cr.execute(
                                "SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and holiday_status_id = %d and type='remove'" % (
                                rec.employee_id.id, rec.holiday_status_id.id))
                            all_datas = self._cr.fetchone()
                            if all_datas and all_datas[0]:
                                med_rmv += all_datas[0]
                            res_date = relativedelta(date_today, join_date)
                            tot_month = res_date.months
                            if tot_month == 3 and med_rmv > 15:
                                raise ValidationError(
                                    _('You can not apply medical leave more than 15 days in 3 months!'))
                            elif tot_month == 4 and med_rmv > 30:
                                raise ValidationError(
                                    _('You can not apply medical leave more than 30 days in 4 months!'))
                            elif tot_month == 5 and med_rmv > 45:
                                raise ValidationError(
                                    _('You can not apply medical leave more than 45 days in 5 months!'))
                            elif tot_month >= 6 and med_rmv > 60:
                                raise ValidationError(
                                    _('You can not apply medical leave more than 60 days in one Year!'))
                        if three_months > date_today:
                            raise ValidationError(_('You are not able to apply Hospitalisation leave Request.!'))

HrHoliday()

class hr_holidays_status(models.Model):
    _inherit = 'hr.holidays.status'

    mass_leave_deduction = fields.Boolean(string='Override Pre-Approval', default=True)

hr_holidays_status()
