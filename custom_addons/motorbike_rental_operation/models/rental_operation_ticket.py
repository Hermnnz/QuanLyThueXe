# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class RentalOperationTicket(models.Model):
    _name = 'rental.operation.ticket'
    _description = 'Phiếu Vận Hành Tổng (Giao Nhận)'

    name = fields.Char(string='Mã Vận Hành (Mã OP)', required=True, copy=False, readonly=True, default='Mới')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.operation.ticket')
        tickets = super(RentalOperationTicket, self).create(vals_list)
        for ticket in tickets:
            if ticket.state != 'contract_cancelled' and any(v.status in ('renting', 'returned') for v in ticket.vehicle_detail_ids):
                ticket._sync_contract_in_progress()
        return tickets

    def _sync_contract_in_progress(self):
        """Chuyển hợp đồng liên kết sang Đang thuê ('in_progress') nếu có xe trong phiếu được giao"""
        for rec in self:
            if rec.state == 'contract_cancelled':
                continue
            contract = rec.contract_id
            if contract and contract.state == 'confirmed':
                contract.sudo().write({'state': 'in_progress'})

    # Danh sách hợp đồng khả dụng được lọc động
    available_contract_ids = fields.Many2many(
        'rental.contract',
        compute='_compute_available_contract_ids',
        string='Hợp đồng khả dụng'
    )

    # Hợp đồng thuê xe liên kết
    contract_id = fields.Many2one(
        'rental.contract',
        string='Hợp đồng thuê',
        required=True,
        domain="[('id', 'in', available_contract_ids)]"
    )
    customer_id = fields.Many2one('res.partner', string='Khách hàng', related='contract_id.customer_id', store=True, readonly=True)
    customer_phone = fields.Char(string='Số điện thoại', related='customer_id.phone', store=True, readonly=True)

    rental_order_ref = fields.Char(related='contract_id.name', string='Mã hợp đồng', store=True, readonly=True)
    contract_state = fields.Selection(
        related='contract_id.state',
        string='Trạng thái hợp đồng',
        store=True,
        readonly=True
    )
    actual_delivery_date = fields.Datetime(string='Thời gian giao thực tế')
    actual_return_date = fields.Datetime(string='Thời gian thu hồi thực tế')

    @api.depends('contract_id')
    def _compute_available_contract_ids(self):
        """Lọc động danh sách hợp đồng khi chọn trong phiếu vận hành:
        1. Không cho hiển thị hợp đồng đã tồn tại trong bảng giao xe
        2. Chỉ hiển thị các hợp đồng ở trạng thái 'Đã xác nhận' (confirmed)
        """
        all_tickets = self.env['rental.operation.ticket'].search([])
        for rec in self:
            rec_origin_id = rec._origin.id if rec._origin else (rec.id if isinstance(rec.id, int) else False)
            other_tickets = all_tickets.filtered(lambda t: t.id != rec_origin_id) if rec_origin_id else all_tickets

            # Thu thập ID hợp đồng đã có trong bảng giao xe khác
            used_contract_ids = set(other_tickets.mapped('contract_id.id'))

            # Tìm danh sách hợp đồng ứng viên (chỉ lấy hợp đồng ở trạng thái 'Đã xác nhận')
            candidate_contracts = self.env['rental.contract'].search([('state', '=', 'confirmed')])
            valid_ids = [c.id for c in candidate_contracts if c.id not in used_contract_ids]

            # Đảm bảo hợp đồng đang lưu của phiếu hiện tại vẫn được giữ lại để hiển thị
            if rec.contract_id and rec.contract_id.id not in valid_ids:
                valid_ids.append(rec.contract_id.id)

            rec.available_contract_ids = self.env['rental.contract'].browse(valid_ids)

    @api.constrains('contract_id')
    def _check_contract_id_filter(self):
        """Ràng buộc kiểm tra khi lưu phiếu:
        Không cho chọn hợp đồng đã tồn tại trong bảng giao xe
        """
        for rec in self:
            if not rec.contract_id:
                continue

            # Kiểm tra hợp đồng đã tồn tại trong bảng giao xe
            duplicate_ticket = self.search([
                ('id', '!=', rec.id),
                ('contract_id', '=', rec.contract_id.id)
            ], limit=1)
            if duplicate_ticket:
                raise ValidationError(
                    _('Không thể chọn hợp đồng "%(contract)s"! Hợp đồng này đã tồn tại trong bảng giao xe (Phiếu vận hành: %(ticket)s).') % {
                        'contract': rec.contract_id.display_name or rec.contract_id.name,
                        'ticket': duplicate_ticket.name,
                    }
                )

    # TỰ ĐỘNG GỌI DỮ LIỆU TỪ HỢP ĐỒNG ĐỂ FILL VÀO PHIẾU BÀN GIAO
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        self._compute_available_contract_ids()
        if not self.contract_id:
            return

        # Tự động đổ danh sách xe từ hợp đồng sang danh sách xe bàn giao, lấy địa điểm chung mặc định
        vehicle_lines = []
        for line in self.contract_id.line_ids:
            if line.vehicle_id:
                has_electric = getattr(line.vehicle_id, 'is_electric_motorbike', False)
                checkout_date = False
                checkout_time = False
                if self.contract_id.start_date:
                    loc_dt = fields.Datetime.context_timestamp(self, self.contract_id.start_date)
                    checkout_date = loc_dt.date()
                    checkout_time = loc_dt.strftime('%H:%M')
                checkin_date = False
                checkin_time = False
                if self.contract_id.end_date:
                    loc_dt_in = fields.Datetime.context_timestamp(self, self.contract_id.end_date)
                    checkin_date = loc_dt_in.date()
                    checkin_time = loc_dt_in.strftime('%H:%M')
                vehicle_vals = {
                    'vehicle_id': line.vehicle_id.id,
                    'vehicle_price': line.daily_rate,
                    'delivery_location': 'Tại cửa hàng',
                    'return_location': 'Tại cửa hàng',
                    'delivery_date': checkout_date,
                    'return_date': checkin_date,
                    'delivery_time': checkout_time or False,
                    'return_time': checkin_time or False,
                    'date_checkout': self.contract_id.start_date,
                    'date_checkin': self.contract_id.end_date,
                    'actual_delivery_date': False,
                    'actual_return_date': False,
                    'status': 'waiting',
                    'is_selected': False,
                    'is_custom_delivery_location': False,
                    'is_custom_return_location': False,
                    'is_custom_delivery_date': False,
                    'is_custom_return_date': False,
                    'is_custom_delivery_time': False,
                    'is_custom_return_time': False,
                    'qty_helmet': 2,
                    'qty_raincoat': 2,
                    'qty_phone_holder': 1,
                    'qty_charger': 1 if has_electric else 0,
                    'delivery_visual_note': self.env['rental.operation.ticket.vehicle']._get_vehicle_exterior_condition(line.vehicle_id),
                }
                vehicle_lines.append((0, 0, vehicle_vals))

        # (5, 0, 0) xóa sạch các dòng cũ nếu đổi hợp đồng, sau đó nạp các dòng xe mới
        self.vehicle_detail_ids = [(5, 0, 0)] + vehicle_lines

    expected_checkout = fields.Datetime(string='Thời gian giao xe', related='contract_id.start_date', store=True, readonly=True)
    rental_duration_days = fields.Integer(string='Thời gian thuê (Ngày)', related='contract_id.rental_days', store=True, readonly=True)
    expected_checkin = fields.Datetime(string='Thời gian thu hồi', related='contract_id.end_date', store=True, readonly=True)

    # Tiền tệ
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='contract_id.currency_id',
        store=True,
        readonly=True,
    )

    # Thiết lập giao/thu hồi chung của hợp đồng cho toàn bộ xe trong phiếu
    quick_delivery_location = fields.Char(string='Vị trí giao xe', default='Tại cửa hàng')
    quick_return_location = fields.Char(string='Vị trí thu hồi xe', default='Tại cửa hàng')
    quick_delivery_time = fields.Char(string='Giờ giao xe', help='Giờ giao xe mặc định (VD: 08:30)')

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

    @api.onchange('quick_delivery_time')
    def _onchange_quick_delivery_time(self):
        for line in self.vehicle_detail_ids:
            if not line.is_custom_delivery_time and line.status in ('waiting', 'delivering'):
                line.delivery_time = self.quick_delivery_time or False

    def write(self, vals):
        for rec in self:
            if rec.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành này đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không được phép chỉnh sửa!'))
            if rec.state == 'done':
                if 'quick_delivery_location' in vals:
                    raise UserError('Phiếu vận hành đã hoàn tất, không được phép chỉnh sửa Địa điểm giao chung!')
                if 'quick_return_location' in vals:
                    raise UserError('Phiếu vận hành đã hoàn tất, không được phép chỉnh sửa Địa điểm thu hồi chung!')
                if 'quick_delivery_time' in vals:
                    raise UserError('Phiếu vận hành đã hoàn tất, không được phép chỉnh sửa Giờ giao chung!')

        res = super(RentalOperationTicket, self).write(vals)
        if 'contract_id' in vals or 'vehicle_detail_ids' in vals:
            for ticket in self:
                if ticket.state != 'contract_cancelled' and any(v.status in ('renting', 'returned') for v in ticket.vehicle_detail_ids):
                    ticket._sync_contract_in_progress()

        if 'quick_delivery_location' in vals or 'quick_return_location' in vals or 'quick_delivery_time' in vals:
            for rec in self:
                for line in rec.vehicle_detail_ids:
                    line_vals = {}
                    if 'quick_delivery_location' in vals and not line.is_custom_delivery_location and line.status in ('waiting', 'delivering'):
                        line_vals['delivery_location'] = rec.quick_delivery_location or 'Tại cửa hàng'
                    if 'quick_return_location' in vals and not line.is_custom_return_location and line.status != 'returned':
                        line_vals['return_location'] = rec.quick_return_location or 'Tại cửa hàng'
                    if 'quick_delivery_time' in vals and not line.is_custom_delivery_time and line.status in ('waiting', 'delivering'):
                        line_vals['delivery_time'] = rec.quick_delivery_time or False
                    if line_vals:
                        line.write(line_vals)
        return res

    # Liên kết bảng con chi tiết xe, sự cố và biên lai giao xe
    vehicle_detail_ids = fields.One2many('rental.operation.ticket.vehicle', 'ticket_id', string='Chi tiết Xe')
    incident_ids = fields.One2many('rental.operation.incident.log', 'ticket_id', string='Sự cố & Hư hỏng')
    receipt_ids = fields.One2many('rental.delivery.receipt', 'ticket_id', string='Biên lai giao xe')
    receipt_count = fields.Integer(string='Số biên lai', compute='_compute_receipt_count')
    has_selected_receipts = fields.Boolean(compute='_compute_has_selected_receipts')

    return_receipt_ids = fields.One2many('rental.return.receipt', 'ticket_id', string='Biên lai thu hồi xe')
    return_receipt_count = fields.Integer(string='Số biên lai thu hồi', compute='_compute_return_receipt_count')
    has_selected_return_receipts = fields.Boolean(compute='_compute_has_selected_return_receipts')

    @api.depends('receipt_ids')
    def _compute_receipt_count(self):
        for rec in self:
            rec.receipt_count = len(rec.receipt_ids)

    @api.depends('receipt_ids.is_selected')
    def _compute_has_selected_receipts(self):
        for rec in self:
            rec.has_selected_receipts = any(r.is_selected for r in rec.receipt_ids)

    @api.depends('return_receipt_ids')
    def _compute_return_receipt_count(self):
        for rec in self:
            rec.return_receipt_count = len(rec.return_receipt_ids)

    @api.depends('return_receipt_ids.is_selected')
    def _compute_has_selected_return_receipts(self):
        for rec in self:
            rec.has_selected_return_receipts = any(r.is_selected for r in rec.return_receipt_ids)

    vehicle_exchange_ids = fields.One2many(
        'rental.vehicle.exchange', 'ticket_id', string='Danh sách Đổi xe'
    )
    vehicle_exchange_count = fields.Integer(
        string='Số lượt đổi xe', compute='_compute_vehicle_exchange_count'
    )

    @api.depends('vehicle_exchange_ids')
    def _compute_vehicle_exchange_count(self):
        for rec in self:
            rec.vehicle_exchange_count = len(rec.vehicle_exchange_ids)

    has_selected_exchanges = fields.Boolean(compute='_compute_has_selected_exchanges')

    @api.depends('vehicle_exchange_ids.is_selected')
    def _compute_has_selected_exchanges(self):
        for rec in self:
            rec.has_selected_exchanges = any(e.is_selected for e in rec.vehicle_exchange_ids)

    def action_select_all_exchanges(self):
        """Tick chọn tất cả bản ghi đổi xe"""
        self.ensure_one()
        self.vehicle_exchange_ids.write({'is_selected': True})

    def action_deselect_all_exchanges(self):
        """Bỏ tick chọn tất cả bản ghi đổi xe"""
        self.ensure_one()
        self.vehicle_exchange_ids.write({'is_selected': False})

    def action_bulk_start_exchanges(self):
        """Bắt đầu đổi xe cho các bản ghi được tick chọn"""
        self.ensure_one()
        selected = self.vehicle_exchange_ids.filtered(lambda e: e.is_selected)
        if not selected:
            selected = self.vehicle_exchange_ids.filtered(lambda e: e.status != 'cancelled')
            if not selected:
                raise UserError(_('Không có bản ghi đổi xe nào để hủy!'))
        drafts = selected.filtered(lambda e: e.status == 'draft')
        if not drafts:
            raise UserError(_('Không có bản ghi nào ở trạng thái "Chưa thực hiện" trong số các mục đã chọn!'))
        drafts.action_start()

        selected.write({'is_selected': False})

    def action_bulk_done_exchanges(self):
        """Hoàn thành đổi xe cho các bản ghi được tick chọn"""
        self.ensure_one()
        selected = self.vehicle_exchange_ids.filtered(lambda e: e.is_selected)
        if not selected:
            selected = self.vehicle_exchange_ids.filtered(lambda e: e.status != 'cancelled')
            if not selected:
                raise UserError(_('Không có bản ghi đổi xe nào để hủy!'))
        in_progress = selected.filtered(lambda e: e.status == 'in_progress')
        if not in_progress:
            raise UserError(_('Không có bản ghi nào ở trạng thái "Đang thực hiện" trong số các mục đã chọn!'))
        in_progress.action_done()

        selected.write({'is_selected': False})

    def action_bulk_cancel_exchanges(self):
        """Hủy đổi xe cho các bản ghi được tick chọn"""
        self.ensure_one()
        selected = self.vehicle_exchange_ids.filtered(lambda e: e.is_selected)
        if not selected:
            selected = self.vehicle_exchange_ids.filtered(lambda e: e.status != 'cancelled')
            if not selected:
                raise UserError(_('Không có bản ghi đổi xe nào để hủy!'))
        cancellable = selected.filtered(lambda e: e.status == 'confirmed')


        if not cancellable:
            selected.write({'is_selected': False})
            self.has_selected_exchanges = False
            if any(e.status == 'done' for e in selected):
                raise UserError(_('Không thể hủy yêu cầu đổi xe đã hoàn thành!'))
            return True

        if cancellable:
            cancellable.action_cancel()
        selected.write({'is_selected': False})

    def action_view_vehicle_exchanges(self):
        self.ensure_one()
        return {
            'name': _('Đổi Xe'),
            'type': 'ir.actions.act_window',
            'res_model': 'rental.vehicle.exchange',
            'view_mode': 'list,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }

    def action_new_vehicle_exchange(self):
        """Mở phiếu đổi xe; chỉ hợp đồng đang thuê mới được đổi."""
        self.ensure_one()
        if self.contract_id.state != 'in_progress':
            raise UserError(_('Chỉ được đổi xe khi hợp đồng đang thuê.'))
        return {
            'name': _('Đổi xe'), 'type': 'ir.actions.act_window',
            'res_model': 'rental.vehicle.exchange', 'view_mode': 'form',
            'target': 'new', 'context': {'default_ticket_id': self.id},
        }

    # Trạng thái phiếu tự động cập nhật theo các xe con
    state = fields.Selection([
        ('waiting', 'Chưa thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('contract_cancelled', 'Hợp đồng bị hủy'),
        ('done', 'Hoàn tất'),
    ], string='Trạng thái Vận Hành', compute='_compute_state', store=True, readonly=False,
       default='waiting', group_expand='_group_expand_state')

    @api.model
    def _group_expand_state(self, values, domain):
        """Giữ ba cột vận hành theo thứ tự; chỉ hiện cột đã hủy khi người dùng chủ động xem."""
        states = ['waiting', 'in_progress']
        if 'contract_cancelled' in values:
            states.append('contract_cancelled')
        return states + ['done']

    @api.depends('vehicle_detail_ids.status', 'contract_id.state')
    def _compute_state(self):
        """Tự động tính trạng thái của phiếu tổng dựa trên các xe con. Việc thu hồi xe chỉ hoàn tất phiếu vận hành, không tự động đóng hợp đồng."""
        for rec in self:
            if rec.state == 'contract_cancelled':
                rec.state = 'contract_cancelled'
                continue
            if rec.contract_id and rec.contract_id.state == 'cancelled':
                rec.state = 'contract_cancelled'
                continue
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

            # Khi trong phiếu bàn giao của một hợp đồng có ít nhất một chiếc xe ở trạng thái đã giao xe ('renting')
            # hoặc đã được giao và thu hồi ('returned'), hợp đồng duy trì trạng thái Đang thuê ('in_progress')
            if any(s in ('renting', 'returned') for s in statuses):
                rec._sync_contract_in_progress()

    def _inverse_state(self):

        selected.write({'is_selected': False})

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

    # Đánh dấu có ít nhất 1 xe đang được tick chọn
    has_selected_vehicles = fields.Boolean(
        string='Có xe được chọn',
        compute='_compute_has_selected_vehicles',
    )

    @api.depends('vehicle_detail_ids.is_selected')
    def _compute_has_selected_vehicles(self):
        for rec in self:
            rec.has_selected_vehicles = any(rec.vehicle_detail_ids.mapped('is_selected'))

    @api.onchange('vehicle_detail_ids')
    def _onchange_vehicle_detail_ids(self):
        self.has_selected_vehicles = any(self.vehicle_detail_ids.mapped('is_selected'))

    # Thao tác tick chọn hàng loạt
    def action_select_all_vehicles(self):
        """Chọn tất cả xe trong phiếu"""
        for rec in self:
            if rec.state in ('done', 'contract_cancelled') or (rec.contract_id and rec.contract_id.state == 'done'):
                continue
            rec.vehicle_detail_ids.write({'is_selected': True})
            rec.has_selected_vehicles = bool(rec.vehicle_detail_ids)

    def action_deselect_all_vehicles(self):
        """Bỏ chọn tất cả xe trong phiếu"""
        for rec in self:
            if rec.state in ('done', 'contract_cancelled') or (rec.contract_id and rec.contract_id.state == 'done'):
                continue
            rec.vehicle_detail_ids.write({'is_selected': False})
            rec.has_selected_vehicles = False

    def action_bulk_update_schedule(self):
        """Mở popup cập nhật địa điểm và thời gian giao/thu hồi xe cho các xe được chọn"""
        self.ensure_one()
        if self.state in ('done', 'contract_cancelled') or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất hoặc đã bị khóa, không thể thực hiện thao tác này!')
        selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            raise UserError('Vui lòng tick chọn ít nhất một xe để cập nhật địa điểm/thời gian!')

        first_line = selected_lines[0]
        default_loc = first_line.delivery_location or 'Tại cửa hàng'
        default_deliv_date = first_line.delivery_date
        if not default_deliv_date and first_line.date_checkout:
            default_deliv_date = fields.Datetime.context_timestamp(self, first_line.date_checkout).date()
        elif not default_deliv_date and self.expected_checkout:
            default_deliv_date = fields.Datetime.context_timestamp(self, self.expected_checkout).date()
        elif not default_deliv_date and self.contract_id and self.contract_id.start_date:
            default_deliv_date = fields.Datetime.context_timestamp(self, self.contract_id.start_date).date()

        default_time = first_line.delivery_time or ''
        if not default_time and first_line.date_checkout:
            default_time = fields.Datetime.context_timestamp(self, first_line.date_checkout).strftime('%H:%M')
        elif not default_time and self.expected_checkout:
            default_time = fields.Datetime.context_timestamp(self, self.expected_checkout).strftime('%H:%M')

        default_ret_loc = first_line.return_location or 'Tại cửa hàng'
        default_ret_date = first_line.return_date
        if not default_ret_date and first_line.date_checkin:
            default_ret_date = fields.Datetime.context_timestamp(self, first_line.date_checkin).date()
        elif not default_ret_date and self.expected_checkin:
            default_ret_date = fields.Datetime.context_timestamp(self, self.expected_checkin).date()
        elif not default_ret_date and self.contract_id and self.contract_id.end_date:
            default_ret_date = fields.Datetime.context_timestamp(self, self.contract_id.end_date).date()

        default_ret_time = first_line.return_time or ''
        if not default_ret_time and first_line.date_checkin:
            default_ret_time = fields.Datetime.context_timestamp(self, first_line.date_checkin).strftime('%H:%M')
        elif not default_ret_time and self.expected_checkin:
            default_ret_time = fields.Datetime.context_timestamp(self, self.expected_checkin).strftime('%H:%M')

        return {
            'name': 'Cập nhật Địa điểm & Thời gian Giao / Thu hồi xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.vehicle.schedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_vehicle_ids': [(6, 0, selected_lines.ids)],
                'default_delivery_location': default_loc,
                'default_delivery_date': default_deliv_date,
                'default_delivery_time': default_time,
                'default_return_location': default_ret_loc,
                'default_return_date': default_ret_date,
                'default_return_time': default_ret_time,
            }
        }

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
            selected_lines = self.incident_ids.filtered(lambda l: l.status == 'processing')
            if not selected_lines:
                raise UserError('Vui lòng tick chọn ít nhất một sự cố!')

        already_resolved = selected_lines.filtered(lambda l: l.status == 'resolved')
        if already_resolved:
            names = ', '.join(already_resolved.mapped(lambda l: l._get_incident_label()))
            raise UserError(f'Sự cố {names} đã được giải quyết hoàn tất!')

        selected_lines.action_start_processing()

    def action_bulk_resolve_incidents(self):
        """Xác nhận hoàn tất các sự cố đã chọn"""
        self.ensure_one()
        selected_lines = self.incident_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            selected_lines = self.incident_ids.filtered(lambda l: l.status == 'processing')
            if not selected_lines:
                raise UserError('Vui lòng tick chọn ít nhất một sự cố để xác nhận hoàn tất!')

        already_resolved = selected_lines.filtered(lambda l: l.status == 'resolved')
        if already_resolved:
            names = ', '.join(already_resolved.mapped(lambda l: l._get_incident_label()))
            raise UserError(f'Sự cố {names} đã được hoàn tất trước đó!')

        selected_lines.action_resolve()

    def action_bulk_sync_incidents_to_fleet(self):
        """Lưu thay đổi các sự cố và đồng bộ sang Fleet:
        - Sự cố Cần sửa chữa: đẩy qua bảng sự cố ở Quản lý xe (Fleet) và lưu ở trạng thái Đang thực hiện ('processing')
        - Sự cố Không cần sửa chữa: lưu luôn ở trạng thái Hoàn tất ('resolved')
        """
        self.ensure_one()
        if not self.incident_ids:
            raise UserError('Phiếu vận hành hiện chưa có sự cố nào để lưu thay đổi!')

        for incident in self.incident_ids:
            if incident.needs_repair:
                if not incident.vehicle_id:
                    raise UserError(f'Vui lòng chọn xe gặp sự cố cho {incident.name or "sự cố"} trước khi lưu thay đổi.')
                if not incident.service_id:
                    incident._sync_to_fleet_service()
                if incident.status != 'processing':
                    incident.write({'status': 'processing'})
            else:
                if incident.status != 'resolved':
                    incident.write({'status': 'resolved'})
        return True

    def action_bulk_start_delivery(self):
        """Mở popup xác nhận bắt đầu giao các xe được chọn"""
        self.ensure_one()
        if self.state in ('done', 'contract_cancelled') or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất hoặc đã bị khóa, không thể thực hiện thao tác này!')
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
        if self.state in ('done', 'contract_cancelled') or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất hoặc đã bị khóa, không thể thực hiện thao tác này!')
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
        if self.state in ('done', 'contract_cancelled') or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất hoặc đã bị khóa, không thể thực hiện thao tác này!')
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

    def action_view_delivery_receipts(self):
        """Hàm mở Biên lai giao xe từ Smart Button:
        Nếu chỉ có 1 biên lai, mở trực tiếp form xem/in.
        Nếu chưa có hoặc có nhiều hơn 1, mở danh sách.
        """
        self.ensure_one()
        receipts = self.receipt_ids
        if len(receipts) == 1:
            return {
                'name': 'Biên Lai Giao Xe',
                'type': 'ir.actions.act_window',
                'res_model': 'rental.delivery.receipt',
                'res_id': receipts.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'name': 'Biên Lai Giao Xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.delivery.receipt',
            'view_mode': 'list,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }

    def action_select_all_receipts(self):
        """Tick chọn tất cả biên lai giao xe"""
        self.ensure_one()
        self.receipt_ids.write({'is_selected': True})

    def action_deselect_all_receipts(self):
        """Bỏ tick chọn tất cả biên lai giao xe"""
        self.ensure_one()
        self.receipt_ids.write({'is_selected': False})

    def action_bulk_start_delivery_receipts(self):
        """Bắt đầu giao xe cho các biên lai được tick chọn"""
        self.ensure_one()
        selected = self.receipt_ids.filtered(lambda r: r.is_selected)
        if not selected:
            raise UserError(_('Vui lòng tick chọn ít nhất một biên lai giao xe!'))
        return selected.action_start_delivery()

    def action_bulk_confirm_delivery_receipts(self):
        """Xác nhận đã giao cho các biên lai được tick chọn"""
        self.ensure_one()
        selected = self.receipt_ids.filtered(lambda r: r.is_selected)
        if not selected:
            raise UserError(_('Vui lòng tick chọn ít nhất một biên lai giao xe!'))
        return selected.action_confirm_delivery()

    def action_view_return_receipts(self):
        """Mở Biên lai thu hồi xe từ Smart Button"""
        self.ensure_one()
        receipts = self.return_receipt_ids
        if len(receipts) == 1:
            return {
                'name': 'Biên Lai Thu Hồi Xe',
                'type': 'ir.actions.act_window',
                'res_model': 'rental.return.receipt',
                'res_id': receipts.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'name': 'Biên Lai Thu Hồi Xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.return.receipt',
            'view_mode': 'list,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }

    def action_select_all_return_receipts(self):
        """Tick chọn tất cả biên lai thu hồi xe"""
        self.ensure_one()
        self.return_receipt_ids.write({'is_selected': True})

    def action_deselect_all_return_receipts(self):
        """Bỏ tick chọn tất cả biên lai thu hồi xe"""
        self.ensure_one()
        self.return_receipt_ids.write({'is_selected': False})

    def action_bulk_confirm_return_receipts(self):
        """Xác nhận đã thu hồi cho các biên lai được tick chọn"""
        self.ensure_one()
        selected = self.return_receipt_ids.filtered(lambda r: r.is_selected)
        if not selected:
            raise UserError(_('Vui lòng tick chọn ít nhất một biên lai thu hồi xe!'))
        return selected.action_confirm_return()

    def action_open_delivery_receipt_wizard(self):
        """Mở popup xác nhận và xuất biên lai giao xe:
        - Những xe nào chung 1 người nhận, 1 thời gian, 1 địa điểm thì vào 1 biên lai
        - Nếu nhóm xe đã có biên lai trước đó: tải thông tin lên để cập nhật / ghi đè
        - Nếu nhóm xe chưa có biên lai: khởi tạo dữ liệu để tạo mới
        """
        self.ensure_one()
        if self.state == 'contract_cancelled' or (self.contract_id and self.contract_id.state == 'cancelled'):
            raise UserError(_('Hợp đồng / Phiếu vận hành đã bị hủy, không thể xuất biên lai giao xe!'))

        if not self.vehicle_detail_ids:
            raise UserError(_('Phiếu vận hành chưa có danh sách xe bàn giao!'))

        # 1. Lọc xe cần xuất: Chỉ lấy các xe chưa giao thành công ('waiting', 'delivering')
        # Trừ các xe và biên lai đã giao thành công ('delivered')
        selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.is_selected)
        if selected_lines:
            target_lines = selected_lines.filtered(lambda l: l.status in ('waiting', 'delivering'))
            if not target_lines:
                raise UserError(_('Tất cả xe được chọn đã được bàn giao thành công! Các biên lai đã giao thành công được giữ nguyên.'))
        else:
            target_lines = self.vehicle_detail_ids.filtered(lambda l: l.status in ('waiting', 'delivering'))
            if not target_lines:
                raise UserError(_('Tất cả các xe trong phiếu đã được bàn giao thành công! Không có xe nào cần xuất biên lai giao xe.'))

        # 2. Phân nhóm xe: chung 1 người nhận, 1 ngày giao, 1 giờ giao, 1 địa điểm -> 1 biên lai
        groups_dict = {}
        for line in target_lines:
            cust = self.customer_id
            loc = (line.delivery_location or 'Tại cửa hàng').strip()
            deliv_date = line.delivery_date
            if not deliv_date and line.date_checkout:
                deliv_date = fields.Datetime.context_timestamp(self, line.date_checkout).date()
            elif not deliv_date and self.expected_checkout:
                deliv_date = fields.Datetime.context_timestamp(self, self.expected_checkout).date()
            elif not deliv_date and self.contract_id and self.contract_id.start_date:
                deliv_date = fields.Datetime.context_timestamp(self, self.contract_id.start_date).date()

            raw_time = (line.delivery_time or '').strip()
            if not raw_time and line.date_checkout:
                raw_time = fields.Datetime.context_timestamp(self, line.date_checkout).strftime('%H:%M')
            elif not raw_time and self.expected_checkout:
                raw_time = fields.Datetime.context_timestamp(self, self.expected_checkout).strftime('%H:%M')
            elif not raw_time and hasattr(self, 'quick_delivery_time') and self.quick_delivery_time:
                raw_time = (self.quick_delivery_time or '').strip()

            dt_str = deliv_date.isoformat() if deliv_date else ''
            tm = raw_time or ''
            key = f"{cust.id}_{loc}_{dt_str}_{tm}"
            if key not in groups_dict:
                groups_dict[key] = {
                    'customer_id': cust.id,
                    'customer_phone': self.customer_phone or (cust.phone or cust.mobile or ''),
                    'location': loc,
                    'date': deliv_date,
                    'time': tm,
                    'lines': []
                }
            groups_dict[key]['lines'].append(line)

        # 3. Chuẩn bị dữ liệu từng tab biên lai trong wizard
        # Lấy danh sách các biên lai giao xe chưa giao thành công để ghi đè lên
        candidate_receipts = self.receipt_ids.filtered(lambda r: r.state != 'delivered')
        used_receipt_ids = set()

        wizard_vals = {
            'ticket_id': self.id,
        }

        group_idx = 1
        total_groups = len(groups_dict)

        for key, g in groups_dict.items():
            tab_idx = min(group_idx, 6)
            veh_count = len(g['lines'])
            grp_deliv_date = g['date']
            time_display = g['time'] if g['time'] else '......'
            date_display = f" - {grp_deliv_date.strftime('%d/%m/%Y')}" if grp_deliv_date else ""
            grp_name = (
                f"Biên lai {group_idx}: Giờ giao {time_display}{date_display} ({veh_count} xe)"
                if total_groups > 1
                else f"Biên lai: Giờ giao {time_display}{date_display} ({veh_count} xe)"
            )

            electric_count = sum(1 for vl in g['lines'] if getattr(vl.vehicle_id, 'is_electric_motorbike', False))

            v_vals_list = []
            for vline in g['lines']:
                initial_note = vline._get_display_visual_note() if hasattr(vline, '_get_display_visual_note') else (vline.delivery_visual_note or 'Ngoại quan của xe không có vấn đề')
                v_vals_list.append((0, 0, {
                    'vehicle_detail_id': vline.id,
                    'delivery_visual_note': initial_note,
                }))

            # Tìm biên lai cũ chưa giao thành công để ghi đè:
            existing_receipt = False
            # Ưu tiên 1: Biên lai của chính các xe trong nhóm (chưa giao thành công)
            for vl in g['lines']:
                if vl.delivery_receipt_id and vl.delivery_receipt_id in candidate_receipts and vl.delivery_receipt_id.id not in used_receipt_ids:
                    existing_receipt = vl.delivery_receipt_id
                    break
            # Ưu tiên 2: Biên lai chưa giao thành công khớp vị trí, ngày và giờ giao
            if not existing_receipt:
                for cr in candidate_receipts:
                    if cr.id not in used_receipt_ids and cr.customer_id.id == g['customer_id']:
                        if (
                            (cr.delivery_location or '').strip() == g['location']
                            and (cr.delivery_time or '').strip() == g['time']
                            and cr.delivery_date == grp_deliv_date
                        ):
                            existing_receipt = cr
                            break
            # Ưu tiên 3: Bất kỳ biên lai chưa giao thành công nào còn trống
            if not existing_receipt:
                for cr in candidate_receipts:
                    if cr.id not in used_receipt_ids:
                        existing_receipt = cr
                        break

            if existing_receipt:
                used_receipt_ids.add(existing_receipt.id)
                wizard_vals.update({
                    f'receipt_{tab_idx}_visible': True,
                    f'receipt_{tab_idx}_name': grp_name,
                    f'receipt_{tab_idx}_receipt_id': existing_receipt.id,
                    f'receipt_{tab_idx}_customer_id': self.customer_id.id or existing_receipt.customer_id.id,
                    f'receipt_{tab_idx}_customer_phone': self.customer_phone or (self.customer_id.phone or self.customer_id.mobile or '') or existing_receipt.customer_phone or '',
                    f'receipt_{tab_idx}_delivery_time': g['time'] or existing_receipt.delivery_time or False,
                    f'receipt_{tab_idx}_delivery_date': grp_deliv_date or existing_receipt.delivery_date or False,
                    f'receipt_{tab_idx}_delivery_location': g['location'] or existing_receipt.delivery_location or 'Tại cửa hàng',
                    f'receipt_{tab_idx}_vehicle_count': veh_count,
                    f'receipt_{tab_idx}_qty_helmet': existing_receipt.qty_helmet,
                    f'receipt_{tab_idx}_qty_raincoat': existing_receipt.qty_raincoat,
                    f'receipt_{tab_idx}_qty_phone_holder': existing_receipt.qty_phone_holder,
                    f'receipt_{tab_idx}_qty_charger': existing_receipt.qty_charger,
                    f'receipt_{tab_idx}_vehicle_ids': v_vals_list,
                })
            else:
                wizard_vals.update({
                    f'receipt_{tab_idx}_visible': True,
                    f'receipt_{tab_idx}_name': grp_name,
                    f'receipt_{tab_idx}_receipt_id': False,
                    f'receipt_{tab_idx}_customer_id': g['customer_id'],
                    f'receipt_{tab_idx}_customer_phone': g.get('customer_phone') or '',
                    f'receipt_{tab_idx}_delivery_time': g['time'] or False,
                    f'receipt_{tab_idx}_delivery_date': grp_deliv_date or False,
                    f'receipt_{tab_idx}_delivery_location': g['location'],
                    f'receipt_{tab_idx}_vehicle_count': veh_count,
                    f'receipt_{tab_idx}_qty_helmet': 2 * veh_count,
                    f'receipt_{tab_idx}_qty_raincoat': 2 * veh_count,
                    f'receipt_{tab_idx}_qty_phone_holder': 1 * veh_count,
                    f'receipt_{tab_idx}_qty_charger': electric_count,
                    f'receipt_{tab_idx}_vehicle_ids': v_vals_list,
                })

            group_idx += 1

        wizard = self.env['rental.delivery.receipt.wizard'].create(wizard_vals)

        return {
            'name': 'Xác Nhận & Xuất Biên Lai Giao Xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.delivery.receipt.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_open_return_receipt_wizard(self):
        """Mở popup xác nhận và xuất biên lai thu hồi xe:
        - Những xe nào chung 1 người trả, 1 thời gian, 1 địa điểm thì vào 1 biên lai
        - Nếu nhóm xe đã có biên lai trước đó: tải thông tin lên để cập nhật / ghi đè
        - Nếu nhóm xe chưa có biên lai: khởi tạo dữ liệu để tạo mới
        """
        self.ensure_one()
        if self.state == 'contract_cancelled' or (self.contract_id and self.contract_id.state == 'cancelled'):
            raise UserError(_('Hợp đồng / Phiếu vận hành đã bị hủy, không thể xuất biên lai thu hồi xe!'))

        if not self.vehicle_detail_ids:
            raise UserError(_('Phiếu vận hành chưa có danh sách xe bàn giao!'))

        # 1. Lọc xe cần xuất: Chỉ lấy các xe chưa thu hồi thành công (status != 'returned')
        # Trừ các xe và biên lai đã thu hồi thành công ('returned')
        selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.is_selected)
        if selected_lines:
            target_lines = selected_lines.filtered(lambda l: l.status != 'returned')
            if not target_lines:
                raise UserError(_('Tất cả xe được chọn đã được thu hồi hoàn tất! Các biên lai đã thu hồi thành công được giữ nguyên.'))
        else:
            target_lines = self.vehicle_detail_ids.filtered(lambda l: l.status != 'returned')
            if not target_lines:
                raise UserError(_('Tất cả các xe trong phiếu đã được thu hồi hoàn tất! Không có xe nào cần xuất biên lai thu hồi.'))

        # 2. Phân nhóm xe: chung 1 người trả, 1 ngày thu hồi, 1 giờ thu hồi, 1 địa điểm -> 1 biên lai
        groups_dict = {}
        for line in target_lines:
            cust = self.customer_id
            loc = (line.return_location or 'Tại cửa hàng').strip()
            ret_date = line.return_date
            if not ret_date and line.date_checkin:
                ret_date = fields.Datetime.context_timestamp(self, line.date_checkin).date()
            elif not ret_date and self.expected_checkin:
                ret_date = fields.Datetime.context_timestamp(self, self.expected_checkin).date()
            elif not ret_date and self.contract_id and self.contract_id.end_date:
                ret_date = fields.Datetime.context_timestamp(self, self.contract_id.end_date).date()

            raw_time = (line.return_time or '').strip()
            if not raw_time and line.date_checkin:
                raw_time = fields.Datetime.context_timestamp(self, line.date_checkin).strftime('%H:%M')
            elif not raw_time and self.expected_checkin:
                raw_time = fields.Datetime.context_timestamp(self, self.expected_checkin).strftime('%H:%M')
            elif not raw_time and hasattr(self, 'quick_return_time') and self.quick_return_time:
                raw_time = (self.quick_return_time or '').strip()

            dt_str = ret_date.isoformat() if ret_date else ''
            tm = raw_time or ''
            key = f"{cust.id}_{loc}_{dt_str}_{tm}"
            if key not in groups_dict:
                groups_dict[key] = {
                    'customer_id': cust.id,
                    'customer_phone': self.customer_phone or (cust.phone or cust.mobile or ''),
                    'location': loc,
                    'date': ret_date,
                    'time': tm,
                    'lines': []
                }
            groups_dict[key]['lines'].append(line)

        # 3. Chuẩn bị dữ liệu từng tab biên lai trong wizard
        # Lấy danh sách các biên lai thu hồi xe chưa thu hồi thành công để ghi đè lên
        candidate_receipts = self.return_receipt_ids.filtered(lambda r: r.state != 'returned')
        used_receipt_ids = set()

        wizard_vals = {
            'ticket_id': self.id,
        }

        group_idx = 1
        total_groups = len(groups_dict)

        for key, g in groups_dict.items():
            tab_idx = min(group_idx, 6)
            veh_count = len(g['lines'])
            grp_ret_date = g['date']
            time_display = g['time'] if g['time'] else '......'
            date_display = f" - {grp_ret_date.strftime('%d/%m/%Y')}" if grp_ret_date else ""
            grp_name = (
                f"Biên lai thu hồi {group_idx}: Giờ {time_display}{date_display} ({veh_count} xe)"
                if total_groups > 1
                else f"Biên lai thu hồi: Giờ {time_display}{date_display} ({veh_count} xe)"
            )

            electric_count = sum(1 for vl in g['lines'] if getattr(vl.vehicle_id, 'is_electric_motorbike', False))

            v_vals_list = []
            for vline in g['lines']:
                v_vals_list.append((0, 0, {
                    'vehicle_detail_id': vline.id,
                    'return_visual_note': vline.return_visual_note or 'Xe hoàn trả đầy đủ, ngoại quan bình thường, không trầy xước phát sinh.',
                }))

            # Tìm biên lai cũ chưa thu hồi thành công để ghi đè:
            existing_receipt = False
            # Ưu tiên 1: Biên lai của chính các xe trong nhóm (chưa thu hồi thành công)
            for vl in g['lines']:
                if vl.return_receipt_id and vl.return_receipt_id in candidate_receipts and vl.return_receipt_id.id not in used_receipt_ids:
                    existing_receipt = vl.return_receipt_id
                    break
            # Ưu tiên 2: Biên lai chưa thu hồi thành công khớp vị trí, ngày và giờ thu hồi
            if not existing_receipt:
                for cr in candidate_receipts:
                    if cr.id not in used_receipt_ids and cr.customer_id.id == g['customer_id']:
                        if (
                            (cr.return_location or '').strip() == g['location']
                            and (cr.return_time or '').strip() == g['time']
                            and cr.return_date == grp_ret_date
                        ):
                            existing_receipt = cr
                            break
            # Ưu tiên 3: Bất kỳ biên lai chưa thu hồi thành công nào còn trống
            if not existing_receipt:
                for cr in candidate_receipts:
                    if cr.id not in used_receipt_ids:
                        existing_receipt = cr
                        break

            if existing_receipt:
                used_receipt_ids.add(existing_receipt.id)
                wizard_vals.update({
                    f'receipt_{tab_idx}_visible': True,
                    f'receipt_{tab_idx}_name': grp_name,
                    f'receipt_{tab_idx}_receipt_id': existing_receipt.id,
                    f'receipt_{tab_idx}_customer_id': self.customer_id.id or existing_receipt.customer_id.id,
                    f'receipt_{tab_idx}_customer_phone': self.customer_phone or (self.customer_id.phone or self.customer_id.mobile or '') or existing_receipt.customer_phone or '',
                    f'receipt_{tab_idx}_return_time': g['time'] or existing_receipt.return_time or False,
                    f'receipt_{tab_idx}_return_date': grp_ret_date or existing_receipt.return_date or False,
                    f'receipt_{tab_idx}_return_location': g['location'] or existing_receipt.return_location or 'Tại cửa hàng',
                    f'receipt_{tab_idx}_vehicle_count': veh_count,
                    f'receipt_{tab_idx}_qty_helmet': existing_receipt.qty_helmet,
                    f'receipt_{tab_idx}_qty_raincoat': existing_receipt.qty_raincoat,
                    f'receipt_{tab_idx}_qty_phone_holder': existing_receipt.qty_phone_holder,
                    f'receipt_{tab_idx}_qty_charger': existing_receipt.qty_charger,
                    f'receipt_{tab_idx}_return_visual_note': existing_receipt.return_visual_note or 'Ngoại quan bình thường, không trầy xước phát sinh.',
                    f'receipt_{tab_idx}_vehicle_ids': v_vals_list,
                })
            else:
                wizard_vals.update({
                    f'receipt_{tab_idx}_visible': True,
                    f'receipt_{tab_idx}_name': grp_name,
                    f'receipt_{tab_idx}_receipt_id': False,
                    f'receipt_{tab_idx}_customer_id': g['customer_id'],
                    f'receipt_{tab_idx}_customer_phone': g.get('customer_phone') or '',
                    f'receipt_{tab_idx}_return_time': g['time'] or False,
                    f'receipt_{tab_idx}_return_date': grp_ret_date or False,
                    f'receipt_{tab_idx}_return_location': g['location'],
                    f'receipt_{tab_idx}_vehicle_count': veh_count,
                    f'receipt_{tab_idx}_qty_helmet': 2 * veh_count,
                    f'receipt_{tab_idx}_qty_raincoat': 2 * veh_count,
                    f'receipt_{tab_idx}_qty_phone_holder': 1 * veh_count,
                    f'receipt_{tab_idx}_qty_charger': electric_count,
                    f'receipt_{tab_idx}_return_visual_note': 'Ngoại quan bình thường, không trầy xước phát sinh.',
                    f'receipt_{tab_idx}_vehicle_ids': v_vals_list,
                })

            group_idx += 1

        wizard = self.env['rental.return.receipt.wizard'].create(wizard_vals)

        return {
            'name': 'Xác Nhận & Xuất Biên Lai Thu Hồi Xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.return.receipt.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _get_return_receipt_vehicles(self):
        """Trả về danh sách xe cần in trên biên lai thu hồi:
        - Nếu có tick chọn xe: ưu tiên in các xe được tick chọn
        - Nếu không tick chọn: in toàn bộ xe trong phiếu
        Hàm này chỉ đọc, hoàn toàn không sửa đổi hay cập nhật bất kỳ dữ liệu gì.
        """
        self.ensure_one()
        selected = self.vehicle_detail_ids.filtered(lambda v: v.is_selected)
        return selected if selected else self.vehicle_detail_ids

    def action_print_return_receipt(self):
        """Xuất biên lai thu hồi xe dạng PDF:
        - Không áp đặt điều kiện chặn (luôn in được khi cần).
        - Tuyệt đối không thay đổi, cập nhật hay ghi bất kỳ dữ liệu nào.
        """
        self.ensure_one()
        return self.env.ref('motorbike_rental_operation.action_report_return_receipt').report_action(self)


    def action_contract_cancelled(self):
        """Chuyển phiếu sang trạng thái Hợp đồng bị hủy và khóa bản ghi"""
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('Phiếu vận hành đã hoàn tất, không thể chuyển sang hợp đồng bị hủy!'))
            if rec.state == 'contract_cancelled':
                continue

            rec.write({'state': 'contract_cancelled'})

    def action_reset_waiting(self):
        """Khôi phục toàn bộ xe về trạng thái chờ giao"""
        for rec in self:
            if rec.state in ('done', 'contract_cancelled'):
                raise UserError(_('Phiếu vận hành đã hoàn tất hoặc đã bị khóa, không thể khôi phục trạng thái!'))
            rec.vehicle_detail_ids.action_reset_waiting()

    def unlink(self):
        raise UserError(_('Không được phép xóa bản ghi Phiếu Vận Hành (Giao/Thu Hồi Xe)!'))
