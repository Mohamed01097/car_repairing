# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, time, datetime, timedelta
from odoo.exceptions import UserError

class FleetWorkOrder(models.Model):
    _name = 'fleet.workorder'
    _inherit = ['mail.thread']
    _description = "Fleet WorkOrder"

    name = fields.Char(string='Work Order', required=True)
    sequence = fields.Char(string='Sequence', readonly=True, copy=False)
    date = fields.Date(string='Date')
    client_id = fields.Many2one('res.partner', string='Client', required=True)
    client_phone = fields.Char(string='Phone.')
    client_mobile = fields.Char(string='Mobile')
    client_email = fields.Char(string='Email')
    date_planned = fields.Datetime(string='Scheduled Date')
    date_planned_end = fields.Datetime(string='Planned End Date')
    cycle = fields.Float(string='Number of Cycles')
    hour = fields.Float(string='Number of Hours')
    date_start = fields.Datetime(string='Start Date', readonly=True)
    pause_time = fields.Datetime(string='Pause Date', readonly=True)
    date_finished = fields.Datetime(string='End Date', readonly=True)
    total_paused_hours = fields.Float(string='Total Paused Hours', readonly=True)
    delay = fields.Float(string='Working Hours', readonly=True)
    hours_worked = fields.Float(string='Hours Worked')
    state = fields.Selection(
        [('draft', 'Draft'), ('cancel', 'Cancelled'), ('pause', 'Paused'), ('startworking', 'In Progress'),
         ('done', 'Finished'), ('deleted', 'Deleted')], 'Status', readonly=True, copy=False,
        help="* When a work order is created it is set in 'Draft' status.\n" \
             "* When user sets work order in start mode that time it will be set in 'In Progress' status.\n" \
             "* When work order is in running mode, during that time if user wants to stop or to make changes in order then can set in 'Pending' status.\n" \
             "* When the user cancels the work order it will be set in 'Canceled' status.\n" \
             "* When order is completely processed that time it is set in 'Finished' status.")
    timer_line_ids = fields.One2many('workorder.timer.line', 'workorder_id', string='Timer Lines')
    phone = fields.Char(string='Phone')
    fleet_id = fields.Many2one('fleet.vehicle', 'Fleet',)
    # @api.onchange('fleet_repair_line.fleet_id')
    # def _compute_fleet_id(self):
    #     for record in self:
    #         print("jjjjjjjjjjjjjjjjjjjjjjj",record.fleet_repair_line.fleet_id)
    #         record.fleet_repair_line.fleet_id = record.fleet_id
    license_plate = fields.Char('License Plate',
                                help='License plate number of the vehicle (ie: plate number for a car)',
                                # related="feet_id.license_plate"
                                )
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle')
    fuel_type = fields.Selection([('diesel', 'Diesel'),
                                  ('gasoline', 'Gasoline'),
                                  ('full_hybrid', 'Full Hybrid'),
                                  ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
                                  ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
                                  ('cng', 'CNG'),
                                  ('lpg', 'LPG'),
                                  ('hydrogen', 'Hydrogen'),
                                  ('electric', 'Electric'), ('hybrid', 'Hybrid')], 'Fuel Type',
                                 help='Fuel Used by the vehicle')

    service_type = fields.Many2one('service.type', string='Nature of Service')
    user_id = fields.Many2one('res.users', string='Technician')
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority')
    description = fields.Text(string='Fault Description')
    spare_part_ids = fields.One2many('spare.part.line', 'diagnose_id', string='Spare Parts Needed')
    est_ser_hour = fields.Float(string='Estimated Sevice Hours')
    service_product_id = fields.Many2one('product.product', string='Service Product')
    service_product_price = fields.Integer('Service Product Price')
    fleet_repair_id = fields.Many2one('fleet.repair', string='Car Repair', copy=False, readonly=True)
    diagnose_id = fields.Many2one('fleet.diagnose', string='Car Diagnosis', copy=False, readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', copy=False, readonly=True)
    spare_part_ids = fields.One2many('spare.part.line', 'workorder_id', string='Spare Parts')
    fleet_repair_line = fields.One2many('fleet.repair.line', 'workorder_id', string="fleet Lines")
    count_fleet_repair = fields.Integer(string="Invoice", compute='_compute_fleet_repair_id')
    count_dig = fields.Integer(string="Count diagnose", compute='_compute_dig_id')
    confirm_sale_order = fields.Boolean('is confirm')
    saleorder_count = fields.Integer(string="Sale Order", compute='_compute_saleorder_id')
    timesheet_ids = fields.One2many('account.analytic.line', 'workorder_id', string="Timesheet")
    car_lift = fields.Many2one('car.lift', string="Car Lift")
    parking_slot = fields.Many2one('parking.slot', string="Parking Slot")
    responsible_person = fields.Many2one('res.partner', string="Responsible Technician")
    checklist_ids = fields.Many2many('fleet.repair.checklist', string='Checklist')
    notes = fields.Text()
    repair_image_line_ids = fields.One2many(
        'fleet.repair.image.line',
        'workorder_id',
        string='Repair Images'
    )
    order_checklist_ids = fields.One2many('fleet.repair.checklist.order', 'workorder_id', string='Repair Checklist')
    _order = 'id desc'

    @api.depends('fleet_repair_id')
    def _compute_fleet_repair_id(self):
        for order in self:
            repair_order_ids = self.env['fleet.repair'].search([('workorder_id', '=', order.id)])
            order.count_fleet_repair = len(repair_order_ids)

    @api.depends('diagnose_id')
    def _compute_dig_id(self):
        for order in self:
            work_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id.workorder_id', '=', order.id)])
            order.count_dig = len(work_order_ids)

    @api.depends('confirm_sale_order')
    def _compute_saleorder_id(self):
        for order in self:
            so_order_ids = self.env['sale.order'].search([('state', '=', 'sale'), ('workorder_id', '=', order.id)])
            order.saleorder_count = len(so_order_ids)

    def button_view_repair(self):
        list = []
        context = dict(self._context or {})
        repair_order_ids = self.env['fleet.repair'].search([('workorder_id', '=', self.id)])
        for order in repair_order_ids:
            list.append(order.id)
        return {
            'name': _('Car Repair'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'fleet.repair',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', list)],
            'context': context,
        }

    def button_view_diagnosis(self):
        list = []
        context = dict(self._context or {})
        dig_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id.workorder_id', '=', self.id)])
        for order in dig_order_ids:
            list.append(order.id)
        return {
            'name': _('Car Diagnosis'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'fleet.diagnose',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', list)],
            'context': context,
        }

    def button_view_saleorder(self):
        list = []
        context = dict(self._context or {})
        order_ids = self.env['sale.order'].search([('state', '=', 'sale'), ('workorder_id', '=', self.id)])
        for order in order_ids:
            list.append(order.id)
        return {
            'name': _('Sale'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', list)],
            'context': context,
        }

    def button_cancel(self):
        self.write({'state': 'cancel'})

    def _create_timer_log(self, action, duration=0.0):
        """Helper to add a log line"""
        self.env['workorder.timer.line'].create({
            'workorder_id': self.id,
            'action': action,
            'action_time': datetime.now(),
            'duration': duration,
        })
    def button_resume(self):
        if self.state != 'pause':
            return
        now = datetime.now()
        paused_hours = 0.0
        if self.pause_time:
            paused_hours = (now - self.pause_time).total_seconds() / 3600
        self.write({
            'total_paused_hours': self.total_paused_hours + paused_hours,
            'pause_time': False,
            'state': 'startworking',
        })
        self._create_timer_log('resume', duration=paused_hours)
        self.write({'state': 'startworking'})

    def button_pause(self):
        """Open wizard to enter pause reason"""
        self.ensure_one()
        return {
            'name': 'Pause Work Order',
            'type': 'ir.actions.act_window',
            'res_model': 'pause.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_workorder_id': self.id},
        }

    def button_draft(self):
        self.write({'state': 'draft'})

    def action_start_working(self):
        """ Sets state to start working and writes starting date.
        @return: True
        """
        now = datetime.now()
        self.write({
            'date_start': now,
            'state': 'startworking',
        })
        self._create_timer_log('start')
        if self.fleet_repair_id:
            self.fleet_repair_id.sudo().write({'state': 'workorder'})

        return True

    def action_done(self):
        """ Sets state to done, writes finish date and calculates delay.
        @return: True
        """
        for line in self.order_checklist_ids:
            if not line.done:
                raise UserError(_("Please complete all checklist items before marking the work order as done."))

        if not self.date_start:
            return
        now = datetime.now()
        total_hours = (now - self.date_start).total_seconds() / 3600
        effective_hours = total_hours - self.total_paused_hours
        if effective_hours < 0:
            effective_hours = 0
        delay = 0.0
        delay = (now - self.date_start).total_seconds() / 3600
        if delay < 0:
            delay = 0
        self.write({'state': 'done', 'date_finished': now, 'delay': delay,'hours_worked':effective_hours})
        if self.sale_order_id:
            self.sale_order_id.sudo().write({'state': 'sale'})
        if self.fleet_repair_id:
            self.fleet_repair_id.sudo().write({'state': 'work_completed'})
        return True
    def select_all(self):
        for line in self.repair_checklist_ids:
            line.done = True

    @api.onchange('checklist_ids')
    def onchange_checklist_ids(self):
        for rec in self:
            if rec.checklist_ids:
                checklist_points = self.env['checklist.points'].search([
                    ('type_ids', 'in', rec.checklist_ids.ids)
                ])
                rec.repair_checklist_ids = [(5, 0, 0)] + [
                    (0, 0, {
                        'name': point.name,
                        'description': '',  # يمكن تهيئته من point لو عندك
                        'done': False,
                    }) for point in checklist_points
                ]
            else:
                rec.repair_checklist_ids = [(5, 0, 0)]




class FleetRepairImageLine(models.Model):
    _name = 'fleet.repair.image.line'
    _description = 'Repair Image Line'

    workorder_id = fields.Many2one('fleet.workorder', string='Repair')

    b_image1 = fields.Binary('Image1')
    b_image2 = fields.Binary('Image2')
    b_image3 = fields.Binary('Image3')
    b_image4 = fields.Binary('Image4')
    b_image5 = fields.Binary('Image5')
    a_image1 = fields.Binary('Image1')
    a_image2 = fields.Binary('Image2')
    a_image3 = fields.Binary('Image3')
    a_image4 = fields.Binary('Image4')
    a_image5 = fields.Binary('Image5')



class WorkorderTimerLine(models.Model):
    _name = 'workorder.timer.line'
    _description = "Work Order Timer Log"
    _order = 'action_time asc'

    workorder_id = fields.Many2one('fleet.workorder', string="Work Order", ondelete='cascade')
    action = fields.Selection([
        ('start', 'Start'),
        ('pause', 'Pause'),
        ('resume', 'Resume'),
        ('finish', 'Finish'),
    ], string="Action", required=True)
    action_time = fields.Datetime(string="Time", required=True)
    duration = fields.Float(string="Duration (Hours)")
    reason = fields.Selection([
    ('lunch_break', 'Lunch Break'),
    ('praying_break', 'Praying'),
    ('restroom_break', 'Restroom Break'),
    ], string="Reason")  # 🔹 السبب

class ChecklistPoints(models.Model):
    _name = 'checklist.points'
    _description = "Checklist Points"

    name = fields.Char(string='Name')
    type_ids = fields.Many2many('fleet.repair.checklist')
    _sql_constraints = [
        ('unique_name', 'unique (name)', "This name is already exist")
    ]
class FleetRepairChecklist(models.Model):
    _name = 'fleet.repair.checklist.order'
    _description = "FLEET REPAIR Checklist"

    name = fields.Char('Checklist Name')
    active = fields.Boolean(default=True)
    description = fields.Char(string="Description")
    done = fields.Boolean(string="Done")
    workorder_id = fields.Many2one('fleet.workorder', string="Checklist",ondelete='cascade')

class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    default_fuel_type = fields.Selection(default='gasoline')
