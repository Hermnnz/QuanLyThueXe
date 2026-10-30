# -*- coding: utf-8 -*-
"""Model cho quy trình đổi xe trong module vận hành.

- Trạng thái: Xác nhận (confirmed), Hoàn thành (done), Hủy (cancelled)
- Khi vừa tạo bản ghi mới:
  + Cập nhật trạng thái xe B trong Fleet sang 'renting' (Đang thuê)
  + Thêm xe B vào chi tiết Hợp đồng (rental.contract.line)
  + Thêm xe B vào chi tiết Vận hành (rental.operation.ticket.vehicle) với trạng thái 'waiting' (Chưa giao),
    ngày/giờ giao trống, địa điểm nhận mặc định 'Tại cửa hàng'
  + Trạng thái bản ghi đổi xe = 'confirmed' (Xác nhận)
- Tự động hoàn thành (done):
  + Khi Xe B giao thành công (status in ('renting', 'returned')) VÀ Xe A đã thu hồi xong (status == 'returned')
  + Xe A chuyển sang trạng thái 'maintenance' (Bảo dưỡng) trong Fleet
- Khi bấm nút Hủy:
  + Hoàn tác: Xóa xe B khỏi Hợp đồng & Phiếu vận hành, trả xe B về 'available' (Sẵn sàng) trong Fleet
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
    vehicle_b_id = fields.Many2one(
        'fleet.vehicle', string='Xe B (xe thay thế)', required=True,
        domain="[('operational_status', '=', 'available')]",
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
            if not vals.get('name') or vals.get('name') == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.vehicle.exchange') or _('Mới')
            vals['status'] = 'confirmed'

        records = super().create(vals_list)

        for rec in records:
            # 1. Cập nhật trạng thái xe B trong Fleet chuyển sang 'renting' (Đang thuê)
            if rec.vehicle_b_id:
                rec.vehicle_b_id.sudo().write({'operational_status': 'renting'})

            # Xác định giá thuê hàng ngày và dòng xe theo mã xe B
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

            # 2. Thêm xe B vào chi tiết Hợp đồng (rental.contract.line)
            if contract:
                c_line_vals = {
                    'contract_id': contract.id,
                    'vehicle_id': rec.vehicle_b_id.id,
                    'vehicle_type_id': vehicle_type.id if vehicle_type else False,
                    'daily_rate': daily_rate,
                    'notes': f"Xe thay thế cho {rec.vehicle_a_id.display_name} (Mã đổi: {rec.name})",
                }
                c_line = self.env['rental.contract.line'].with_context(allow_vehicle_exchange=True).create(c_line_vals)
                rec.contract_line_b_id = c_line.id

            # 3. Thêm xe B vào chi tiết Vận hành (rental.operation.ticket.vehicle)
            # trạng thái chưa giao xe, ngày & giờ giao trống, địa chỉ nhận mặc định tại cửa hàng
            if rec.ticket_id:
                ext_condition = self.env['rental.operation.ticket.vehicle']._get_vehicle_exterior_condition(rec.vehicle_b_id)
                t_line_vals = {
                    'ticket_id': rec.ticket_id.id,
                    'vehicle_id': rec.vehicle_b_id.id,
                    'vehicle_price': daily_rate,
                    'status': 'waiting',
                    'delivery_date': False,
                    'delivery_time': False,
                    'delivery_location': 'Tại cửa hàng',
                    'is_selected': False,
                    'delivery_visual_note': ext_condition,
                }
                t_line = self.env['rental.operation.ticket.vehicle'].with_context(allow_vehicle_exchange=True).create(t_line_vals)
                rec.ticket_line_b_id = t_line.id

        return records

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
        """Hủy đổi xe: Hoàn tác xe B, trả trạng thái về available, chuyển status thành cancelled."""
        for rec in self:
            if rec.status == 'done':
                raise UserError(_('Không thể hủy yêu cầu đổi xe đã hoàn thành.'))
            if rec.status == 'cancelled':
                rec.is_selected = False
                continue
            if rec.ticket_line_b_id and rec.ticket_line_b_id.status in ('delivering', 'renting', 'returned'):
                raise UserError(_('Xe B (%s) đã bắt đầu giao hoặc đã được bàn giao cho khách, không thể hủy yêu cầu đổi xe!') % rec.vehicle_b_id.display_name)

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
            elif rec.ticket_id and rec.ticket_id.contract_id and rec.vehicle_b_id:
                old_c_lines = rec.ticket_id.contract_id.line_ids.filtered(lambda l: l.vehicle_id == rec.vehicle_b_id)
                if old_c_lines:
                    old_c_lines.with_context(allow_vehicle_exchange=True).unlink()

            # 3. Trả lại trạng thái xe B trong Fleet về 'available'
            if rec.vehicle_b_id:
                self.env.cr.execute("""
                    UPDATE fleet_vehicle
                    SET operational_status = 'available',
                        technical_ready = TRUE
                    WHERE id = %s
                """, (rec.vehicle_b_id.id,))
                rec.vehicle_b_id.invalidate_recordset(['operational_status', 'technical_ready'])

            rec.status = 'cancelled'
            rec.is_selected = False
