import math

from odoo import api, models
from odoo.exceptions import ValidationError, UserError


class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    @api.constrains('value', 'date', 'vehicle_id')
    def _check_motorbike_odometer(self):
        for log in self.filtered('vehicle_id.is_electric_motorbike'):
            if not math.isfinite(log.value):
                raise ValidationError('ODO phải là một số hữu hạn.')
            if log.value < 0:
                raise ValidationError('ODO không được âm.')
            if not log.date:
                raise ValidationError('Cần ngày ghi nhận ODO.')
            # Tối ưu: Đẩy kiểm tra vi phạm xuống PostgreSQL Index, dừng ngay ở dòng đầu tiên thay vì kéo toàn bộ về RAM
            if self.sudo().search_count([
                ('vehicle_id', '=', log.vehicle_id.id),
                ('id', '!=', log.id),
                ('date', '!=', False),
                '|',
                '&', ('date', '<', log.date), ('value', '>', log.value),
                '&', ('date', '>', log.date), ('value', '<', log.value),
            ], limit=1):
                raise ValidationError('ODO phải không giảm theo ngày ghi nhận.')

    def unlink(self):
        if self.filtered('vehicle_id.is_electric_motorbike'):
            raise UserError('Lịch sử ODO là dữ liệu kiểm toán kỹ thuật; không được phép xóa.')
        return super().unlink()
