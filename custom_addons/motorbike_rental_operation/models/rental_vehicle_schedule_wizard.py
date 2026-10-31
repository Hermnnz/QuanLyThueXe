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
    return_time = fields.Char(
        string='Giờ thu hồi xe', 
        placeholder='VD: 12:00 hoặc 18:00',
        help='Thời gian thu hồi xe dự kiến (VD: 18:00)'
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

            # Xe chưa thu hồi (chờ giao, đang giao hoặc đang thuê) được phép sửa thông tin thu hồi (địa điểm & giờ thu hồi)
            if veh.status != 'returned':
                if self.return_location and self.return_location != veh.return_location:
                    veh_vals['return_location'] = self.return_location
                    veh_vals['is_custom_return_location'] = True
                if self.return_time and self.return_time != veh.return_time:
                    veh_vals['return_time'] = self.return_time
                    veh_vals['is_custom_return_time'] = True

            if veh_vals:
                veh.write(veh_vals)

        # Đồng bộ trực tiếp vào các biên lai giao xe chưa hoàn tất (nếu có)
        receipts_to_update = self.vehicle_ids.mapped('delivery_receipt_id').filtered(lambda r: r.state != 'delivered')
        for r in receipts_to_update:
            r_vals = {}
            if self.delivery_location:
                r_vals['delivery_location'] = self.delivery_location
            if self.delivery_time:
                r_vals['delivery_time'] = self.delivery_time
            if r_vals:
                r.write(r_vals)

        # Đồng bộ trực tiếp vào các biên lai thu hồi xe chưa hoàn tất (nếu có)
        ret_receipts_to_update = self.vehicle_ids.mapped('return_receipt_id').filtered(lambda r: r.state != 'returned')
        for r in ret_receipts_to_update:
            r_vals = {}
            if self.return_location:
                r_vals['return_location'] = self.return_location
            if self.return_time:
                r_vals['return_time'] = self.return_time
            if r_vals:
                r.write(r_vals)

        # Bỏ tick chọn sau khi cập nhật thành công
        self.vehicle_ids.write({'is_selected': False})
        return {'type': 'ir.actions.act_window_close'}
