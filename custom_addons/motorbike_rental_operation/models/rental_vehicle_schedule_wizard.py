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

        vals = {}
        if self.delivery_location:
            vals['delivery_location'] = self.delivery_location
            vals['is_custom_delivery_location'] = True
        if self.delivery_time:
            vals['delivery_time'] = self.delivery_time
            vals['is_custom_delivery_time'] = True
        if self.return_location:
            vals['return_location'] = self.return_location
            vals['is_custom_return_location'] = True

        if vals:
            self.vehicle_ids.write(vals)

        # Bỏ tick chọn sau khi cập nhật thành công
        self.vehicle_ids.write({'is_selected': False})
        return {'type': 'ir.actions.act_window_close'}
