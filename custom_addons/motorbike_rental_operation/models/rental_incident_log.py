# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class RentalIncidentLog(models.Model):
    _name = 'rental.operation.incident.log'
    _description = 'Nhật ký Sự cố & Hư hỏng'

    name = fields.Char(string='Mã Ghi nhận (Mã INC)', required=True, copy=False, readonly=True, default='Mới')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.operation.incident.log')
        return super(RentalIncidentLog, self).create(vals_list)

    ticket_id = fields.Many2one('rental.operation.ticket', string='Thuộc Phiếu Vận Hành', ondelete='cascade')
    
    # Ô tick chọn phục vụ thao tác hàng loạt
    is_selected = fields.Boolean(string='Chọn', default=False)
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='ticket_id.currency_id',
        store=True,
        readonly=True,
    )

    price_catalog_id = fields.Many2one(
        'motorbike.rental.price.catalog',
        string='Loại sự cố / Bồi thường',
        domain="[('category', 'in', ('compensation', 'surcharge'))]",
    )

    penalty_amount = fields.Monetary(
        string='Tiền phạt / Bồi thường',
        currency_field='currency_id',
    )

    @api.onchange('price_catalog_id')
    def _onchange_price_catalog_id(self):
        if self.price_catalog_id:
            self.penalty_amount = self.price_catalog_id.unit_price
            if not self.damage_description:
                self.damage_description = self.price_catalog_id.name

    
    available_vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        compute='_compute_available_vehicle_ids',
        string='Xe có trong phiếu'
    )

    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Xe gặp sự cố',
        required=True,
        domain="[('id', 'in', available_vehicle_ids)]"
    )

    @api.depends('ticket_id', 'ticket_id.vehicle_detail_ids.vehicle_id')
    def _compute_available_vehicle_ids(self):
        for rec in self:
            if rec.ticket_id and rec.ticket_id.vehicle_detail_ids:
                rec.available_vehicle_ids = rec.ticket_id.vehicle_detail_ids.mapped('vehicle_id')
            else:
                rec.available_vehicle_ids = self.env['fleet.vehicle'].search([])

    date_reported = fields.Datetime(string='Ngày giờ ghi nhận', default=fields.Datetime.now)

    fault_party = fields.Selection([
        ('customer', 'Lỗi do Khách hàng'),
        ('vehicle', 'Lỗi do Xe / Công ty')
    ], string='Lỗi thuộc về', required=True, default='customer')

    damage_description = fields.Text(string='Mô tả chi tiết lỗi')

    needs_repair = fields.Boolean(string='Cần sửa chữa', default=True)

    status = fields.Selection([
        ('new', 'Mới'),
        ('processing', 'Đang xử lý'),
        ('resolved', 'Đã giải quyết')
    ], string='Trạng thái', default='new')

    def _get_incident_label(self):
        self.ensure_one()
        veh_name = self.vehicle_id.display_name or self.vehicle_id.name or 'Xe'
        return f"{self.name} (Xe {veh_name})"

    def action_start_processing(self):
        """Xác nhận bắt đầu xử lý sự cố"""
        for rec in self:
            label = rec._get_incident_label()
            if rec.status == 'resolved':
                raise UserError(f'Sự cố {label} đã được giải quyết hoàn tất!')
            if rec.status == 'processing':
                raise UserError(f'Sự cố {label} đang trong quá trình xử lý!')
            rec.write({
                'status': 'processing',
                'is_selected': False,
            })

    def action_resolve(self):
        """Xác nhận sự cố đã được xử lý / khắc phục hoàn tất"""
        for rec in self:
            label = rec._get_incident_label()
            if rec.status == 'new':
                raise UserError(f'Sự cố {label} chưa được bắt đầu xử lý!')
            if rec.status == 'resolved':
                raise UserError(f'Sự cố {label} đã hoàn tất trước đó!')
            rec.write({
                'status': 'resolved',
                'is_selected': False,
            })

