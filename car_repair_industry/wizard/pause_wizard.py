from odoo import models, fields, api
from datetime import datetime
class PauseReasonWizard(models.TransientModel):
    _name = 'pause.reason.wizard'
    _description = "Pause Reason Wizard"

    workorder_id = fields.Many2one('fleet.workorder', string="Work Order", required=True)
    reason = fields.Text(string="Reason", required=True)

    def action_confirm(self):
        """Save pause reason and update work order"""
        workorder = self.workorder_id
        now = datetime.now()

        # ✅ احسب الوقت والمدة لو حابب
        workorder.write({
            'pause_time': now,
            'state': 'pause',
        })

        # ✅ أنشئ سطر جديد في سجل التايمر
        self.env['workorder.timer.line'].create({
            'workorder_id': workorder.id,
            'action': 'pause',
            'action_time': now,
            'reason': self.reason,
        })
        return {'type': 'ir.actions.act_window_close'}
