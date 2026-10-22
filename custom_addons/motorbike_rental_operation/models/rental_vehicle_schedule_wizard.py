# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class RentalVehicleScheduleWizard(models.TransientModel):
    _name = 'rental.vehicle.schedule.wizard'
    _description = 'Cập nhật Địa điểm & Thời gian Giao/Thu hồi Xe'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành')
    vehicle_ids = fields.Many2many(
        'rental.operation.ticket.vehicle',
        'rental_veh_sched_wiz_vehicle_rel',
        'wizard_id',
        'vehicle_id',
        string='Xe được chọn'
    )
    vehicle_count = fields.Integer(string='Số lượng xe', compute='_compute_vehicle_count')

    delivery_location = fields.Char(
        string='Địa điểm giao xe', 
        default='Tại cửa hàng',
        help='Địa điểm giao xe cho các xe được chọn'
    )
    delivery_time = fields.Char(
        string='Giờ giao xe', 
        placeholder='VD: 08:30 hoặc 14:00',
        help='Thời gian giao xe dự kiến (VD: 08:30)'
    )
    return_location = fields.Char(
        string='Địa điểm thu hồi xe', 
        default='Tại cửa hàng',
        help='Địa điểm thu hồi xe cho các xe được chọn'
    )

    @api.depends('vehicle_ids')
    def _compute_vehicle_count(self):
        for rec in self:
            rec.vehicle_count = len(rec.vehicle_ids)

    def action_apply(self):
        self.ensure_one()
        if not self.vehicle_ids:
            raise UserError('Không có xe nào được chọn để cập nhật!')

        for veh in self.vehicle_ids:
            veh_vals = {}
            # Xe chưa giao mới được sửa thông tin giao xe (địa điểm & giờ giao)
            if veh.status in ('waiting', 'delivering'):
                if self.delivery_location and self.delivery_location != veh.delivery_location:
                    veh_vals['delivery_location'] = self.delivery_location
                    veh_vals['is_custom_delivery_location'] = True
                if self.delivery_time and self.delivery_time != veh.delivery_time:
                    veh_vals['delivery_time'] = self.delivery_time
                    veh_vals['is_custom_delivery_time'] = True

            # Xe chưa thu hồi (chờ giao, đang giao hoặc đang thuê) được phép sửa địa điểm thu hồi
            if veh.status != 'returned':
                if self.return_location and self.return_location != veh.return_location:
                    veh_vals['return_location'] = self.return_location
                    veh_vals['is_custom_return_location'] = True

            if veh_vals:
                veh.write(veh_vals)

        # Bỏ tick chọn sau khi cập nhật thành công
        self.vehicle_ids.write({'is_selected': False})
        return {'type': 'ir.actions.act_window_close'}
