from datetime import datetime
import pytz
from odoo import api, models,fields


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    image_type = fields.Selection([
        ('before', 'Before Installation'),
        ('after', 'After Installation'),
    ], string='Image Type')

    @api.model
    def action_camera_capture(self, res_mode, res_id,image_type):
        return {
            'type': 'ir.actions.client',
            'name': 'Image Capture',
            'tag': 'camera_capture',
            'context': {
                'no_breadcrumbs': True,
                'res_id': res_id,
                'res_model': res_mode,
                'default_image_type': 'after',
            }
        }
    
    def action_capture_show(self):
        base64String = 'data:%s;base64,%s' %(self.mimetype, self.datas.decode('utf-8'))
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

    @api.model
    def camera_save_capture(self, res_model, res_id, data, mimetype, note=''):
        model = self.env[res_model].sudo().browse(res_id)
        if model:
            try:
                image_type = 'before'
                if hasattr(model, 'state') and model.state == 'done':
                    image_type = 'after'
                # Get current time in UTC timezone
                utc_now = datetime.now(pytz.UTC)
                filename = 'Captured on %s' %(utc_now.strftime('%H:%M:%S %d/%m/%Y'))
                data = data.split(',')[1]
                data += "=" * ((4 - len(data) % 4) % 4) 
                val={
                    'name': filename,
                    'type': 'binary',
                    'datas': data,
                    'res_model': res_model,
                    'res_id': res_id,
                    'store_fname': filename,
                    'mimetype': mimetype,
                    'image_type': image_type,
                }
                attach = self.env['ir.attachment'].sudo().create(val)
                print(attach)
                message_body = 'Captured on %s' % utc_now.strftime('%H:%M:%S %d/%m/%Y')
                if note:
                    message_body += ' with note: %s' % note
                # model.message_post(body=message_body, attachment_ids=[attach.id])
                return {'result': ('Image captured successfully.')}
            except Exception as e:
                return {'warning': ('Cannot save captured image with error: %s'% e)}
        else:
            return {'warning': ('Record was not found.')}
