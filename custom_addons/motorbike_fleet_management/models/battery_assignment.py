from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MotorbikeBatteryAssignment(models.Model):
    _name = 'motorbike.battery.assignment'
    _description = 'Lịch sử gắn pin'
    _rec_name = 'battery_id'
    _order = 'installed_at desc, id desc'

    battery_id = fields.Many2one('motorbike.battery', required=True, ondelete='restrict', string='Pin')
    vehicle_id = fields.Many2one('fleet.vehicle', required=True, ondelete='cascade', string='Xe')
    installed_at = fields.Datetime('Thời điểm gắn', required=True, default=fields.Datetime.now)
    removed_at = fields.Datetime('Thời điểm tháo')
    install_odo = fields.Float('ODO lúc gắn')
    remove_odo = fields.Float('ODO lúc tháo')
    reason = fields.Text('Lý do / ghi chú')

    def init(self):
        # One open assignment per vehicle and battery, including concurrent writes.
        self.env.cr.execute('''CREATE UNIQUE INDEX IF NOT EXISTS motorbike_assignment_open_battery
            ON motorbike_battery_assignment (battery_id) WHERE removed_at IS NULL''')
        self.env.cr.execute('''CREATE UNIQUE INDEX IF NOT EXISTS motorbike_assignment_open_vehicle
            ON motorbike_battery_assignment (vehicle_id) WHERE removed_at IS NULL''')

    @api.constrains('battery_id', 'vehicle_id', 'installed_at', 'removed_at', 'install_odo', 'remove_odo')
    def _check_assignment(self):
        for item in self:
            if item.removed_at and item.removed_at < item.installed_at:
                raise ValidationError(_('Thời điểm tháo không được trước thời điểm gắn.'))
            if min(item.install_odo, item.remove_odo) < 0:
                raise ValidationError(_('ODO không được âm.'))
            if item.removed_at and item.remove_odo and item.remove_odo < item.install_odo:
                raise ValidationError(_('ODO lúc tháo không được nhỏ hơn ODO lúc gắn.'))
            domain = [('id', '!=', item.id), '|',
                      ('battery_id', '=', item.battery_id.id), ('vehicle_id', '=', item.vehicle_id.id),
                      '|', ('removed_at', '=', False), ('removed_at', '>', item.installed_at)]
            if item.removed_at:
                domain.append(('installed_at', '<', item.removed_at))
            if self.sudo().search_count(domain):
                raise ValidationError(_('Khoảng gắn pin trùng lịch sử của pin hoặc xe. Hãy đóng lần gắn cũ trước.'))
