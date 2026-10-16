# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class RentalOperationTicket(models.Model):
    _name = 'rental.operation.ticket'
    _description = 'Phiếu Vận Hành Tổng (Giao Nhận)'

    name = fields.Char(string='Mã Vận Hành (Mã OP)', required=True, copy=False, readonly=True, default='Mới')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.operation.ticket')
        return super(RentalOperationTicket, self).create(vals_list)

    # Hợp đồng thuê xe liên kết
    contract_id = fields.Many2one('rental.contract', string='Hợp đồng thuê', required=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng', related='contract_id.customer_id', store=True, readonly=True)

    rental_order_ref = fields.Char(related='contract_id.name', string='Mã hợp đồng', store=True, readonly=True)
    actual_return_date = fields.Datetime(string='Giờ trả thực tế')

    # TỰ ĐỘNG GỌI DỮ LIỆU TỪ HỢP ĐỒNG ĐỂ FILL VÀO PHIẾU BÀN GIAO
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            return

        # Tự động đổ danh sách xe từ hợp đồng sang danh sách xe bàn giao, lấy địa điểm chung mặc định
        vehicle_lines = []
        for line in self.contract_id.line_ids:
            if line.vehicle_id:
                vehicle_vals = {
                    'vehicle_id': line.vehicle_id.id,
                    'vehicle_price': line.daily_rate,
                    'delivery_location': self.quick_delivery_location or 'Tại cửa hàng',
                    'return_location': self.quick_return_location or 'Tại cửa hàng',
                    'date_checkout': self.contract_id.start_date,
                    'date_checkin': self.contract_id.end_date,
                    'status': 'waiting',
                    'is_selected': False,
                    'is_custom_delivery_location': False,
                    'is_custom_return_location': False,
                }
                vehicle_lines.append((0, 0, vehicle_vals))

        # (5, 0, 0) xóa sạch các dòng cũ nếu đổi hợp đồng, sau đó nạp các dòng xe mới
        self.vehicle_detail_ids = [(5, 0, 0)] + vehicle_lines

    expected_checkout = fields.Datetime(string='Ngày Giao Xe', related='contract_id.start_date', store=True, readonly=True)
    rental_duration_days = fields.Integer(string='Thời gian thuê (Ngày)', related='contract_id.rental_days', store=True, readonly=True)
    expected_checkin = fields.Datetime(string='Ngày Trả Xe', related='contract_id.end_date', store=True, readonly=True)

    # Tiền tệ
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='contract_id.currency_id',
        store=True,
        readonly=True,
    )

    # Thiết lập giao/nhận chung của hợp đồng cho toàn bộ xe trong phiếu
    quick_delivery_location = fields.Char(string='Địa điểm Giao chung (Hợp đồng)', default='Tại cửa hàng')
    quick_return_location = fields.Char(string='Địa điểm Nhận chung (Hợp đồng)', default='Tại cửa hàng')

    @api.onchange('quick_delivery_location')
    def _onchange_quick_delivery_location(self):
        for line in self.vehicle_detail_ids:
            if not line.is_custom_delivery_location and line.status in ('waiting', 'delivering'):
                line.delivery_location = self.quick_delivery_location or 'Tại cửa hàng'

    @api.onchange('quick_return_location')
    def _onchange_quick_return_location(self):
        for line in self.vehicle_detail_ids:
            if not line.is_custom_return_location and line.status != 'returned':
                line.return_location = self.quick_return_location or 'Tại cửa hàng'

    def write(self, vals):
        if 'quick_delivery_location' in vals:
            for rec in self:
                if rec.state == 'done':
                    raise UserError('Phiếu vận hành đã hoàn tất, không được phép chỉnh sửa Địa điểm giao chung!')
        if 'quick_return_location' in vals:
            for rec in self:
                if rec.state == 'done':
                    raise UserError('Phiếu vận hành đã hoàn tất, không được phép chỉnh sửa Địa điểm nhận chung!')

        res = super(RentalOperationTicket, self).write(vals)
        if 'quick_delivery_location' in vals or 'quick_return_location' in vals:
            for rec in self:
                for line in rec.vehicle_detail_ids:
                    line_vals = {}
                    if 'quick_delivery_location' in vals and not line.is_custom_delivery_location and line.status in ('waiting', 'delivering'):
                        line_vals['delivery_location'] = rec.quick_delivery_location or 'Tại cửa hàng'
                    if 'quick_return_location' in vals and not line.is_custom_return_location and line.status != 'returned':
                        line_vals['return_location'] = rec.quick_return_location or 'Tại cửa hàng'
                    if line_vals:
                        line.write(line_vals)
        return res

    # Liên kết bảng con chi tiết xe và sự cố
    vehicle_detail_ids = fields.One2many('rental.operation.ticket.vehicle', 'ticket_id', string='Chi tiết Xe')
    incident_ids = fields.One2many('rental.operation.incident.log', 'ticket_id', string='Sự cố & Hư hỏng')

    # Trạng thái phiếu tự động cập nhật theo các xe con
    state = fields.Selection([
        ('waiting', 'Chưa thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn tất')
    ], string='Trạng thái Vận Hành', compute='_compute_state', store=True, default='waiting')

    @api.depends('vehicle_detail_ids.status')
    def _compute_state(self):
        """Tự động tính trạng thái của phiếu tổng dựa trên các xe con"""
        for rec in self:
            if not rec.vehicle_detail_ids:
                rec.state = 'waiting'
                continue
            statuses = rec.vehicle_detail_ids.mapped('status')
            if all(s == 'returned' for s in statuses):
                rec.state = 'done'
                if not rec.actual_return_date:
                    rec.actual_return_date = fields.Datetime.now()
            elif all(s == 'waiting' for s in statuses):
                rec.state = 'waiting'
            else:
                rec.state = 'in_progress'

    # Các trường tách bảng riêng theo trạng thái để dễ quan sát
    waiting_vehicle_ids = fields.Many2many(
        'rental.operation.ticket.vehicle',
        compute='_compute_split_vehicles',
        string='Xe Chưa Giao'
    )
    delivering_vehicle_ids = fields.Many2many(
        'rental.operation.ticket.vehicle',
        compute='_compute_split_vehicles',
        string='Xe Đang Giao'
    )
    renting_vehicle_ids = fields.Many2many(
        'rental.operation.ticket.vehicle',
        compute='_compute_split_vehicles',
        string='Xe Đang Thuê'
    )
    returned_vehicle_ids = fields.Many2many(
        'rental.operation.ticket.vehicle',
        compute='_compute_split_vehicles',
        string='Xe Đã Thu Hồi'
    )

    waiting_count = fields.Integer(string='Chờ giao', compute='_compute_split_vehicles')
    delivering_count = fields.Integer(string='Đang giao', compute='_compute_split_vehicles')
    renting_count = fields.Integer(string='Đang thuê', compute='_compute_split_vehicles')
    returned_count = fields.Integer(string='Đã thu hồi', compute='_compute_split_vehicles')
    total_vehicle_count = fields.Integer(string='Tổng xe', compute='_compute_split_vehicles')

    @api.depends('vehicle_detail_ids', 'vehicle_detail_ids.status')
    def _compute_split_vehicles(self):
        for rec in self:
            rec.waiting_vehicle_ids = rec.vehicle_detail_ids.filtered(lambda l: l.status == 'waiting')
            rec.delivering_vehicle_ids = rec.vehicle_detail_ids.filtered(lambda l: l.status == 'delivering')
            rec.renting_vehicle_ids = rec.vehicle_detail_ids.filtered(lambda l: l.status == 'renting')
            rec.returned_vehicle_ids = rec.vehicle_detail_ids.filtered(lambda l: l.status == 'returned')
            rec.waiting_count = len(rec.waiting_vehicle_ids)
            rec.delivering_count = len(rec.delivering_vehicle_ids)
            rec.renting_count = len(rec.renting_vehicle_ids)
            rec.returned_count = len(rec.returned_vehicle_ids)
            rec.total_vehicle_count = len(rec.vehicle_detail_ids)

    # Thao tác tick chọn hàng loạt
    def action_select_all_vehicles(self):
        """Chọn tất cả xe trong phiếu"""
        for rec in self:
            rec.vehicle_detail_ids.write({'is_selected': True})

    def action_deselect_all_vehicles(self):
        """Bỏ chọn tất cả xe trong phiếu"""
        for rec in self:
            rec.vehicle_detail_ids.write({'is_selected': False})

    # Thao tác tick chọn hàng loạt cho Sự cố
    def action_select_all_incidents(self):
        """Chọn tất cả sự cố trong phiếu"""
        for rec in self:
            rec.incident_ids.write({'is_selected': True})

    def action_deselect_all_incidents(self):
        """Bỏ chọn tất cả sự cố trong phiếu"""
        for rec in self:
            rec.incident_ids.write({'is_selected': False})

    def action_bulk_start_processing_incidents(self):
        """Xác nhận xử lý các sự cố đã chọn"""
        self.ensure_one()
        selected_lines = self.incident_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            selected_lines = self.incident_ids.filtered(lambda l: l.status == 'new')
            if not selected_lines:
                raise UserError('Vui lòng tick chọn ít nhất một sự cố ở trạng thái "Mới"!')

        already_resolved = selected_lines.filtered(lambda l: l.status == 'resolved')
        if already_resolved:
            names = ', '.join(already_resolved.mapped(lambda l: l._get_incident_label()))
            raise UserError(f'Sự cố {names} đã được giải quyết hoàn tất!')

        already_processing = selected_lines.filtered(lambda l: l.status == 'processing')
        if already_processing:
            names = ', '.join(already_processing.mapped(lambda l: l._get_incident_label()))
            raise UserError(f'Sự cố {names} đang trong quá trình xử lý!')

        selected_lines.action_start_processing()

    def action_bulk_resolve_incidents(self):
        """Xác nhận hoàn tất các sự cố đã chọn"""
        self.ensure_one()
        selected_lines = self.incident_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            selected_lines = self.incident_ids.filtered(lambda l: l.status == 'processing')
            if not selected_lines:
                raise UserError('Vui lòng tick chọn ít nhất một sự cố để xác nhận hoàn tất!')

        not_processing = selected_lines.filtered(lambda l: l.status == 'new')
        if not_processing:
            names = ', '.join(not_processing.mapped(lambda l: l._get_incident_label()))
            raise UserError(f'Sự cố {names} chưa được bắt đầu xử lý!')

        already_resolved = selected_lines.filtered(lambda l: l.status == 'resolved')
        if already_resolved:
            names = ', '.join(already_resolved.mapped(lambda l: l._get_incident_label()))
            raise UserError(f'Sự cố {names} đã được hoàn tất trước đó!')

        selected_lines.action_resolve()

    def action_bulk_start_delivery(self):
        """Mở popup xác nhận bắt đầu giao các xe được chọn"""
        self.ensure_one()
        selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.status == 'waiting')
            if not selected_lines:
                raise UserError('Vui lòng tick chọn ít nhất một xe ở trạng thái "Chưa giao"!')

        already_returned = selected_lines.filtered(lambda l: l.status == 'returned')
        if already_returned:
            names = ', '.join(already_returned.mapped(lambda l: l._get_vehicle_label()))
            raise UserError(f'Xe {names} đã được thu hồi!')

        already_renting = selected_lines.filtered(lambda l: l.status == 'renting')
        if already_renting:
            names = ', '.join(already_renting.mapped(lambda l: l._get_vehicle_label()))
            raise UserError(f'Xe {names} đã được giao!')

        names = ', '.join(selected_lines.mapped(lambda l: l._get_vehicle_label()))
        return {
            'name': 'Xác nhận Bắt đầu Giao xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.operation.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_action_type': 'start_delivery',
                'default_vehicle_ids': [(6, 0, selected_lines.ids)],
                'default_message': f'Bạn có chắc chắn xe {names} đã bắt đầu được đi giao chưa?',
            }
        }

    def action_bulk_confirm_delivery(self):
        """Mở popup xác nhận đã giao các xe được chọn (cho phép từ Chưa thực hiện hoặc Đang giao)"""
        self.ensure_one()
        selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.status in ('waiting', 'delivering'))
            if not selected_lines:
                raise UserError('Vui lòng tick chọn ít nhất một xe để xác nhận đã giao!')

        already_returned = selected_lines.filtered(lambda l: l.status == 'returned')
        if already_returned:
            names = ', '.join(already_returned.mapped(lambda l: l._get_vehicle_label()))
            raise UserError(f'Xe {names} đã được thu hồi!')

        already_renting = selected_lines.filtered(lambda l: l.status == 'renting')
        if already_renting:
            names = ', '.join(already_renting.mapped(lambda l: l._get_vehicle_label()))
            raise UserError(f'Xe {names} đã được giao!')

        names = ', '.join(selected_lines.mapped(lambda l: l._get_vehicle_label()))
        return {
            'name': 'Xác nhận Đã Giao xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.operation.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_action_type': 'confirm_delivery',
                'default_vehicle_ids': [(6, 0, selected_lines.ids)],
                'default_message': f'Bạn có chắc chắn xe {names} đã được bàn giao cho khách hàng chưa?',
            }
        }

    def action_bulk_confirm_return(self):
        """Mở popup xác nhận thu hồi các xe được chọn (bắt buộc phải ở trạng thái Đã giao xe)"""
        self.ensure_one()
        selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.status == 'renting')
            if not selected_lines:
                raise UserError('Vui lòng tick chọn ít nhất một xe để xác nhận thu hồi!')

        not_delivered = selected_lines.filtered(lambda l: l.status in ('waiting', 'delivering'))
        if not_delivered:
            names = ', '.join(not_delivered.mapped(lambda l: l._get_vehicle_label()))
            raise UserError(f'Xe {names} chưa được bàn giao!')

        already_returned = selected_lines.filtered(lambda l: l.status == 'returned')
        if already_returned:
            names = ', '.join(already_returned.mapped(lambda l: l._get_vehicle_label()))
            raise UserError(f'Xe {names} đã được thu hồi!')

        names = ', '.join(selected_lines.mapped(lambda l: l._get_vehicle_label()))
        return {
            'name': 'Xác nhận Thu hồi xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.operation.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_action_type': 'confirm_return',
                'default_vehicle_ids': [(6, 0, selected_lines.ids)],
                'default_message': f'Bạn chắc chắn xe {names} đã thu hồi hoàn tất chưa?',
            }
        }

    def action_view_vehicles(self):
        """Hàm hỗ trợ nút thống kê trên form"""
        return True

    def action_reset_waiting(self):
        """Khôi phục toàn bộ xe về trạng thái chờ giao"""
        for rec in self:
            rec.vehicle_detail_ids.action_reset_waiting()

    def unlink(self):
        return super(RentalOperationTicket, self.with_context(delete_ticket=True)).unlink()
