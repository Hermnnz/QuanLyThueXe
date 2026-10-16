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

    odo_start = fields.Float(string='ODO lúc giao (km)', copy=False)
    odo_end = fields.Float(string='ODO lúc nhận (km)', copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('status', 'waiting') != 'waiting':
                raise UserError('Xe mới trong phiếu phải ở trạng thái Chưa giao.')
            if vals.get('vehicle_id'):
                vehicle = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
                vals.setdefault('odo_start', vehicle.odometer)
                vals.setdefault('odo_end', vehicle.odometer)
        return super().create(vals_list)

    def action_start_delivery(self):
        if any(rec.status != 'waiting' for rec in self):
            raise UserError('Chỉ bắt đầu giao xe đang Chưa giao.')
        return self.write({'status': 'delivering', 'is_selected': False})

    def action_confirm_delivery(self):
        if any(rec.status not in ('waiting', 'delivering') for rec in self):
            raise UserError('Xe đã bàn giao hoặc đã thu hồi.')
        return self.write({'status': 'renting', 'is_selected': False})

    def action_confirm_return(self):
        if any(rec.status != 'renting' for rec in self):
            raise UserError('Chỉ thu hồi xe đang cho thuê, mỗi lần thuê nhận trả một lần.')
        return self.write({'status': 'returned', 'is_selected': False})

    def write(self, vals):
        transitions = {'waiting': {'delivering', 'renting'},
                       'delivering': {'renting'}, 'renting': {'returned'}, 'returned': set()}
        for rec in self:
            if (rec.status != 'waiting' or vals.get('status', 'waiting') != 'waiting') and any(
                    key in vals and vals[key] != rec[key].id for key in ('vehicle_id', 'ticket_id')):
                raise UserError('Không đổi xe hoặc phiếu sau khi bắt đầu giao.')
            if 'delivery_location' in vals and rec.status in ('renting', 'returned') and vals['delivery_location'] != rec.delivery_location:
                raise UserError('Không đổi địa chỉ giao sau khi bàn giao.')
            if 'return_location' in vals and rec.status == 'returned' and vals['return_location'] != rec.return_location:
                raise UserError('Không đổi địa chỉ nhận sau khi thu hồi.')
            for key, locked in [('odo_start', rec.status != 'waiting'), ('odo_end', rec.status == 'returned')]:
                if key in vals and locked and vals[key] != rec[key]:
                    raise UserError('Không sửa ODO của lần giao/nhận đã xác nhận.')
            target = vals.get('status')
            if target is None or target == rec.status:
                continue
            if target not in transitions.get(rec.status, set()):
                raise UserError('Chuyển trạng thái giao/nhận không hợp lệ hoặc đã thực hiện.')
            contract = rec.ticket_id.contract_id
            if contract.state not in ('confirmed', 'in_progress'):
                raise UserError('Hợp đồng phải được xác nhận hoặc đang thuê để giao/nhận xe.')
            if rec.vehicle_id not in contract.line_ids.mapped('vehicle_id'):
                raise UserError('Xe giao/nhận phải thuộc hợp đồng.')
            now = fields.Datetime.now()
            if rec.status == 'waiting':
                contract._check_vehicle_availability()
                rec.vehicle_id.action_deliver_vehicle(
                    contract.start_date, contract.end_date,
                    odometer_start=vals.get('odo_start', rec.odo_start), checkout_at=now)
                super(RentalOperationTicketVehicle, rec).write({'date_checkout': now})
            elif target == 'renting':
                if rec.vehicle_id.operational_status != 'renting':
                    raise UserError('Trạng thái Fleet không còn khớp với xe đang giao.')
            elif target == 'returned':
                rec.vehicle_id.action_return_vehicle(
                    'pending', odometer_end=vals.get('odo_end', rec.odo_end), checkin_at=now)
                super(RentalOperationTicketVehicle, rec).write({'date_checkin': now})
        return super().write(vals)

    def action_reset_waiting(self):
        if any(rec.status != 'waiting' for rec in self):
            raise UserError('Không đặt lại xe đã bắt đầu giao; cần xử lý theo nghiệp vụ nhận trả.')
        return True

    def unlink(self):
        for rec in self:
            if rec.status != 'waiting':
                raise UserError('Không xóa lịch sử xe đã bắt đầu giao hoặc đã thu hồi.')
            if rec.ticket_id and not self.env.context.get('delete_ticket'):
                raise UserError('Không được phép xóa xe khỏi phiếu bàn giao! Danh sách xe được lấy theo hợp đồng thuê.')
        return super(RentalOperationTicketVehicle, self).unlink()
