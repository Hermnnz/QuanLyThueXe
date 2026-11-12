import math

from odoo import api, models
from odoo.exceptions import ValidationError, UserError


class FleetVehicleOdometer(models.Model):
    """Quản lý lịch sử ODO, chống tua ngược km và bảo vệ tính toàn vẹn dữ liệu."""
    _inherit = 'fleet.vehicle.odometer'

    @api.constrains('value', 'date', 'vehicle_id')
    def _check_motorbike_odometer(self):
        """Kiểm tra tính đơn điệu không giảm của ODO theo thời gian để chống tua ngược đồng hồ km."""
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
        """Cấm xóa lịch sử ODO nhằm bảo toàn dữ liệu kiểm toán kỹ thuật phương tiện."""
        if self.filtered('vehicle_id.is_electric_motorbike'):
            raise UserError('Lịch sử ODO là dữ liệu kiểm toán kỹ thuật; không được phép xóa.')
        return super().unlink()
