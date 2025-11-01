from odoo import models, fields


# class StockPicking(models.Model):
#     _inherit = 'stock.picking'
#
#     capture_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'stock.picking'), ('name', '=like', 'Captured on %')], string='Attachments')
#
#     def action_camera_capture(self):
#         return self.capture_ids.action_camera_capture('stock.picking', self.id)

class FleetWorkorder(models.Model):
    _inherit = 'fleet.workorder'

    capture_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[('res_model', '=', 'fleet.workorder'), ('image_type', '=', 'before')],
        string='Before Installation Images'
    )
    permit_capture_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[('res_model', '=', 'fleet.workorder'), ('image_type', '=', 'permit')],
        string='Permit Installation Images'
    )
    after_capture_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[('res_model', '=', 'fleet.workorder'), ('image_type', '=', 'after')],
        string='After Installation Images'
    )

    def action_camera_capture_before(self):
        """فتح الكاميرا لصور قبل التركيب"""
        return self.env['ir.attachment'].action_camera_capture('fleet.workorder', self.id, 'before')

    def action_camera_capture_permit(self):
        """فتح الكاميرا لصور قبل التركيب"""
        return self.env['ir.attachment'].action_camera_capture('fleet.workorder', self.id, 'permit')

    def action_camera_capture_after(self):
        """فتح الكاميرا لصور بعد التركيب"""
        return self.env['ir.attachment'].action_camera_capture('fleet.workorder', self.id, 'after')