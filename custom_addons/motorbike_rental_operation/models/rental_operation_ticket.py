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
            if any(v.status in ('renting', 'returned') for v in ticket.vehicle_detail_ids):
                ticket._sync_contract_in_progress()
        return tickets

    def write(self, vals):
        res = super(RentalOperationTicket, self).write(vals)
        if 'contract_id' in vals or 'vehicle_detail_ids' in vals:
            for ticket in self:
                if any(v.status in ('renting', 'returned') for v in ticket.vehicle_detail_ids):
                    ticket._sync_contract_in_progress()
        return res

    def _sync_contract_in_progress(self):
        """Chuyển hợp đồng liên kết sang Đang thuê ('in_progress') nếu có xe trong phiếu được giao"""
        for rec in self:
            contract = rec.contract_id
            if contract and contract.state not in ('in_progress', 'done', 'cancelled'):
                if contract.state == 'draft':
                    contract.action_confirm()
                if contract.state == 'confirmed':
                    contract.write({'state': 'in_progress'})

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
        2. Không cho hiển thị nếu trùng mã khách hàng, chi tiết xe VÀ trùng thời gian với hợp đồng đã tồn tại trong phiếu giao
           (Nếu khác thời gian thì vẫn được hiển thị và chọn)
        3. Chỉ hiển thị các hợp đồng ở trạng thái 'Đã xác nhận' (confirmed)
        """
        all_tickets = self.env['rental.operation.ticket'].search([])
        for rec in self:
            rec_origin_id = rec._origin.id if rec._origin else (rec.id if isinstance(rec.id, int) else False)
            other_tickets = all_tickets.filtered(lambda t: t.id != rec_origin_id) if rec_origin_id else all_tickets

            # Yêu cầu 1: Thu thập ID hợp đồng đã có trong bảng giao xe khác
            used_contract_ids = set(other_tickets.mapped('contract_id.id'))

            # Yêu cầu 2: Thu thập thông tin các xe đã có phiếu giao của từng khách hàng kèm khoảng thời gian thuê
            existing_cust_vehicle_intervals = []
            for t in other_tickets:
                cust_id = t.customer_id.id or (t.contract_id and t.contract_id.customer_id.id)
                if not cust_id:
                    continue
                t_start = t.contract_id.start_date or t.expected_checkout
                t_end = t.contract_id.end_date or t.expected_checkin

                # Lấy từ danh sách xe bàn giao trong phiếu (vehicle_detail_ids)
                for v_line in t.vehicle_detail_ids:
                    if v_line.vehicle_id:
                        v_start = v_line.date_checkout or t_start
                        v_end = v_line.date_checkin or t_end
                        existing_cust_vehicle_intervals.append({
                            'cust_id': cust_id,
                            'vehicle_id': v_line.vehicle_id.id,
                            'start': v_start,
                            'end': v_end,
                        })

                # Nếu vehicle_detail_ids trống, lấy từ line_ids của contract_id
                if not t.vehicle_detail_ids and t.contract_id:
                    for c_line in t.contract_id.line_ids:
                        if c_line.vehicle_id:
                            existing_cust_vehicle_intervals.append({
                                'cust_id': cust_id,
                                'vehicle_id': c_line.vehicle_id.id,
                                'start': t_start,
                                'end': t_end,
                            })

            # Tìm danh sách hợp đồng ứng viên (chỉ lấy hợp đồng ở trạng thái 'Đã xác nhận')
            candidate_contracts = self.env['rental.contract'].search([('state', '=', 'confirmed')])
            valid_ids = []
            for c in candidate_contracts:
                # Điều kiện 1: Bỏ qua hợp đồng đã có trong bảng giao xe
                if c.id in used_contract_ids:
                    continue

                # Điều kiện 2: Bỏ qua nếu trùng khách hàng, trùng chi tiết xe VÀ trùng cả thời gian thuê
                c_cust_id = c.customer_id.id
                c_v_ids = set(c.line_ids.mapped('vehicle_id.id'))
                c_start = c.start_date
                c_end = c.end_date

                is_conflict = False
                if c_cust_id and c_v_ids:
                    for item in existing_cust_vehicle_intervals:
                        if item['cust_id'] == c_cust_id and item['vehicle_id'] in c_v_ids:
                            # Kiểm tra trùng thời gian (time overlap: start1 < end2 and end1 > start2)
                            i_start = item['start']
                            i_end = item['end']
                            if c_start and c_end and i_start and i_end:
                                overlap = (c_start < i_end) and (c_end > i_start)
                            else:
                                overlap = True
                            if overlap:
                                is_conflict = True
                                break

                if is_conflict:
                    continue

                valid_ids.append(c.id)

            # Đảm bảo hợp đồng đang lưu của phiếu hiện tại vẫn được giữ lại để hiển thị
            if rec.contract_id and rec.contract_id.id not in valid_ids:
                valid_ids.append(rec.contract_id.id)

            rec.available_contract_ids = self.env['rental.contract'].browse(valid_ids)

    @api.constrains('contract_id')
    def _check_contract_id_filter(self):
        """Ràng buộc kiểm tra khi lưu phiếu:
        1. Không cho chọn hợp đồng đã tồn tại trong bảng giao xe
        2. Không cho chọn nếu trùng mã khách hàng, chi tiết xe VÀ trùng cả thời gian với hợp đồng đã tồn tại trong phiếu giao
        """
        for rec in self:
            if not rec.contract_id:
                continue

            # 1. Kiểm tra hợp đồng đã tồn tại trong bảng giao xe
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

            # 2. Kiểm tra trùng mã khách hàng, chi tiết xe VÀ trùng thời gian thuê với hợp đồng đã tồn tại trong phiếu giao
            cust_id = rec.contract_id.customer_id.id
            rec_vehicles = set(rec.contract_id.line_ids.mapped('vehicle_id.id'))
            rec_start = rec.contract_id.start_date or rec.expected_checkout
            rec_end = rec.contract_id.end_date or rec.expected_checkin
            if cust_id and rec_vehicles:
                other_tickets = self.search([
                    ('id', '!=', rec.id),
                    ('contract_id', '!=', False),
                    ('contract_id.customer_id', '=', cust_id)
                ])
                for t in other_tickets:
                    t_start = t.contract_id.start_date or t.expected_checkout
                    t_end = t.contract_id.end_date or t.expected_checkin

                    # Kiểm tra các xe trong vehicle_detail_ids
                    for v_line in t.vehicle_detail_ids:
                        v_id = v_line.vehicle_id.id
                        if v_id in rec_vehicles:
                            v_start = v_line.date_checkout or t_start
                            v_end = v_line.date_checkin or t_end
                            if rec_start and rec_end and v_start and v_end:
                                overlap = (rec_start < v_end) and (rec_end > v_start)
                            else:
                                overlap = True
                            if overlap:
                                v_name = v_line.vehicle_id.name or 'Xe'
                                raise ValidationError(
                                    _('Không thể chọn hợp đồng "%(contract)s"! Khách hàng "%(customer)s" và chi tiết xe (%(vehicles)s) '
                                      'bị trùng thời gian thuê với hợp đồng "%(t_contract)s" đã tồn tại trong phiếu giao %(ticket)s.') % {
                                        'contract': rec.contract_id.display_name or rec.contract_id.name,
                                        'customer': rec.contract_id.customer_id.name,
                                        'vehicles': v_name,
                                        't_contract': t.contract_id.display_name or t.contract_id.name,
                                        'ticket': t.name,
                                    }
                                )

                    # Nếu t chưa có vehicle_detail_ids thì đối chiếu qua line_ids của contract
                    if not t.vehicle_detail_ids:
                        t_vehicles = set(t.contract_id.line_ids.mapped('vehicle_id.id'))
                        overlap_vehicles = rec_vehicles & t_vehicles
                        if overlap_vehicles:
                            if rec_start and rec_end and t_start and t_end:
                                overlap = (rec_start < t_end) and (rec_end > t_start)
                            else:
                                overlap = True
                            if overlap:
                                v_names = ', '.join(self.env['fleet.vehicle'].browse(list(overlap_vehicles)).mapped('name') or ['Xe'])
                                raise ValidationError(
                                    _('Không thể chọn hợp đồng "%(contract)s"! Khách hàng "%(customer)s" và chi tiết xe (%(vehicles)s) '
                                      'bị trùng thời gian thuê với hợp đồng "%(t_contract)s" đã tồn tại trong phiếu giao %(ticket)s.') % {
                                        'contract': rec.contract_id.display_name or rec.contract_id.name,
                                        'customer': rec.contract_id.customer_id.name,
                                        'vehicles': v_names,
                                        't_contract': t.contract_id.display_name or t.contract_id.name,
                                        'ticket': t.name,
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
                vehicle_vals = {
                    'vehicle_id': line.vehicle_id.id,
                    'vehicle_price': line.daily_rate,
                    'delivery_location': 'Tại cửa hàng',
                    'return_location': 'Tại cửa hàng',
                    'delivery_time': False,
                    'date_checkout': self.contract_id.start_date,
                    'date_checkin': self.contract_id.end_date,
                    'actual_delivery_date': False,
                    'actual_return_date': False,
                    'status': 'waiting',
                    'is_selected': False,
                    'is_custom_delivery_location': False,
                    'is_custom_return_location': False,
                    'is_custom_delivery_time': False,
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
    quick_delivery_time = fields.Char(string='Giờ giao xe', default='08:00', help='Giờ giao xe mặc định (VD: 08:30)')

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
                line.delivery_time = self.quick_delivery_time or '08:00'

    def write(self, vals):
        if 'quick_delivery_location' in vals:
            for rec in self:
                if rec.state == 'done':
                    raise UserError('Phiếu vận hành đã hoàn tất, không được phép chỉnh sửa Địa điểm giao chung!')
        if 'quick_return_location' in vals:
            for rec in self:
                if rec.state == 'done':
                    raise UserError('Phiếu vận hành đã hoàn tất, không được phép chỉnh sửa Địa điểm thu hồi chung!')
        if 'quick_delivery_time' in vals:
            for rec in self:
                if rec.state == 'done':
                    raise UserError('Phiếu vận hành đã hoàn tất, không được phép chỉnh sửa Giờ giao chung!')

        res = super(RentalOperationTicket, self).write(vals)
        if 'quick_delivery_location' in vals or 'quick_return_location' in vals or 'quick_delivery_time' in vals:
            for rec in self:
                for line in rec.vehicle_detail_ids:
                    line_vals = {}
                    if 'quick_delivery_location' in vals and not line.is_custom_delivery_location and line.status in ('waiting', 'delivering'):
                        line_vals['delivery_location'] = rec.quick_delivery_location or 'Tại cửa hàng'
                    if 'quick_return_location' in vals and not line.is_custom_return_location and line.status != 'returned':
                        line_vals['return_location'] = rec.quick_return_location or 'Tại cửa hàng'
                    if 'quick_delivery_time' in vals and not line.is_custom_delivery_time and line.status in ('waiting', 'delivering'):
                        line_vals['delivery_time'] = rec.quick_delivery_time or '08:00'
                    if line_vals:
                        line.write(line_vals)
        return res

    # Liên kết bảng con chi tiết xe, sự cố và biên lai giao xe
    vehicle_detail_ids = fields.One2many('rental.operation.ticket.vehicle', 'ticket_id', string='Chi tiết Xe')
    incident_ids = fields.One2many('rental.operation.incident.log', 'ticket_id', string='Sự cố & Hư hỏng')
    receipt_ids = fields.One2many('rental.delivery.receipt', 'ticket_id', string='Biên lai giao xe')
    receipt_count = fields.Integer(string='Số biên lai', compute='_compute_receipt_count')

    @api.depends('receipt_ids')
    def _compute_receipt_count(self):
        for rec in self:
            rec.receipt_count = len(rec.receipt_ids)

    # Trạng thái phiếu tự động cập nhật theo các xe con
    state = fields.Selection([
        ('waiting', 'Chưa thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn tất')
    ], string='Trạng thái Vận Hành', compute='_compute_state', store=True, default='waiting')

    @api.depends('vehicle_detail_ids.status')
    def _compute_state(self):
        """Tự động tính trạng thái của phiếu tổng dựa trên các xe con. Việc thu hồi xe chỉ hoàn tất phiếu vận hành, không tự động đóng hợp đồng."""
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

            # Khi trong phiếu bàn giao của một hợp đồng có ít nhất một chiếc xe ở trạng thái đã giao xe ('renting')
            # hoặc đã được giao và thu hồi ('returned'), hợp đồng duy trì trạng thái Đang thuê ('in_progress')
            if any(s in ('renting', 'returned') for s in statuses):
                rec._sync_contract_in_progress()

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
            if rec.state == 'done' or (rec.contract_id and rec.contract_id.state == 'done'):
                continue
            rec.vehicle_detail_ids.write({'is_selected': True})
            rec.has_selected_vehicles = bool(rec.vehicle_detail_ids)

    def action_deselect_all_vehicles(self):
        """Bỏ chọn tất cả xe trong phiếu"""
        for rec in self:
            rec.vehicle_detail_ids.write({'is_selected': False})
            rec.has_selected_vehicles = False

    def action_bulk_update_schedule(self):
        """Mở popup cập nhật địa điểm và thời gian giao xe cho các xe được chọn"""
        self.ensure_one()
        if self.state == 'done' or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất toàn bộ, không thể thực hiện thao tác này!')
        selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.is_selected)
        if not selected_lines:
            raise UserError('Vui lòng tick chọn ít nhất một xe để cập nhật địa điểm/thời gian!')

        first_line = selected_lines[0]
        default_loc = first_line.delivery_location or 'Tại cửa hàng'
        default_time = first_line.delivery_time or ''
        default_ret_loc = first_line.return_location or 'Tại cửa hàng'

        return {
            'name': 'Cập nhật Địa điểm & Giờ Giao xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.vehicle.schedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_vehicle_ids': [(6, 0, selected_lines.ids)],
                'default_delivery_location': default_loc,
                'default_delivery_time': default_time,
                'default_return_location': default_ret_loc,
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

    def action_bulk_sync_incidents_to_fleet(self):
        """Đồng bộ các sự cố sang Bảo dưỡng & Sửa chữa của Fleet"""
        self.ensure_one()
        unsynced = self.incident_ids.filtered(lambda l: not l.service_id)
        if not unsynced:
            raise UserError('Tất cả các sự cố trong phiếu này đã được đồng bộ sang Bảo dưỡng & Sửa chữa!')
        for inc in unsynced:
            inc.with_context(skip_sync_fleet=True).write({'needs_repair': True, 'needs_repair_display': 'yes'})
            inc.needs_repair = True
            inc.needs_repair_display = 'yes'
        unsynced._sync_to_fleet_service()
        return True

    def action_bulk_start_delivery(self):
        """Mở popup xác nhận bắt đầu giao các xe được chọn"""
        self.ensure_one()
        if self.state == 'done' or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất toàn bộ, không thể thực hiện thao tác này!')
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
        if self.state == 'done' or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất toàn bộ, không thể thực hiện thao tác này!')
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
        if self.state == 'done' or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất toàn bộ, không thể thực hiện thao tác này!')
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
        """Hàm mở danh sách Biên lai giao xe từ Smart Button"""
        self.ensure_one()
        return {
            'name': 'Biên Lai Giao Xe',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.delivery.receipt',
            'view_mode': 'list,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }

    def action_open_delivery_receipt_wizard(self):
        """Mở popup xác nhận và xuất biên lai giao xe: tự động gom nhóm theo người, địa điểm, giờ giao để xuất các biên lai riêng biệt"""
        self.ensure_one()
        if self.state == 'done' or (self.contract_id and self.contract_id.state == 'done'):
            raise UserError('Hợp đồng / Phiếu vận hành đã hoàn tất toàn bộ, không thể xuất biên lai giao xe!')

        # 1. Lọc các xe được tick chọn
        selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.is_selected)
        if selected_lines:
            already_delivered = selected_lines.filtered(lambda l: l.status in ('renting', 'returned'))
            if already_delivered:
                names = ', '.join(already_delivered.mapped(lambda l: l._get_vehicle_label()))
                raise UserError(f'Xe {names} đã được giao xe thành công!')
        else:
            # Nếu không tick chọn xe nào: chỉ lấy các xe chưa giao thành công (chờ giao hoặc đang giao)
            selected_lines = self.vehicle_detail_ids.filtered(lambda l: l.status in ('waiting', 'delivering'))
            if not selected_lines:
                delivered_lines = self.vehicle_detail_ids.filtered(lambda l: l.status in ('renting', 'returned'))
                if delivered_lines:
                    names = ', '.join(delivered_lines.mapped(lambda l: l._get_vehicle_label()))
                    raise UserError(f'Xe {names} đã được giao xe thành công!')
                raise UserError('Không có xe nào để xuất biên lai giao xe!')

        # 3. Phân nhóm các xe theo (Khách hàng, Địa điểm giao, Giờ giao)
        groups_dict = {}
        for line in selected_lines:
            cust = self.customer_id
            loc = (line.delivery_location or 'Tại cửa hàng').strip()
            tm = (line.delivery_time or '08:00').strip()
            key = f"{cust.id}_{loc}_{tm}"
            if key not in groups_dict:
                groups_dict[key] = {
                    'customer_id': cust.id,
                    'customer_phone': self.customer_phone or (cust.phone or cust.mobile or ''),
                    'location': loc,
                    'time': tm,
                    'lines': []
                }
            groups_dict[key]['lines'].append(line)

        # 4. Chuẩn bị dữ liệu từng tab biên lai
        wizard_vals = {
            'ticket_id': self.id,
        }

        group_idx = 1
        total_groups = len(groups_dict)

        for key, g in groups_dict.items():
            tab_idx = min(group_idx, 6)
            veh_count = len(g['lines'])
            if total_groups > 1:
                grp_name = f"Biên lai {group_idx}: Giờ giao {g['time']} ({veh_count} xe)"
            else:
                grp_name = f"Biên lai: Giờ giao {g['time']} ({veh_count} xe)"

            v_vals_list = []
            for vline in g['lines']:
                veh_condition = vline._get_vehicle_exterior_condition(vline.vehicle_id) if vline.vehicle_id else False
                if veh_condition and veh_condition != 'Ngoại quan của xe không có vấn đề':
                    initial_note = veh_condition
                else:
                    initial_note = vline.delivery_visual_note or veh_condition or 'Ngoại quan của xe không có vấn đề'

                v_vals_list.append((0, 0, {
                    'vehicle_detail_id': vline.id,
                    'group_key': key,
                    'group_name': grp_name,
                    'delivery_visual_note': initial_note,
                }))

            if not wizard_vals.get(f'receipt_{tab_idx}_visible'):
                wizard_vals.update({
                    f'receipt_{tab_idx}_visible': True,
                    f'receipt_{tab_idx}_name': grp_name,
                    f'receipt_{tab_idx}_customer_id': g['customer_id'],
                    f'receipt_{tab_idx}_customer_phone': g.get('customer_phone') or '',
                    f'receipt_{tab_idx}_delivery_time': g['time'],
                    f'receipt_{tab_idx}_delivery_date': fields.Date.context_today(self),
                    f'receipt_{tab_idx}_delivery_location': g['location'],
                    f'receipt_{tab_idx}_vehicle_count': veh_count,
                    # Mặc định theo số lượng xe: 2 mũ, 2 áo mưa, 1 giá đt, 1 sạc trên 1 xe
                    f'receipt_{tab_idx}_qty_helmet': 2 * veh_count,
                    f'receipt_{tab_idx}_qty_raincoat': 2 * veh_count,
                    f'receipt_{tab_idx}_qty_phone_holder': 1 * veh_count,
                    f'receipt_{tab_idx}_qty_charger': 1 * veh_count,
                    f'receipt_{tab_idx}_vehicle_ids': v_vals_list,
                })
            else:
                prev_veh_ids = wizard_vals[f'receipt_{tab_idx}_vehicle_ids']
                prev_veh_ids.extend(v_vals_list)
                wizard_vals[f'receipt_{tab_idx}_vehicle_count'] += veh_count
                wizard_vals[f'receipt_{tab_idx}_qty_helmet'] += 2 * veh_count
                wizard_vals[f'receipt_{tab_idx}_qty_raincoat'] += 2 * veh_count
                wizard_vals[f'receipt_{tab_idx}_qty_phone_holder'] += 1 * veh_count
                wizard_vals[f'receipt_{tab_idx}_qty_charger'] += 1 * veh_count

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

    def action_reset_waiting(self):
        """Khôi phục toàn bộ xe về trạng thái chờ giao"""
        for rec in self:
            rec.vehicle_detail_ids.action_reset_waiting()

    def unlink(self):
        return super(RentalOperationTicket, self.with_context(delete_ticket=True)).unlink()
