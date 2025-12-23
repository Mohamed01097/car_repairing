# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, time, datetime
from odoo import tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools import human_size
import base64


class FleetRepair(models.Model):
    _name = 'fleet.repair'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Car Customization"
    _order = 'id desc'

    name = fields.Char(string='Subject', required=True)
    sequence = fields.Char(string='Sequence', readonly=True, copy=False)
    client_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True,
                                domain="[('partner_type', '=', 'customer')]")
    client_phone = fields.Char(string='Phone')
    client_mobile = fields.Char(string='Mobile')
    client_email = fields.Char(string='Email')

    def get_today_date(self):
        return fields.Date.today()

    receipt_date = fields.Date(string='Date of Receipt', default=get_today_date)
    contact_name = fields.Char(string='Contact Name')
    phone = fields.Char(string='Contact Number')
    fleet_id = fields.Many2one('fleet.vehicle', 'Car')
    license_plate = fields.Char('License Plate',
                                help='License plate number of the vehicle (ie: plate number for a car)')
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
    guarantee = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Under Guarantee?')
    guarantee_type = fields.Selection(
        [('paid', 'paid'), ('free', 'Free')], string='Guarantee Type')
    service_type = fields.Many2one('service.type', string='Nature of Service')
    user_id = fields.Many2one('res.users', string='Assigned to', tracking=True)
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority')
    description = fields.Text(string='Notes')
    service_detail = fields.Text(string='Service Details')
    state = fields.Selection([
        ('draft', 'Received'),
        # ('diagnosis', 'In Diagnosis'),
        # ('diagnosis_complete', 'Diagnosis Complete'),
        ('quote', 'Quotation Sent'),
        ('saleorder', 'Quotation Approved'),
        ('workorder', 'Work in Progress'),
        ('work_completed', 'Work Completed'),
        ('invoiced', 'Invoiced'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], 'Status', default="draft", readonly=True, copy=False, help="Gives the status of the fleet repairing.",
        index=True, tracking=True)
    diagnose_id = fields.Many2one('fleet.diagnose', string='Car Diagnose', copy=False)
    workorder_id = fields.Many2one('fleet.workorder', string='Car Work Order', copy=False)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', copy=False)
    fleet_repair_line = fields.One2many('fleet.repair.line', 'fleet_repair_id', string="Car Lines")
    workorder_count = fields.Integer(string='Work Orders', compute='_compute_workorder_id')
    dig_count = fields.Integer(string='Diagnosis Orders', compute='_compute_dignosis_id')
    quotation_count = fields.Integer(string="Quotations", compute='_compute_quotation_id')
    saleorder_count = fields.Integer(string="Sale Order", compute='_compute_saleorder_id')
    inv_count = fields.Integer(string="Invoice")
    confirm_sale_order = fields.Boolean('is confirm')
    images_ids = fields.One2many('ir.attachment', 'car_repair_id', 'Images')
    parent_id = fields.Many2one('fleet.repair', string='Parent Repair', index=True)
    cap_imag = fields.Binary(string="Capture Image")
    child_ids = fields.One2many('fleet.repair', 'parent_id', string="Sub-Repair")
    before_image_ids = fields.One2many('maintenance.image', 'maintenance_id', string="Before Images")
    after_image_ids = fields.One2many('maintenance.image', 'maintenance_id', string="After Images")
    repair_checklist_ids = fields.One2many('fleet.repair.checklist.repair', 'repair_id', string='Repair Checklist',
                                           compute='_compute_repair_checklist_ids')
    feedback_description = fields.Char(string="Feedback")
    rating = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], string="Rating")
    timesheet_ids = fields.One2many('account.analytic.line', 'repair_id', string="Timesheet")
    planned_hours = fields.Float("Initially Planned Hours", tracking=True)
    subtask_planned_hours = fields.Float("Sub-tasks Planned Hours", compute='_compute_subtask_planned_hours',
                                         help="Sum of the hours allocated for all the sub-tasks (and their own sub-tasks) linked to this task. Usually less than or equal to the allocated hours of this task.")
    car_lift = fields.Many2one('car.lift', domain="[('activate','=',True)]")
    parking_slot = fields.Many2one('parking.slot', domain="[('activate','=',True)]")
    responsible_person = fields.Many2one('res.partner', string='Responsible Technician',
                                         domain="[('partner_type','=','technician')]")
    checklist_ids = fields.Many2many('fleet.repair.checklist', string='Checklist')
    notes = fields.Text()
    # start
    api.depends('checklist_ids')

    @api.depends('checklist_ids')
    def _compute_repair_checklist_ids(self):
        for rec in self:
            if rec.checklist_ids:
                # البحث عن النقاط المرتبطة بـ checklist_ids
                checklist_points = self.env['checklist.points'].search([
                    ('type_ids', 'in', rec.checklist_ids.ids)
                ])

                # إذا كانت repair_checklist_ids فارغة، نحتاج لإنشاء السجلات الجديدة
                if not rec.repair_checklist_ids:
                    created_checklists = self.env['fleet.repair.checklist.repair'].create([{
                        'name': point.name,
                        'description': '',  # أو تخصيصه بناءً على النقطة
                        'done': False,
                        'repair_id': rec.id,
                    } for point in checklist_points])

                    # ربط السجلات التي تم إنشاؤها بـ repair_checklist_ids باستخدام write
                    rec.write({
                        'repair_checklist_ids': [(6, 0, created_checklists.ids)]
                    })
                else:
                    # إذا كانت repair_checklist_ids تحتوي على قيم، نقوم بتحديث السجلات الموجودة
                    # في حالة تحديث أي من السجلات، استخدم هذه الطريقة فقط لإضافة عناصر جديدة
                    rec.repair_checklist_ids = [(4, point.id) for point in checklist_points]
            else:
                # إذا كانت checklist_ids فارغة، نقوم بمسح السجلات الموجودة
                rec.repair_checklist_ids = False  # أو [(5, 0, 0)] إذا كنت ترغب في مسح السجلات

    @api.constrains('fleet_repair_line')
    def check_line_count(self):
        for record in self:
            if not record.fleet_repair_line:
                raise UserError('You cannot create Car Customization without cars.')
            if len(record.fleet_repair_line) > 1:
                raise UserError('You cannot create Car Customization with more than one car.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['sequence'] = self.env['ir.sequence'].next_by_code('fleet.repair') or 'New'
            result = super(FleetRepair, self).create(vals)

            return result

    @api.depends('child_ids.planned_hours')
    def _compute_subtask_planned_hours(self):
        for task in self:
            task.subtask_planned_hours = sum(
                child_task.planned_hours + child_task.subtask_planned_hours for child_task in task.child_ids)

    # @api.onchange('checklist_ids')
    # def onchange_checklist_ids(self):
    #     for rec in self:
    #         if rec.checklist_ids:
    #             checklist_points = self.env['checklist.points'].search([
    #                 ('type_ids', 'in', rec.checklist_ids.ids)
    #             ])
    #             rec.repair_checklist_ids = [(5, 0, 0)] + [
    #                 (0, 0, {
    #                     'name': point.name,
    #                     'description': '',  # يمكن تهيئته من point لو عندك
    #                     'done': False,
    #                 }) for point in checklist_points
    #             ]
    #         else:
    #             rec.repair_checklist_ids = False

    def select_all(self):
        for line in self.repair_checklist_ids:
            line.done = True

    # def button_view_diagnosis(self):
    #     list = []
    #     context = dict(self._context or {})
    #     dig_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id', '=', self.id)])
    #     for order in dig_order_ids:
    #         list.append(order.id)
    #     return {
    #         'name': _('Car Diagnosis'),
    #         'view_type': 'form',
    #         'view_mode': 'list,form',
    #         'res_model': 'fleet.diagnose',
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #         'domain': [('id', 'in',list )],
    #         'context': context,
    #     }

    def button_view_workorder(self):
        list = []
        context = dict(self._context or {})
        work_order_ids = self.env['fleet.workorder'].search([('fleet_repair_id', '=', self.id)])
        for order in work_order_ids:
            list.append(order.id)
        return {
            'name': _('Car Work Order'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'fleet.workorder',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', list)],
            'context': context,
        }

    def button_view_quotation(self):
        list = []
        context = dict(self._context or {})
        quo_order_ids = self.env['sale.order'].search([('state', '=', 'draft'), ('fleet_repair_id', '=', self.id)])
        for order in quo_order_ids:
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

    def button_view_saleorder(self):
        list = []
        context = dict(self._context or {})
        quo_order_ids = self.env['sale.order'].search([('state', '=', 'sale'), ('fleet_repair_id', '=', self.id)])
        for order in quo_order_ids:
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

    def button_view_invoice(self):
        list = []
        inv_list = []
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        so_order_ids = self.env['sale.order'].search([('state', '=', 'sale'), ('fleet_repair_id', '=', self.id)])
        for order in so_order_ids:
            inv_order_ids = self.env['account.move'].search([('origin', '=', order.name)])
            if inv_order_ids:
                for order_id in inv_order_ids:
                    if order_id.id not in list:
                        list.append(order_id.id)

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'list'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(list) > 1:
            result['domain'] = "[('id','in',%s)]" % list
        elif len(list) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = list[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.depends('workorder_id')
    def _compute_workorder_id(self):
        for order in self:
            work_order_ids = self.env['fleet.workorder'].search([('fleet_repair_id', '=', order.id)])
            order.workorder_count = len(work_order_ids)

    @api.depends('diagnose_id')
    def _compute_dignosis_id(self):
        for order in self:
            dig_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id', '=', order.id)])
            order.dig_count = len(dig_order_ids)

    @api.depends('sale_order_id')
    def _compute_quotation_id(self):
        for order in self:
            quo_order_ids = self.env['sale.order'].search([('state', '=', 'draft'), ('fleet_repair_id', '=', order.id)])
            order.quotation_count = len(quo_order_ids)

    @api.depends('confirm_sale_order')
    def _compute_saleorder_id(self):
        for order in self:
            order.quotation_count = 0
            so_order_ids = self.env['sale.order'].search([('state', '=', 'sale'), ('fleet_repair_id', '=', order.id)])
            order.saleorder_count = len(so_order_ids)

    @api.depends('state')
    def _compute_invoice_id(self):
        count = 0
        if self.state == 'invoiced':
            for order in self:
                so_order_ids = self.env['sale.order'].search(
                    [('state', '=', 'sale'), ('fleet_repair_id', '=', order.id)])
                for order in so_order_ids:
                    inv_order_ids = self.env['account.move'].search([('origin', '=', order.name)])
                    if inv_order_ids:
                        self.inv_count = len(inv_order_ids)

    # def diagnosis_created(self):
    #     self.write({'state': 'diagnosis'})

    def quote_created(self):
        self.write({'state': 'quote'})

    def order_confirm(self):
        self.write({'state': 'saleorder'})

    def fleet_confirmed(self):
        self.write({'state': 'confirm'})

    def workorder_created(self):
        self.write({'state': 'workorder'})

    @api.onchange('client_id')
    def onchange_partner_id(self):
        addr = {}
        if self.client_id:
            addr = self.client_id.address_get(['contact'])
            addr['client_phone'] = self.client_id.phone
            addr['client_mobile'] = self.client_id.mobile
            addr['client_email'] = self.client_id.email
        return {'value': addr}

    def action_create_fleet_diagnosis(self):
        Diagnosis_obj = self.env['fleet.diagnose']
        fleet_line_obj = self.env['fleet.repair.line']
        timesheet_obj = self.env['account.analytic.line']
        repair_obj = self.env['fleet.repair'].browse(self._ids[0])
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        if not repair_obj.fleet_repair_line:
            raise UserError('You cannot create Car Diagnosis without Cars.')
        diagnose_vals = {
            'service_rec_no': repair_obj.sequence,
            'name': repair_obj.name,
            'priority': repair_obj.priority,
            'receipt_date': repair_obj.receipt_date,
            'client_id': repair_obj.client_id.id,
            'contact_name': repair_obj.contact_name,
            'phone': repair_obj.phone,
            'client_phone': repair_obj.client_phone,
            'client_mobile': repair_obj.client_mobile,
            'client_email': repair_obj.client_email,
            'fleet_repair_id': repair_obj.id,
            'state': 'draft',
        }
        diagnose_id = Diagnosis_obj.create(diagnose_vals)
        for line in repair_obj.fleet_repair_line:
            fleet_line_vals = {
                'fleet_id': line.fleet_id.id,
                'license_plate': line.license_plate,
                'vin_sn': line.vin_sn,
                'fuel_type': line.fuel_type,
                'model_id': line.model_id.id,
                'service_type': line.service_type.id,
                'guarantee': line.guarantee,
                'guarantee_type': line.guarantee_type,
                'service_detail': line.service_detail,
                # 'diagnose_id': diagnose_id.id,
                'list_of_damage': line.list_of_damage,
                'car_year': line.car_year,
                # 'diagnose_id': diagnose_id.id,
                'state': 'done',
                'source_line_id': line.id,
            }
            fleet_line_obj.create(fleet_line_vals)
            line.write({'state': 'done'})

        for rec in repair_obj.timesheet_ids:
            timesheet_line_vals = {
                'date': rec.date,
                # 'diagnose_id':  diagnose_id.id,
                'project_id': rec.project_id.id,
                'name': rec.name,
                'service_type': rec.service_type.id,
                'unit_amount': rec.unit_amount,
                'company_id': rec.company_id.id,
                'currency_id': rec.currency_id.id,

            }
            timesheet_obj.create(timesheet_line_vals)

        self.write({'state': 'quote'})
        quote_vals = {
            'partner_id': self.client_id.id or False,
            'state': 'draft',
            'client_order_ref': self.name,
            'fleet_repair_id': self.id,
        }
        order_id = self.env['sale.order'].create(quote_vals)
        result = mod_obj._xmlid_lookup("%s.%s" % ('sale', 'action_orders'))
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj._xmlid_lookup("%s.%s" % ('sale', 'view_order_form'))
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = order_id.id or False
        self.write({'sale_order_id': order_id.id, 'state': 'done'})
        return result

    def action_print_receipt(self):
        assert len(self._ids) == 1, 'This option should only be used for a single id at a time'
        return self.env.ref('car_repair_industry.fleet_repair_receipt_id').report_action(self)

    def action_print_label(self):
        if not self.fleet_repair_line:
            raise UserError(_('You cannot print report without Car details'))

        assert len(self._ids) == 1, 'This option should only be used for a single id at a time'
        return self.env.ref('car_repair_industry.fleet_repair_label_id').report_action(self)

    def action_view_quotation(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        order_id = self.sale_order_id.id
        result = mod_obj._xmlid_lookup("%s.%s" % ('sale', 'action_orders'))[1:3]
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj._xmlid_lookup("%s.%s" % ('sale', 'view_order_form'))[1:3]
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = order_id or False
        return result

    def action_view_work_order(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        work_order_id = self.workorder_id.id
        result = mod_obj._xmlid_lookup("%s.%s" % ('car_repair_industry', 'action_fleet_workorder_tree_view'))[1:3]
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj._xmlid_lookup("%s.%s" % ('car_repair_industry', 'view_fleet_workorder_form'))[1:3]
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = work_order_id or False
        return result

    @api.model
    def action_activity_dashboard_redirect(self):
        if self.env.user.has_group('base.group_user'):
            return self.env["ir.actions.actions"]._for_xml_id("car_repair_industry.fleet_repair_dashboard")
        return self.env["ir.actions.actions"]._for_xml_id("car_repair_industry.fleet_repair_dashboard")

    # start
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

    def button_cancel(self):
        self.write({'work_order_state': 'cancel'})

    def button_resume(self):
        self.write({'work_order_state': 'startworking'})

    def button_pause(self):
        self.write({'work_order_state': 'pause'})

    def button_draft(self):
        self.write({'work_order_state': 'draft'})

    def action_start_working(self):
        """ Sets state to start working and writes starting date.
        @return: True
        """
        date_now = datetime.now()
        self.write({'work_order_state': 'startworking', 'date_start': date_now})
        self.sudo().write({'state': 'workorder'})
        return True

    def action_done(self):
        """ Sets state to done, writes finish date and calculates delay.
        @return: True
        """
        delay = 0.0
        date_now = datetime.now()
        date_start = datetime.now()
        date_finished = date_now
        delay += (date_finished - date_start).days * 24
        delay += (date_finished - date_start).seconds / float(60 * 60)
        if delay < 0:
            delay = 0
        self.write({'work_order_state': 'done', 'date_finished': date_now, 'delay': delay})
        if self.sale_order_id:
            self.sale_order_id.sudo().write({'state': 'sale'})
        self.sudo().write({'state': 'work_completed'})
        return True


class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    car_repair_id = fields.Many2one('fleet.repair', 'Car Repair')
    image2 = fields.Binary(string='File Content (base64)', compute='_compute_datas', inverse='_inverse_datas')
    image3 = fields.Binary(string='File Content (base64)', compute='_compute_datas', inverse='_inverse_datas')

    @api.depends('store_fname', 'db_datas', 'file_size')
    @api.depends_context('bin_size')
    def _compute_datas(self):
        if self._context.get('bin_size'):
            for attach in self:
                attach.image2 = human_size(attach.file_size)
                attach.image3 = human_size(attach.file_size)
            return

        for attach in self:
            attach.datas = base64.b64encode(attach.raw or b'')
            attach.image2 = base64.b64encode(attach.raw or b'')
            attach.image3 = base64.b64encode(attach.raw or b'')

    def _inverse_datas(self):
        self._set_attachment_data(lambda attach: base64.b64decode(attach.datas or b''))


class ServiceType(models.Model):
    _name = 'service.type'
    _description = "Service Type"

    name = fields.Char(string='Name',required=True)




class ParkingSlot(models.Model):
    _name = 'parking.slot'
    _description = "Parking Slot"

    name = fields.Char(string='Name',required=True)
    description = fields.Text(string='Description')
    activate = fields.Boolean(string='Active', default=True)
    _sql_constraints = [
        ('unique_name', 'unique (name)', "This name is already exist")
    ]


class CarLift(models.Model):
    _name = 'car.lift'
    _description = "Car Lift"

    name = fields.Char(string='Name',required=True)
    description = fields.Text(string='Description')
    activate = fields.Boolean(string='Active', default=True)
    _sql_constraints = [
        ('unique_name', 'unique (name)', "This name is already exist")
    ]


class FleetRepairLine(models.Model):
    _name = 'fleet.repair.line'
    _description = "Fleet repair line"

    fleet_id = fields.Many2one('fleet.vehicle', 'Car')
    license_plate = fields.Char('License Plate',
                                help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle')
    fuel_type = fields.Selection([('diesel', 'Diesel'),
                                  ('petrol', 'Petrol'),
                                  ('gasoline', 'Gasoline'),
                                  ('full_hybrid', 'Full Hybrid'),
                                  ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
                                  ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
                                  ('cng', 'CNG'),
                                  ('lpg', 'LPG'),
                                  ('hydrogen', 'Hydrogen'),
                                  ('electric', 'Electric'), ('hybrid', 'Hybrid')], 'Fuel Type',
                                 help='Fuel Used by the vehicle')
    guarantee = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Under Guarantee?')
    guarantee_type = fields.Selection(
        [('paid', 'paid'), ('free', 'Free')], string='Guarantee Type')
    service_type = fields.Many2one('service.type', string='Nature of Service')
    fleet_repair_id = fields.Many2one('fleet.repair', string='Car.', copy=False)
    service_detail = fields.Text(string='Service Details')
    diagnostic_result = fields.Text(string='Diagnostic Result')
    diagnose_id = fields.Many2one('fleet.diagnose', string='Car Diagnose', copy=False)
    workorder_id = fields.Many2one('fleet.workorder', string='Car Work Order', copy=False)
    source_line_id = fields.Many2one('fleet.repair.line', string='Source')
    est_ser_hour = fields.Float(string='Estimated Sevice Hours')
    service_product_id = fields.Many2one('product.product', string='Service Product')
    service_product_price = fields.Float('Service Product Price')
    spare_part_ids = fields.One2many('spare.part.line', 'fleet_id', string='Spare Parts Needed')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], 'Status', default="draft", readonly=True, copy=False, help="Gives the status of the fleet Diagnosis.",
        index=True)
    car_year = fields.Char(string="Manufacturing Year")

    list_of_damage = fields.Char(string="Car Manufacturing Year")

    _rec_name = 'fleet_id'

    @api.onchange('service_product_id')
    def onchange_service_product_id(self):
        for price in self:
            price.service_product_price = price.service_product_id.list_price

    def name_get(self):
        if not self._ids:
            return []
        if isinstance(self._ids, (int, int)):
            ids = [self._ids]
        reads = self.read(['fleet_id', 'license_plate'])
        res = []
        for record in reads:
            name = record['license_plate']
            if record['fleet_id']:
                name = record['fleet_id'][1]
            res.append((record['id'], name))
        return res

    def action_add_fleet_diagnosis_result(self):
        for obj in self:
            self.write({'state': 'done'})
        return True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(FleetRepairLine, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        return res

    @api.onchange('fleet_id')
    def onchange_fleet_id(self):
        addr = {}
        if self.fleet_id:
            fleet = self.fleet_id
            addr['license_plate'] = fleet.license_plate
            addr['vin_sn'] = fleet.vin_sn
            addr['fuel_type'] = fleet.fuel_type
            addr['model_id'] = fleet.model_id.id
        return {'value': addr}


class FleetRepairAnalysis(models.Model):
    _name = 'fleet.repair.analysis'
    _description = "Fleet repair analysis"
    _order = 'id desc'

    id = fields.Integer('fleet Id', readonly=True)
    sequence = fields.Char(string='Sequence', readonly=True)
    receipt_date = fields.Date(string='Date of Receipt', readonly=True)
    state = fields.Selection([
        ('draft', 'Received'),
        ('diagnosis', 'In Diagnosis'),
        ('diagnosis_complete', 'Diagnosis Complete'),
        ('quote', 'Quotation Sent'),
        ('saleorder', 'Quotation Approved'),
        ('workorder', 'Work in Progress'),
        ('work_completed', 'Work Completed'),
        ('invoiced', 'Invoiced'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], 'Status', readonly=True, copy=False, help="Gives the status of the fleet repairing.", index=True)
    client_id = fields.Many2one('res.partner', string='Client', readonly=True)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    repair_id = fields.Many2one('fleet.repair', string="Car customization")
    diagnose_id = fields.Many2one('fleet.diagnose', string="Car diagnose")
    workorder_id = fields.Many2one('fleet.workorder', string="Car workorder")
    service_type = fields.Many2one('service.type', string="Service Type")

    @api.depends('service_type', 'unit_amount')
    def _cal_total_cost(self):
        for timesheet in self:
            if timesheet.type_id and (timesheet.unit_amount > 0):
                timesheet.total_cost = timesheet.service_type.cost * timesheet.unit_amount
            else:
                timesheet.total_cost = 0.0


class Technician(models.Model):
    _name = 'technician'
    _description = 'Technician'

    name = fields.Char(string='Name',required=True)
    description = fields.Text(string='Description')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
        ('technician', 'Technician'),
    ], 'Partner Type', default='customer')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        if not name:
            # When no name is provided, call the parent implementation
            return super().name_search(name=name, args=args, operator=operator,
                                       limit=limit)
        # Add search criteria for name, email, and phone
        domain = ['|', '|',
                  ('name', operator, name),
                  ('email', operator, name),
                  ('phone', operator, name)]
        # Combine with existing args
        if args:
            domain = ['&'] + args + domain
        # Use search_fetch to get both IDs and display_name efficiently
        partners = self.search_fetch(domain, ['display_name'], limit=limit)
        # Return in the expected format: [(id, display_name), ...]
        return [(partner.id, partner.display_name) for partner in partners]


class Vehicle(models.Model):
    _inherit = 'fleet.vehicle'

    owner_id = fields.Many2one('res.partner', string='Owner', domain=[('partner_type', '=', 'customer')])
    phone = fields.Char(related='owner_id.phone')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        if not name:
            # When no name is provided, call the parent implementation
            return super().name_search(name=name, args=args, operator=operator,
                                       limit=limit)
        # Add search criteria for name, email, and phone
        domain = ['|', '|',
                  ('name', operator, name),
                  ('owner_id', operator, name),
                  ('phone', operator, name)]
        # Combine with existing args
        if args:
            domain = ['&'] + args + domain
        # Use search_fetch to get both IDs and display_name efficiently
        vehicles = self.search_fetch(domain, ['display_name'], limit=limit)
        # Return in the expected format: [(id, display_name), ...]
        return [(vehicle.id, vehicle.display_name) for vehicle in vehicles]


class FleetRepairChecklist(models.Model):
    _name = 'fleet.repair.checklist'
    _description = "FLEET REPAIR Checklist"

    name = fields.Char('Checklist Name',required=True)
    active = fields.Boolean(default=True)
    description = fields.Char(string="Description")
    done = fields.Boolean(string="Done")
    _sql_constraints = [
        ('unique_name', 'unique (name)', "This name is already exist")
    ]


class FleetRepairChecklistRepair(models.Model):
    _name = 'fleet.repair.checklist.repair'
    _description = "FLEET REPAIR Checklist"

    name = fields.Char('Checklist Name')
    active = fields.Boolean(default=True)
    description = fields.Char(string="Description")
    done = fields.Boolean(string="Done")
    repair_id = fields.Many2one('fleet.repair', string="Checklist", ondelete='cascade')



# class PriceList(models.Model):
#     _name = 'price.list'
#     _description = "Service Type"
#
#     customer_id = fields.Many2one('res.partner', string='Customer', required=True)
#     sale_order_template_id = fields.Many2one('sale.order.template', string='Sale Order Template')
#     order_line = fields.One2many('price.list.line', 'price_list_id', string='Order Lines')
#
#     date = fields.Date(string="Date", default=fields.Date.today)
#     total_amount = fields.Float(string="Total", compute="_compute_total", store=True)
#     currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
#
#     @api.depends('order_line.price_subtotal')
#     def _compute_total(self):
#         for rec in self:
#             rec.total_amount = sum(line.price_subtotal for line in rec.order_line)
#
#     @api.onchange('sale_order_template_id')
#     def _onchange_sale_order_template_id(self):
#         """لو اختار قالب عرض سعر، انسخ منه السطور"""
#         self.order_line = [(5, 0, 0)]
#         if not self.sale_order_template_id:
#             return
#
#         lines = []
#         for tmpl_line in self.sale_order_template_id.sale_order_template_line_ids:
#             lines.append((0, 0, {
#                 'product_id': tmpl_line.product_id.id,
#                 'name': tmpl_line.name or tmpl_line.product_id.name,
#                 'product_uom_qty': tmpl_line.product_uom_qty,
#                 'product_uom': tmpl_line.product_uom_id.id,
#                 'price_unit': tmpl_line.product_id.list_price,
#                 'price_subtotal': tmpl_line.product_id.list_price * tmpl_line.product_uom_qty,
#                 # 'order_id': 1,
#                 'price_list_id': self.id,
#             }))
#         self.order_line = lines
#
#
# class PriceListLine(models.Model):
#     _name = 'price.list.line'
#     _description = "Price List Line"
#
#     price_list_id = fields.Many2one('price.list', string='Price List', ondelete='cascade')
#     product_id = fields.Many2one('product.product', string='Product')
#     name = fields.Char(string='Description')
#     product_uom_qty = fields.Float(string='Quantity', default=1.0)
#     product_uom = fields.Many2one('uom.uom', string='UoM')
#     price_unit = fields.Float(string='Unit Price', related='product_id.lst_price')
#     price_subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
#
#     @api.depends('product_uom_qty', 'price_unit')
#     def _compute_subtotal(self):
#         for line in self:
#             line.price_subtotal = line.product_uom_qty * line.price_unit
#
#
# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
#     _description = 'Sale Order Line'
#
#     price_list_id = fields.Many2one('price.list', string='Order')