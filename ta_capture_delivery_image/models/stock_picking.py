from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    capture_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'stock.picking'), ('name', '=like', 'Captured on %')], string='Attachments')

    def action_camera_capture(self):
        return self.capture_ids.action_camera_capture('stock.picking', self.id)

class FleetWorkorder(models.Model):
    _inherit = 'fleet.workorder'

    capture_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'fleet.workorder'), ('name', '=like', 'Captured on %'),('image_type','=','before')], string='Attachments')
    after_capture_ids = fields.One2many('ir.attachment', 'res_id',
                                  domain=[('res_model', '=', 'fleet.workorder'), ('name', '=like', 'Captured on %'),('image_type','=','after')],
                                  string='Attachments')

    def action_camera_capture(self):
        image_type = 'before'
        if self.state == 'done':
            image_type = 'after'
        print(self.capture_ids.action_camera_capture('fleet.workorder', self.id,image_type))
        return self.capture_ids.action_camera_capture('fleet.workorder', self.id,image_type)