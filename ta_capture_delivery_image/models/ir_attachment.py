from datetime import datetime
import pytz
from odoo import api, models,fields


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    image_type = fields.Selection([
        ('before', 'Before Installation'),
        ('permit', 'Permit Installation'),
        ('after', 'After Installation'),
    ], string='Image Type')

    @api.model
    def action_camera_capture(self, res_mode, res_id, image_type):
        return {
            'type': 'ir.actions.client',
            'name': 'Image Capture',
            'tag': 'camera_capture',
            'context': {
                'no_breadcrumbs': True,
                'res_id': res_id,
                'res_model': res_mode,
                'default_image_type': image_type,  # ✅ نحفظ نوع الصورة في الـ context
            }
        }

    def action_capture_show(self):
        base64String = 'data:%s;base64,%s' % (self.mimetype, self.datas.decode('utf-8'))
        return {
            'type': 'ir.actions.client',
            'name': 'Image Capture',
            'tag': 'capture_show',
            'context': {
                'no_breadcrumbs': True,
                'mimetype': self.mimetype,
                'capture_base64String': base64String,
            }
        }

    def action_quick_delete(self):
        for rec in self:
            rec.unlink()
    @api.model
    def camera_save_capture(self, res_model, res_id, data, mimetype, note='', image_type='before'):
        model = self.env[res_model].sudo().browse(res_id)
        if not model:
            return {'warning': 'Record was not found.'}
        try:
            utc_now = datetime.now(pytz.UTC)
            filename = f'Captured on {utc_now.strftime("%H:%M:%S %d/%m/%Y")}'
            data = data.split(',')[1]
            data += "=" * ((4 - len(data) % 4) % 4)
            val = {
                'name': filename,
                'type': 'binary',
                'datas': data,
                'res_model': res_model,
                'res_id': res_id,
                'store_fname': filename,
                'mimetype': mimetype,
                'image_type': image_type,  # ✅ النوع القادم من الـ JS
            }
            self.env['ir.attachment'].sudo().create(val)
            return {'result': f'Image ({image_type}) captured successfully.'}
        except Exception as e:
            return {'warning': f'Cannot save captured image with error: {e}'}
