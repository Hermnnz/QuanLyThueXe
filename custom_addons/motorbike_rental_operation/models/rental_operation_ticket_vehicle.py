# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class RentalOperationTicketVehicle(models.Model):
    _name = 'rental.operation.ticket.vehicle'
    _description = 'Chi tiết Xe Vận Hành'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', ondelete='cascade')
    rental_order_ref = fields.Char(string='Thuộc Đơn thuê', related='ticket_id.rental_order_ref', readonly=True)

    # Ô tick chọn phục vụ thao tác hàng loạt
    is_selected = fields.Boolean(string='Chọn', default=False)

    # Tiền tệ kế thừa từ phiếu tổng
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='ticket_id.currency_id',
        store=True,
        readonly=True,
    )

    vehicle_id = fields.Many2one('fleet.vehicle', string='Xe', required=True)
    vehicle_price = fields.Monetary(string='Giá tiền xe', default=0.0, currency_field='currency_id')

    # Thông tin vận chuyển - Mặc định lấy từ địa điểm chung của hợp đồng/phiếu
    delivery_location = fields.Char(string='Vị trí giao xe', default='Tại cửa hàng')
    return_location = fields.Char(string='Vị trí nhận xe', default='Tại cửa hàng')

    # Đánh dấu người dùng đã chỉnh riêng địa điểm (không bị ghi đè khi đổi địa điểm chung)
    is_custom_delivery_location = fields.Boolean(string='Chỉnh địa điểm giao riêng', default=False)
    is_custom_return_location = fields.Boolean(string='Chỉnh địa điểm nhận riêng', default=False)

    @api.onchange('delivery_location')
    def _onchange_delivery_location(self):
        if self.status in ('renting', 'returned'):
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được bàn giao (hoặc đã thu hồi), không được phép chỉnh sửa Địa chỉ giao xe!')
        if self.ticket_id and self.delivery_location != self.ticket_id.quick_delivery_location:
            self.is_custom_delivery_location = True

    @api.onchange('return_location')
    def _onchange_return_location(self):
        if self.status == 'returned':
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được thu hồi hoàn tất, không được phép chỉnh sửa Địa chỉ nhận xe!')
        if self.ticket_id and self.return_location != self.ticket_id.quick_return_location:
            self.is_custom_return_location = True

    # Lịch trình
    date_checkout = fields.Datetime(string='Ngày Giao Xe')
    date_checkin = fields.Datetime(string='Ngày Trả Xe')

    status = fields.Selection([
        ('waiting', 'Chưa giao'),
        ('delivering', 'Đang giao xe'),
        ('renting', 'Đang cho thuê'),
        ('returned', 'Đã thu hồi')
    ], string='Trạng thái Xe', default='waiting')

    def _get_vehicle_label(self):
        self.ensure_one()
        if self.vehicle_id:
            return self.vehicle_id.display_name or self.vehicle_id.name or 'N/A'
        return 'không xác định'

    def action_start_delivery(self):
        """Bắt đầu giao xe cho từng chiếc - Cập nhật xe bên Bắc sang Đang cho thuê (renting)"""
        for rec in self:
            name = rec._get_vehicle_label()
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')
            if rec.status == 'renting':
                raise UserError(f'Xe {name} đã được giao!')
            rec.write({
                'status': 'delivering',
                'is_selected': False,
            })
            if rec.vehicle_id:
                rec.vehicle_id.write({'operational_status': 'renting'})

    def action_confirm_delivery(self):
        """Xác nhận đã bàn giao xe thành công cho khách - Xe bên Bắc ở trạng thái Đang cho thuê (renting)"""
        for rec in self:
            name = rec._get_vehicle_label()
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')
            if rec.status == 'renting':
                raise UserError(f'Xe {name} đã được giao!')
            rec.write({
                'status': 'renting',
                'is_selected': False,
            })
            if rec.vehicle_id:
                rec.vehicle_id.write({'operational_status': 'renting'})

    def action_confirm_return(self):
        """Xác nhận thu hồi nhận lại xe từ khách - Mặc định xe bên Bắc chuyển sang Chờ kiểm tra (pending_inspection)"""
        for rec in self:
            name = rec._get_vehicle_label()
            if rec.status in ('waiting', 'delivering'):
                raise UserError(f'Xe {name} chưa được bàn giao!')
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')
            rec.write({
                'status': 'returned',
                'is_selected': False,
            })
            if rec.vehicle_id:
                rec.vehicle_id.write({
                    'operational_status': 'pending_inspection',
                    'technical_ready': False,
                })

    def write(self, vals):
        if 'delivery_location' in vals:
            for rec in self:
                if rec.status in ('renting', 'returned') and vals['delivery_location'] != rec.delivery_location:
                    name = rec._get_vehicle_label()
                    raise UserError(f'Xe {name} đã được bàn giao cho khách (hoặc đã thu hồi), không được phép chỉnh sửa Địa chỉ giao xe!')
        if 'return_location' in vals:
            for rec in self:
                if rec.status == 'returned' and vals['return_location'] != rec.return_location:
                    name = rec._get_vehicle_label()
                    raise UserError(f'Xe {name} đã được thu hồi hoàn tất, không được phép chỉnh sửa Địa chỉ nhận xe!')

        res = super(RentalOperationTicketVehicle, self).write(vals)
        if 'status' in vals:
            for rec in self:
                if rec.vehicle_id:
                    if vals['status'] in ('delivering', 'renting'):
                        rec.vehicle_id.write({'operational_status': 'renting'})
                    elif vals['status'] == 'returned':
                        rec.vehicle_id.write({
                            'operational_status': 'pending_inspection',
                            'technical_ready': False,
                        })
        return res

    def action_reset_waiting(self):
        """Khôi phục về trạng thái chưa giao"""
        for rec in self:
            rec.write({
                'status': 'waiting',
                'is_selected': False,
            })

    def unlink(self):
        for rec in self:
            if rec.ticket_id and not self.env.context.get('delete_ticket'):
                raise UserError('Không được phép xóa xe khỏi phiếu bàn giao! Danh sách xe được lấy theo hợp đồng thuê.')
        return super(RentalOperationTicketVehicle, self).unlink()
