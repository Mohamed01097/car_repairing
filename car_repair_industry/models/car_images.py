from odoo import models, fields, api

class MaintenanceImage(models.Model):
    _name = "maintenance.image"
    _description = "Maintenance Photos"

    maintenance_id = fields.Many2one('fleet.repair', string="Maintenance Request", ondelete='cascade')
    image = fields.Binary("Image", attachment=True)
    image_type = fields.Selection([
        ('before', 'Before Maintenance'),
        ('after', 'After Maintenance'),
    ], string="Image Type")
    description = fields.Char("Description")
