# -*- coding: utf-8 -*-
"""Model cho quy trình đổi xe trong module vận hành.

- Trạng thái: Xác nhận (confirmed), Hoàn thành (done), Hủy (cancelled)
- Khi vừa tạo bản ghi mới:
  + Giữ xe B ở trạng thái Sẵn sàng; chỉ thêm vào phiếu vận hành ở trạng thái Chưa giao.
    ngày/giờ giao trống, địa điểm nhận mặc định 'Tại cửa hàng'
  + Trạng thái bản ghi đổi xe = 'confirmed' (Xác nhận)
- Tự động hoàn thành (done):
  + Khi A đã thu hồi và B đã giao: thêm dòng lịch sử B vào hợp đồng rồi hoàn thành phiếu đổi.
- Khi bấm nút Hủy:
  + Chỉ hủy được trước khi thu hồi A hoặc bắt đầu giao B.
  + Trạng thái bản ghi = 'cancelled' (Hủy)
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RentalVehicleExchange(models.Model):
    _name = 'rental.vehicle.exchange'
    _description = 'Bảng ghi đổi xe (Exchange Record)'
    _order = 'request_date desc, id desc'

    # ---------------------------------------------------------------------
    # Core fields
    # ---------------------------------------------------------------------
    name = fields.Char(
        string='Mã đổi xe', required=True, copy=False, readonly=True,
        default=lambda self: _('Mới')
    )
    is_selected = fields.Boolean(string='Chọn', default=False)
    ticket_id = fields.Many2one(
        'rental.operation.ticket', string='Phiếu vận hành', ondelete='cascade', index=True, required=True
    )
    request_date = fields.Datetime(
        string='Thời gian yêu cầu', default=fields.Datetime.now, readonly=True
    )
    status = fields.Selection([
        ('confirmed', 'Xác nhận'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Hủy'),
    ], string='Trạng thái', default='confirmed', required=True, copy=False)

    # ---------------------------------------------------------------------
    # Vehicles
    # ---------------------------------------------------------------------
    available_vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        compute='_compute_available_vehicle_ids',
        string='Xe có trong phiếu'
    )
    vehicle_a_id = fields.Many2one(
        'fleet.vehicle', string='Xe A (xe hỏng)', required=True,
        domain="[('id', 'in', available_vehicle_ids)]",
        help='Xe cần được đổi (đang gặp sự cố).')
    vehicle_a_model_id = fields.Many2one(
        'fleet.vehicle.model', related='vehicle_a_id.model_id', readonly=True)
    vehicle_b_id = fields.Many2one(
        'fleet.vehicle', string='Xe B (xe thay thế)', required=True,
        domain="[('operational_status', '=', 'available'), ('model_id', '=', vehicle_a_model_id)]",
        help='Xe thay thế cho xe A.')

    # ---------------------------------------------------------------------
    # Thông tin bổ sung
    # ---------------------------------------------------------------------
    reason = fields.Text(string='Lý do đổi xe')
    error_by = fields.Selection([
        ('company', 'Công ty'),
        ('customer', 'Khách hàng')
    ], string='Lỗi thuộc phía')

    # Giá & Mã hoán đổi (lưu ngầm phục vụ hệ thống nếu cần, không hiển thị trên giao diện)
    vehicle_price = fields.Monetary(
        string='Giá xe (đồng)', currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)

    exchange_code = fields.Char(
        string='Mã hoán đổi', compute='_compute_exchange_code',
        store=True, readonly=True)

    contract_line_b_id = fields.Many2one(
        'rental.contract.line', string='Dòng hợp đồng xe B', readonly=True, ondelete='set null')
    ticket_line_b_id = fields.Many2one(
        'rental.operation.ticket.vehicle', string='Dòng vận hành xe B', readonly=True, ondelete='set null')

    # ---------------------------------------------------------------------
    # Constraints & Validations
    # ---------------------------------------------------------------------
    @api.constrains('vehicle_a_id', 'status')
    def _check_unique_active_exchange(self):
        for rec in self:
            if rec.status == 'confirmed':
                duplicate = self.search([
                    ('id', '!=', rec.id),
                    ('vehicle_a_id', '=', rec.vehicle_a_id.id),
                    ('status', '=', 'confirmed'),
                ], limit=1)
                if duplicate:
                    raise ValidationError(_('Xe "%s" đã có một bản ghi đổi xe đang ở trạng thái Xác nhận. Vui lòng hoàn thành hoặc hủy bản ghi cũ trước.') % rec.vehicle_a_id.display_name)

    @api.onchange('is_selected')
    def _onchange_is_selected(self):
        if self.ticket_id:
            self.ticket_id.has_selected_exchanges = any(self.ticket_id.vehicle_exchange_ids.mapped('is_selected'))

    @api.depends('ticket_id', 'ticket_id.vehicle_detail_ids.vehicle_id')
    def _compute_available_vehicle_ids(self):
        for rec in self:
            if rec.ticket_id and rec.ticket_id.vehicle_detail_ids:
                rec.available_vehicle_ids = rec.ticket_id.vehicle_detail_ids.mapped('vehicle_id')
            else:
                rec.available_vehicle_ids = self.env['fleet.vehicle'].search([])

    @api.depends('vehicle_a_id', 'vehicle_b_id')
    def _compute_exchange_code(self):
        for rec in self:
            a = rec.vehicle_a_id.id or 0
            b = rec.vehicle_b_id.id or 0
            rec.exchange_code = f"A{a}-B{b}"

    @api.onchange('vehicle_a_id')
    def _onchange_vehicle_a_id(self):
        """Khi chọn xe A, tự động đưa giá và lọc xe B sẵn sàng."""
        if self.vehicle_a_id:
            price = 0.0
            if self.ticket_id:
                t_line = self.ticket_id.vehicle_detail_ids.filtered(lambda l: l.vehicle_id == self.vehicle_a_id)
                if t_line:
                    price = t_line[0].vehicle_price
            if not price:
                price = getattr(self.vehicle_a_id, 'car_value', 0.0) or getattr(self.vehicle_a_id, 'purchase_price', 0.0) or 0.0
            self.vehicle_price = price
            domain = [
                ('operational_status', '=', 'available'),
                ('id', '!=', self.vehicle_a_id.id),
            ]
            if self.vehicle_a_id.model_id:
                domain.append(('model_id', '=', self.vehicle_a_id.model_id.id))
            return {'domain': {'vehicle_b_id': domain}}

    @api.constrains('vehicle_b_id')
    def _check_vehicle_b_ready(self):
        """Đảm bảo xe B còn sẵn sàng trước khi lưu."""
        for rec in self:
            if not rec.vehicle_b_id:
                continue
            if rec.status == 'confirmed' and rec.vehicle_b_id.operational_status not in ('available', 'renting'):
                raise ValidationError(_(
                    "Xe B (%s) không ở trạng thái ‘Sẵn sàng’. Không thể dùng để đổi.") %
                    rec.vehicle_b_id.display_name)

    # ---------------------------------------------------------------------
    # Create & Auto Workflow
    # ---------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            ticket = self.env['rental.operation.ticket'].browse(vals.get('ticket_id'))
            vehicle_a = self.env['fleet.vehicle'].browse(vals.get('vehicle_a_id'))
            vehicle_b = self.env['fleet.vehicle'].browse(vals.get('vehicle_b_id'))
            line_a = ticket.vehicle_detail_ids.filtered(lambda line: line.vehicle_id == vehicle_a)
            if ticket.contract_id.state != 'in_progress' or not line_a or line_a[0].status != 'renting':
                raise ValidationError(_('Chỉ được đổi xe A đang cho thuê trong hợp đồng đang thuê.'))
            if vehicle_a == vehicle_b or vehicle_a.model_id != vehicle_b.model_id:
                raise ValidationError(_('Xe B phải khác xe A và cùng dòng xe.'))
            if (vehicle_b.operational_status != 'available' or not vehicle_b.technical_ready
                    or vehicle_b.rental_blocked):
                raise ValidationError(_('Xe B chưa sẵn sàng để đổi.'))
            if not vals.get('name') or vals.get('name') == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.vehicle.exchange') or _('Mới')
            vals['status'] = 'confirmed'

        records = super().create(vals_list)

        for rec in records:
            # B vẫn Sẵn sàng; chỉ khi xác nhận biên lai giao B mới thành Đang thuê.
            # Giữ giá thuê tham khảo trên phiếu vận hành, chưa thêm B vào hợp đồng.
            contract = rec.ticket_id.contract_id if rec.ticket_id else False
            daily_rate = 0.0
            vehicle_type = False
            if rec.vehicle_b_id.model_id:
                vehicle_type = self.env['rental.vehicle.type'].search([
                    ('model_id', '=', rec.vehicle_b_id.model_id.id),
                    ('active', '=', True)
                ], limit=1)

            if not vehicle_type and contract and contract.line_ids:
                line_a = contract.line_ids.filtered(lambda l: l.vehicle_id == rec.vehicle_a_id)
                vehicle_type = line_a[0].vehicle_type_id if line_a else contract.line_ids[0].vehicle_type_id

            if vehicle_type:
                daily_rate = vehicle_type.daily_rate
            elif contract and contract.line_ids:
                line_a = contract.line_ids.filtered(lambda l: l.vehicle_id == rec.vehicle_a_id)
                daily_rate = line_a[0].daily_rate if line_a else 0.0

            # Thêm B vào vận hành ở trạng thái Chưa giao để thu hồi A không kết thúc phiếu.
            # trạng thái chưa giao xe, ngày & giờ giao trống, địa chỉ nhận mặc định tại cửa hàng
            if rec.ticket_id:
                ext_condition = self.env['rental.operation.ticket.vehicle']._get_vehicle_exterior_condition(rec.vehicle_b_id)
                t_line_vals = {
                    'ticket_id': rec.ticket_id.id,
                    'vehicle_id': rec.vehicle_b_id.id,
                    'vehicle_price': daily_rate,
                    'status': 'waiting',
                    'subfleet': True,
                    'delivery_date': False,
                    'delivery_time': False,
                    'delivery_location': 'Tại cửa hàng',
                    'is_selected': False,
                    'delivery_visual_note': ext_condition,
                }
                t_line = self.env['rental.operation.ticket.vehicle'].with_context(allow_vehicle_exchange=True).create(t_line_vals)
                rec.ticket_line_b_id = t_line.id

        return records

    def write(self, vals):
        """Không cho sửa cặp xe của phiếu đổi đã tạo, tránh lệch biên lai và hợp đồng."""
        if {'ticket_id', 'vehicle_a_id', 'vehicle_b_id'} & vals.keys():
            raise UserError(_('Không được đổi xe hoặc phiếu vận hành của yêu cầu đã tạo. Hãy hủy yêu cầu trước khi thu hồi A.'))
        return super().write(vals)

    # ---------------------------------------------------------------------
    # Actions & State Transitions
    # ---------------------------------------------------------------------
    def action_open_exchange_detail(self):
        """Mở chi tiết phiếu đổi xe dạng modal popup"""
        self.ensure_one()
        return {
            'name': _('Chi Tiết Đổi Xe: %s') % (self.name or ''),
            'type': 'ir.actions.act_window',
            'res_model': 'rental.vehicle.exchange',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_cancel(self):
        """Chỉ hủy phiếu đổi khi A chưa thu hồi và B chưa bắt đầu giao."""
        for rec in self:
            if rec.status == 'done':
                raise UserError(_('Không thể hủy yêu cầu đổi xe đã hoàn thành.'))
            if rec.status == 'cancelled':
                rec.is_selected = False
                continue
            if rec.ticket_line_b_id and rec.ticket_line_b_id.status in ('delivering', 'renting', 'returned'):
                raise UserError(_('Xe B (%s) đã bắt đầu giao hoặc đã được bàn giao cho khách, không thể hủy yêu cầu đổi xe!') % rec.vehicle_b_id.display_name)
            line_a = rec.ticket_id.vehicle_detail_ids.filtered(lambda line: line.vehicle_id == rec.vehicle_a_id)
            if line_a and line_a[0].status == 'returned':
                raise UserError(_('Xe A đã được thu hồi, không thể hủy yêu cầu đổi xe.'))

            # 1. Xóa dòng xe B trong chi tiết vận hành
            if rec.ticket_line_b_id:
                rec.ticket_line_b_id.with_context(allow_vehicle_exchange=True).unlink()
            elif rec.ticket_id and rec.vehicle_b_id:
                old_t_lines = rec.ticket_id.vehicle_detail_ids.filtered(lambda l: l.vehicle_id == rec.vehicle_b_id and l.status == 'waiting')
                if old_t_lines:
                    old_t_lines.with_context(allow_vehicle_exchange=True).unlink()

            # 2. Xóa dòng xe B trong chi tiết hợp đồng
            if rec.contract_line_b_id:
                rec.contract_line_b_id.with_context(allow_vehicle_exchange=True).unlink()

            rec.status = 'cancelled'
            rec.is_selected = False
