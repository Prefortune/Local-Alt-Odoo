# -*- coding: utf-8 -*-
################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import pytz
import datetime
import logging
from datetime import time, timedelta


from .zkconst import *
from struct import unpack
from odoo import api, fields, models
from odoo import _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    device_id = fields.Char(string='Biometric Device ID For Machine IP 83.111.122.42')
    device_id_2 = fields.Char(string="Biometric Device ID For Machine  IP 83.111.120.41")


class ZkMachine(models.Model):
    _name = 'zk.machine'

    name = fields.Char(string='Machine IP', required=True)
    port_no = fields.Integer(string='Port No', required=True)
    address_id = fields.Many2one('res.partner', string='Working Address')
    map_field = fields.Char(string='Mapping field name')
    auto_check_out_time = fields.Char(string='Auto Check Out Time',
                                     help="Auto Check Out Time in 24 hours format like 19:00")
    company_id = fields.Many2one('res.company', string='Company', default=lambda
        self: self.env.user.company_id.id)   
    

    def device_connect(self, zk):
        try:
            # _logger.info("..................zk.connect()...%s",zk.connect())
            conn = zk.connect()
            return conn
        except:
            return False
        
    def pf_connect_device(self):
        try:
            machine_ip = self.name
            zk_port = self.port_no
            zk = ZK(machine_ip, port=zk_port, timeout=60,
                                password=0, force_udp=False, ommit_ping=True)           
            conn = self.device_connect(zk)
            if conn:
                _logger.info("..........connected.............zk.............%s",conn)
            else:
                _logger.info(".......Notconnected.............zk.............%s",conn)
        except Exception as error:
            raise ValidationError(f'{error}')
        

    def clear_attendance(self):
        """Methode to clear record from the zk.machine.attendance model and
        from the device"""
        for info in self:
            try:
                machine_ip = info.name
                zk_port = info.port_no
                try:
                    # Connecting with the device
                    zk = ZK(machine_ip, port=zk_port, timeout=30,
                            password=0, force_udp=False, ommit_ping=True)
                except NameError:
                    raise UserError(_(
                        "Please install it with 'pip3 install pyzk'."))
                conn = self.device_connect(zk)
                if conn:
                    conn.enable_device()
                    clear_data = zk.get_attendance()
                    if clear_data:
                        # Clearing data in the device
                        conn.clear_attendance()
                        # Clearing data from attendance log
                        self._cr.execute(
                            """delete from zk_machine_attendance""")
                        conn.disconnect()
                    else:
                        raise UserError(
                            _('Unable to clear Attendance log.Are you sure '
                              'attendance log is not empty.'))
                else:
                    raise UserError(
                        _('Unable to connect to Attendance Device. Please use '
                          'Test Connection button to verify.'))
            except Exception as error:
                raise ValidationError(f'{error}')

    def restart_device(self):
        """Method to restart the device."""
        zk = ZK(self.name, port=self.port_no, timeout=15, password=0,
                force_udp=False, ommit_ping=True)
        if self.device_connect(zk):
            ans=self.device_connect(zk).restart()
            _logger.info("..........restartted.....................zk.............%s",ans)         
        else:
            raise UserError(
                _('Unable to restart, please check the device is connected.'))

    def getSizeUser(self, zk):
        """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent

        Returns the amount of bytes that are going to be sent"""
        command = unpack('HHHH', zk.data_recv[:8])[0]
        if command == CMD_PREPARE_DATA:
            size = unpack('I', zk.data_recv[8:12])[0]
            return size
        else:
            return False

    def zkgetuser(self, zk):
        """Start a connection with the time clock"""
        try:
            users = zk.get_users()
            return users
        except:
            return False

    @api.model
    def cron_download(self):
        """cron_download method: Perform a cron job to download attendance data for all machines.

          This method iterates through all the machines in the 'zk.machine' model and
          triggers the download_attendance method for each machine."""
        machines = self.env['zk.machine'].search([])
        for machine in machines:
            machine.download_attendance()
    
    def check_attendance(self):
        att_obj = self.env['hr.attendance'].sudo().search([('check_out', '=', False)])
        if att_obj:
            for att in att_obj:
                if att.check_in:
                    check_in = att.check_in
                    if check_in.date() < datetime.datetime.now().date():
                        att.write({'check_out': check_in})                        
                    
                else:
                    raise UserError(_('Check In Time Not Found'))
    
    def download_attendance(self):
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")

        zk_attendance = self.env['zk.machine.attendance']
        att_obj = self.env['hr.attendance']

        for info in self:
            machine_ip = info.name
            zk_port = info.port_no
            device_field_name = info.map_field
            auto_checkout_time_str = self.auto_check_out_time or "19:00"
            timeout = 15
            if not device_field_name:
                _logger.error("Device field name is not set for machine %s", machine_ip)
                continue

            try:
                zk = ZK(
                    machine_ip,
                    port=zk_port,
                    timeout=timeout,
                    password=0,
                    force_udp=False,
                    ommit_ping=True
                )
                _logger.info("...............................zk.............%s",zk)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))

            conn = self.device_connect(zk)
            if conn:
                try:
                    user_list = conn.get_users()
                except:
                    user_list = []

                try:
                    attendance_logs = conn.get_attendance()
                except:
                    attendance_logs = []

                if attendance_logs:
                    attendance_logs.sort(key=lambda a: a.timestamp)
                    #_logger.info("...............................attendance %s", attendance_logs)
                    #_logger.info("...............................attendance logs count: %s", len(attendance_logs))

                    last_attendance_map = {}
                    first_entry_as_checkout = {}
                    for entry in attendance_logs:
                        punch_time = datetime.strptime(entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(punch_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        punch_time_str = fields.Datetime.to_string(utc_dt)

                        entry_date = utc_dt.date()
                        employee_key = (entry.user_id, entry_date)
                        if employee_key not in first_entry_as_checkout:
                            # First entry of the day for this employee
                            first_entry_as_checkout[employee_key] = True

                            if entry.punch == 1:  # First entry is a check-out
                                _logger.info("Skipping first entry as check-out for %s %s at %s", device_field_name, entry.user_id, punch_time)
                                continue  # Skip this entry

                        employee = self.env['hr.employee'].search([(device_field_name, '=', entry.user_id)], limit=1)
                        if not employee:
                            uid = next((u for u in user_list if u.user_id == entry.user_id), None)
                            if not uid:
                                _logger.info("No user found for %s %s", device_field_name,entry.user_id)
                                continue

                            #search by name if we get
                            employee = self.env['hr.employee'].search([('name', '=', uid.name)], limit=1)

                            # If no employee found by name, create a new employee
                            if not employee:
                                employee = self.env['hr.employee'].create({
                                    device_field_name: entry.user_id,
                                    'name': uid.name if uid else "Unknown",
                                })
                                _logger.info("Created new employee for %s %s", device_field_name,entry.user_id)
                            else:
                                # If employee found by name, update the device field
                                employee.write({device_field_name: entry.user_id})
                                _logger.info("updated existing employee for %s %s", device_field_name,entry.user_id)

                        if zk_attendance.search(['|',('device_id', '=', entry.user_id),('device_id_2', '=', entry.user_id), ('punching_time', '=', punch_time_str)]):
                            #_logger.info("Duplicate punch found for %s %s at %s", device_field_name, entry.user_id, punch_time_str)
                            continue

                        #entry_date = utc_dt.date()
                        # existing_day_logs = zk_attendance.search([
                        #     ('employee_id', '=', employee.id),
                        #     ('punching_time', '>=', datetime.combine(entry_date, time(0, 0))),
                        #     ('punching_time', '<', datetime.combine(entry_date + timedelta(days=1), time(0, 0)))
                        # ], order='punching_time ASC', limit=1)
                        
                        # if entry.punch == 1 and not existing_day_logs:
                        #     _logger.info("Skipping first punch of day as check-out for device_id %s at %s", entry.user_id, punch_time_str)
                        #     continue

                        _logger.info("Processing punch: %s=%s, punch_type=%s, time=%s", device_field_name, entry.user_id, entry.punch, punch_time_str)

                        zk_attendance.create({
                            'employee_id': employee.id,
                            device_field_name: entry.user_id,
                            'attendance_type': str(entry.status),
                            'punch_type': str(entry.punch),
                            'punching_time': punch_time_str,
                            'address_id': info.address_id.id
                        })
                        _logger.info("Created zk.machine.attendance record for %s on %s", employee.name, punch_time_str)

                        hr_attendance = att_obj.search([
                            ('employee_id', '=', employee.id),
                            ('check_out', '=', False)
                        ], order="check_in DESC", limit=1)

                        if entry.punch == 0:  # Check-in
                            # Check for existing open check-in on same day
                            open_checkin_same_day = att_obj.search([
                                ('employee_id', '=', employee.id),
                                ('check_out', '=', False),
                                ('check_in', '>=', fields.Datetime.to_string(datetime.combine(entry_date, time.min))),
                                ('check_in', '<=', fields.Datetime.to_string(datetime.combine(entry_date, time.max))),
                            ], limit=1)

                            if open_checkin_same_day:
                                _logger.info("Skipping check-in for %s at %s: previous check-in without check-out exists on same day", employee.name, punch_time_str)
                                continue

                            if hr_attendance:
                                prev_checkin = hr_attendance.check_in.astimezone(local_tz).date()
                                if prev_checkin < utc_dt.date():
                                    parsed_time = datetime.strptime(auto_checkout_time_str, "%H:%M").time()
                                    missed_checkout_time = datetime.combine(prev_checkin, parsed_time)
                                    missed_checkout_utc = local_tz.localize(missed_checkout_time).astimezone(pytz.utc)
                                    hr_attendance.write({'check_out': fields.Datetime.to_string(missed_checkout_utc)})
                                    _logger.info("Auto-filled stale checkout for %s on %s", employee.name, prev_checkin)

                            # Now proceed with creating new check-in
                            att_obj.create({
                                'employee_id': employee.id,
                                'check_in': punch_time_str
                            })
                            last_attendance_map[employee.id] = utc_dt.date()
                            _logger.info("Created HR attendance check-in for %s at %s", employee.name, punch_time_str)

                        elif entry.punch == 1:  # Check-out
                            if hr_attendance:
                                hr_attendance.write({'check_out': punch_time_str})
                                _logger.info("Updated HR attendance check-out for %s at %s", employee.name, punch_time_str)

                else:
                    _logger.error("No attendance logs found for %s", machine_ip)

                conn.disconnect()
                return True
            else:
                _logger.error("Unable to connect to %s", machine_ip)




    # def download_attendance(self):
    #     """
    #      download_attendance method: Download attendance data from a ZKTeco machine.

    #      This method connects to a ZKTeco machine specified by the 'name', 'port_no', and other parameters,
    #      retrieves attendance data, and creates corresponding records in 'zk.machine.attendance' and 'hr.attendance'.

    #      Args:
    #          None

    #      Returns:
    #          bool: True if the download is successful, raises exceptions otherwise.
    #      """
    #     _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
    #     zk_attendance = self.env['zk.machine.attendance']
    #     att_obj = self.env['hr.attendance']
    #     for info in self:
    #         machine_ip = info.name
    #         first_ip = '83.111.122.42'
    #         zk_port = int(info.port_no)
    #         timeout = 60
    #         # try:
    #         zk = ZK(machine_ip, port=zk_port, timeout=timeout, password=0,
    #                     force_udp=False, ommit_ping=True)                        
    #         _logger.info("...............................zk.............%s",zk)               
    #         # except NameError:
    #         #     raise UserError(
    #         #         _("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
    #         conn = self.device_connect(zk)
    #         _logger.info("...............................conn.............%s",conn)
    #         if conn:
    #             # conn.disable_device() #Device Cannot be used during this time.
    #             try:
    #                 user = conn.get_users()
    #                 _logger.info("...............................user..........%s",user)
    #             except:
    #                 user = False
    #             try:
    #                 attendance = conn.get_attendance()
    #             except:
    #                 attendance = False
    #             _logger.info("...............................attendance..........%s",attendance)
    #             if attendance:
    #                 for each in attendance:
    #                     atten_time = each.timestamp
    #                     atten_time = datetime.strptime(
    #                         atten_time.strftime('%Y-%m-%d %H:%M:%S'),
    #                         '%Y-%m-%d %H:%M:%S')
    #                     local_tz = pytz.timezone(
    #                         self.env.user.partner_id.tz or 'GMT')
    #                     local_dt = local_tz.localize(atten_time, is_dst=None)
    #                     utc_dt = local_dt.astimezone(pytz.utc)
    #                     utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
    #                     atten_time = datetime.strptime(
    #                         utc_dt, "%Y-%m-%d %H:%M:%S")
    #                     atten_time = fields.Datetime.to_string(atten_time)
    #                     if user:                                               
    #                         field_name=''
    #                         domain =[]
    #                         _logger.info("...............................machine_ip..........%s",machine_ip == first_ip)
    #                         if machine_ip == first_ip:
    #                             field_name='device_id_2'
    #                             domain.append('|')
    #                             domain.append(('device_id_2', '=',int(each.user_id)))
    #                             _logger.info("...............................field_name..........%s....%s",field_name,domain)
    #                         else:
    #                             field_name='device_id'
    #                             domain.append('|')
    #                             domain.append(('device_id', '=',int(each.user_id)))
    #                             _logger.info("...............................field_name..........%s",field_name)
    #                         if domain:
    #                             _logger.info("...............................inside..if")                   
    #                             for uid in user:
    #                                 _logger.info("...............................uid.user_id..........%s",uid.user_id)
    #                                 _logger.info("...............................each.user_id..........%s",each.user_id)
    #                                 if uid.user_id == each.user_id:
    #                                     domain.append(('name','=',uid.name))                                                 
    #                                     _logger.info("...............................domain..........%s",domain)
    #                                     get_user_id = self.env[
    #                                             'hr.employee'].search(domain)
    #                                     _logger.info("...............................get_user_id..........%s",get_user_id)
    #                                     if get_user_id:                                        
    #                                         duplicate_atten_ids = zk_attendance.search( [('device_id', '=', each.user_id), (
    #                                         'punching_time', '=',
    #                                         atten_time)])
    #                                         _logger.info("...............................duplicate_atten_ids..........%s",duplicate_atten_ids)
    #                                         if duplicate_atten_ids:
    #                                             continue
    #                                         else:
    #                                             zk_attendance.create(
    #                                                 {'employee_id': get_user_id.id,
    #                                                 field_name: each.user_id,
    #                                                 'attendance_type': str(
    #                                                     each.status),
    #                                                 'punch_type': str(each.punch),
    #                                                 'punching_time': atten_time,
    #                                                 'address_id': info.address_id.id})
    #                                             att_var = att_obj.sudo().search([(
    #                                                 'employee_id',
    #                                                 '=',
    #                                                 get_user_id.id),
    #                                                 (
    #                                                     'check_out',
    #                                                     '=',
    #                                                     False)])
    #                                             _logger.info("...............................att_var..........%s",att_var)
    #                                             att_var_all = att_obj.search([(
    #                                                 'employee_id',
    #                                                 '=',
    #                                                 get_user_id.id)])
    #                                             _logger.info("...............................att_var..all........%s.....%s",att_var_all,each.punch)
    #                                             if each.punch == 0:  # check-in
    #                                                 for att in att_var_all:
    #                                                     _logger.info("...............................att.check_out....%s....%s",att.check_in,att.check_out)
    #                                                     if not att.check_out:
    #                                                         att.write({
    #                                                             'check_out': att.check_in})
    #                                                 # if not att_var:                                                        
    #                                                 att_obj.create({
    #                                                     'employee_id': get_user_id.id,
    #                                                     'check_in': atten_time})                                                    
    #                                             if each.punch == 1:  # check-out
    #                                                 if len(att_var) == 1:
    #                                                     att_var.write({
    #                                                         'check_out': atten_time})
    #                                                 else:
    #                                                    for att in att_var_all:                                                           
    #                                                         if not att.check_out:                                                                
    #                                                             att.write({
    #                                                                 'check_out': att.check_in})                                                            
    #                                     else:
    #                                         employee = self.env[
    #                                                 'hr.employee'].create(
    #                                                 {field_name: each.user_id,
    #                                                 'name': uid.name})
    #                                         _logger.info("...............................employee..........%s",employee)
    #                                         zk_attendance.create(
    #                                                 {'employee_id': employee.id,
    #                                                 field_name: each.user_id,
    #                                                 'attendance_type': str(
    #                                                     each.status),
    #                                                 'punch_type': str(each.punch),
    #                                                 'punching_time': atten_time,
    #                                                 'address_id': info.address_id.id})
    #                                         _logger.info("...............................zk_attendance..........%s",zk_attendance) 
    #                                         att_var = att_obj.search([(
    #                                                 'employee_id',
    #                                                 '=',
    #                                                 employee.id),
    #                                                 (
    #                                                     'check_out',
    #                                                     '=',
    #                                                     False)])                                         
    #                                         if each.punch == 0:  # check-in                                               
    #                                             if not att_var:
    #                                                 att_obj.create({
    #                                                     'employee_id': employee.id,
    #                                                     'check_in': atten_time})
    #                                             else:
    #                                                 att_var.write({
    #                                                     'check_out': att_var[0].check_in})
    #                                                 att_obj.create({
    #                                                     'employee_id': employee.id,
    #                                                     'check_in': atten_time})
    #                                         else:                                               
    #                                             if len(att_var) == 1:
    #                                                 att_var.write({
    #                                                     'check_out': atten_time})
    #                                             else:
    #                                                 att_var1 = att_obj.search([(
    #                                                     'employee_id',
    #                                                     '=',
    #                                                     employee.id)])
    #                                                 if att_var1:
    #                                                     att_var1[-1].write({
    #                                                         'check_out': atten_time})                                         
    #                                         _logger.info("...............................att_obj..........%s",att_obj)
    #                     # if user:
    #                     #     for uid in user:
    #                     #         if uid.user_id == each.user_id:
    #                     #             get_user_id = self.env[
    #                     #                 'hr.employee'].search(
    #                     #                 [('device_id', '=', each.user_id)])
    #                     #             if get_user_id:
    #                     #                 duplicate_atten_ids = zk_attendance.search(
    #                     #                     [('device_id', '=', each.user_id), (
    #                     #                         'punching_time', '=',
    #                     #                         atten_time)])
    #                     #                 if duplicate_atten_ids:
    #                     #                     continue
    #                     #                 else:
    #                     #                     zk_attendance.create(
    #                     #                         {'employee_id': get_user_id.id,
    #                     #                          'device_id': each.user_id,
    #                     #                          'attendance_type': str(
    #                     #                              each.status),
    #                     #                          'punch_type': str(each.punch),
    #                     #                          'punching_time': atten_time,
    #                     #                          'address_id': info.address_id.id})
    #                     #                     att_var = att_obj.search([(
    #                     #                         'employee_id',
    #                     #                         '=',
    #                     #                         get_user_id.id),
    #                     #                         (
    #                     #                             'check_out',
    #                     #                             '=',
    #                     #                             False)])
    #                     #                     if each.punch == 0:  # check-in
    #                     #                         if not att_var:
    #                     #                             att_obj.create({
    #                     #                                 'employee_id': get_user_id.id,
    #                     #                                 'check_in': atten_time})
    #                     #                     if each.punch == 1:  # check-out
    #                     #                         if len(att_var) == 1:
    #                     #                             att_var.write({
    #                     #                                 'check_out': atten_time})
    #                     #                         else:
    #                     #                             att_var1 = att_obj.search([(
    #                     #                                 'employee_id',
    #                     #                                 '=',
    #                     #                                 get_user_id.id)])
    #                     #                             if att_var1:
    #                     #                                 att_var1[-1].write({
    #                     #                                     'check_out': atten_time})

    #                     #             else:
    #                     #                 employee = self.env[
    #                     #                     'hr.employee'].create(
    #                     #                     {'device_id': each.user_id,
    #                     #                      'name': uid.name})
    #                     #                 zk_attendance.create(
    #                     #                     {'employee_id': employee.id,
    #                     #                      'device_id': each.user_id,
    #                     #                      'attendance_type': str(
    #                     #                          each.status),
    #                     #                      'punch_type': str(each.punch),
    #                     #                      'punching_time': atten_time,
    #                     #                      'address_id': info.address_id.id})
    #                     #                 att_obj.create(
    #                     #                     {'employee_id': employee.id,
    #                     #                      'check_in': atten_time})
    #                     #         else:
    #                     #             pass
    #                 # zk.enableDevice()
    #                 conn.disconnect
    #                 return True
    #             else:
    #                 raise UserError(
    #                     _('Unable to get the attendance log, please try again later.'))
    #         else:
    #             raise UserError(
    #                 _('Unable to connect, please check the parameters and network connections.'))
