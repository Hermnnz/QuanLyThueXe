# -*- coding: utf-8 -*-
"""Model cho quy trình đổi xe trong module vận hành.

- Trạng thái: Chưa thực hiện, Đang thực hiện, Thực hiện thành công, Hủy
- Ngăn tạo đổi chồng lên cùng một xe A nếu bản ghi chưa hủy
- Kiểm tra xe B sẵn sàng
- Khi hoàn thành, xe B chuyển sang trạng thái 'renting', xe A chuyển sang 'maintenance'
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
        'rental.operation.ticket', string='Phiếu vận hành', ondelete='cascade', index=True
    )
    request_date = fields.Datetime(
        string='Thời gian yêu cầu', default=fields.Datetime.now, readonly=True
    )
    status = fields.Selection([
        ('draft', 'Chưa thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Thực hiện thành công'),
        ('cancelled', 'Hủy'),
    ], string='Trạng thái', default='draft', required=True, copy=False)

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
        'res.currency', string='Tiền tệ',
        related='vehicle_a_id.currency_id', store=True, readonly=True)
    exchange_code = fields.Char(
        string='Mã hoán đổi', compute='_compute_exchange_code',
        store=True, readonly=True)

    # ---------------------------------------------------------------------
    # Constraints & validations
    # ---------------------------------------------------------------------
    _sql_constraints = [
        ('unique_active_exchange_per_vehicle_a',
         'UNIQUE(vehicle_a_id, status)',
         'Xe này đã có một bản ghi đổi xe đang hoạt động (chưa hủy). ' \
         'Hãy hủy bản ghi cũ trước khi tạo mới.')
    ]

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
            self.vehicle_price = self.vehicle_a_id.purchase_price or 0.0
            domain = [
                ('operational_status', '=', 'available'),
                ('id', '!=', self.vehicle_a_id.id),
            ]
            if self.vehicle_a_id.model_id:
                domain.append(('model_id', '=', self.vehicle_a_id.model_id.id))
            return {'domain': {'vehicle_b_id': domain}}

    @api.constrains('vehicle_b_id')
    def _check_vehicle_b_ready(self):
        """Đảm bảo xe B còn sẵn sàng."""
        for rec in self:
            if not rec.vehicle_b_id:
                continue
            if rec.status == 'draft' and rec.vehicle_b_id.operational_status != 'available':
                raise ValidationError(_(
                    "Xe B (%s) không ở trạng thái ‘Sẵn sàng’. Không thể dùng để đổi.") %
                    rec.vehicle_b_id.display_name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('Mới'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.vehicle.exchange') or _('Mới')
        return super().create(vals_list)

    # ---------------------------------------------------------------------
    # Actions & State transitions
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

    def action_start(self):
        """Chuyển sang trạng thái Đang thực hiện."""
        for rec in self:
            if rec.status != 'draft':
                raise UserError(_('Chỉ có bản ghi ở trạng thái “Chưa thực hiện” mới có thể bắt đầu.'))
            rec.status = 'in_progress'

    def action_done(self):
        """Kết thúc đổi xe – xe B chuyển sang 'renting', xe A chuyển sang 'maintenance'."""
        for rec in self:
            if rec.status != 'in_progress':
                raise UserError(_('Chỉ có bản ghi đang thực hiện mới có thể đánh dấu thành công.'))
            rec.vehicle_b_id.sudo().write({'operational_status': 'renting'})
            rec.vehicle_a_id.sudo().write({'operational_status': 'maintenance', 'technical_ready': False})
            if rec.ticket_id:
                ticket_line = rec.ticket_id.vehicle_detail_ids.filtered(lambda l: l.vehicle_id == rec.vehicle_a_id)
                if ticket_line:
                    ticket_line.write({'vehicle_id': rec.vehicle_b_id.id})
            rec.status = 'done'

    def action_cancel(self):
        """Hủy đổi xe."""
        for rec in self:
            if rec.status == 'done':
                raise UserError(_('Không được hủy một bản ghi đã hoàn thành.'))
            rec.status = 'cancelled'
