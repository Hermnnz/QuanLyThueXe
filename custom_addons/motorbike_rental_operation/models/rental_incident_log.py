# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RentalIncidentLog(models.Model):
    _name = 'rental.operation.incident.log'
    _description = 'Nhật ký Sự cố & Hư hỏng'

    name = fields.Char(string='Mã sự cố', required=True, copy=False, readonly=True, default='Mới')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.operation.incident.log')
            if vals.get('price_catalog_id') and not vals.get('unit_price'):
                catalog = self.env['motorbike.rental.price.catalog'].browse(vals['price_catalog_id'])
                vals['unit_price'] = catalog.unit_price
            if 'quantity' not in vals:
                vals['quantity'] = 1
            if 'penalty_amount' not in vals:
                qty = vals.get('quantity') if vals.get('quantity') is not None else 1
                price = vals.get('unit_price') or 0.0

            # Đồng bộ hai chiều giữa needs_repair_display và needs_repair
            if 'needs_repair_display' in vals:
                vals['needs_repair'] = (vals['needs_repair_display'] == 'yes')
            elif 'needs_repair' in vals:
                vals['needs_repair_display'] = 'yes' if vals['needs_repair'] else 'no'
            else:
                vals['needs_repair'] = True
                vals['needs_repair_display'] = 'yes'
        records = super(RentalIncidentLog, self.with_context(skip_needs_repair_inverse=True)).create(vals_list)
        # Tự động đồng bộ sang Fleet ngay sau khi tạo bản ghi sự cố
        for rec in records:
            rec._sync_to_fleet_service()
        return records

    def write(self, vals):
        if not self.env.context.get('skip_needs_repair_inverse'):
            if 'needs_repair_display' in vals and 'needs_repair' not in vals:
                vals['needs_repair'] = (vals['needs_repair_display'] == 'yes')
            elif 'needs_repair' in vals and 'needs_repair_display' not in vals:
                vals['needs_repair_display'] = 'yes' if vals['needs_repair'] else 'no'
        res = super(RentalIncidentLog, self).write(vals)
        return res

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

    quantity = fields.Integer(
        string='Số lượng / Số giờ',
        default=1,
    )

    unit = fields.Selection(
        related='price_catalog_id.unit',
        string='Đơn vị tính',
        readonly=True,
    )

    unit_price = fields.Monetary(
        string='Đơn giá',
        currency_field='currency_id',
    )

    penalty_amount = fields.Monetary(
        string='Tiền phạt / Bồi thường',
        currency_field='currency_id',
        compute='_compute_penalty_amount',
        store=True,
        readonly=False,
    )

    @api.depends('quantity', 'unit_price', 'price_catalog_id')
    def _compute_penalty_amount(self):
        for rec in self:
            qty = rec.quantity if rec.quantity is not None else 1
            price = rec.unit_price if rec.unit_price else (rec.price_catalog_id.unit_price if rec.price_catalog_id else 0.0)
            rec.penalty_amount = (qty or 0) * (price or 0.0)

    @api.onchange('price_catalog_id')
    def _onchange_price_catalog_id(self):
        if self.price_catalog_id:
            self.unit_price = self.price_catalog_id.unit_price
            if not self.quantity or self.quantity <= 0:
                self.quantity = 1
            self.penalty_amount = (self.quantity or 1) * (self.unit_price or 0.0)
            if not self.damage_description:
                self.damage_description = self.price_catalog_id.name

    @api.onchange('quantity', 'unit_price')
    def _onchange_quantity_price(self):
        qty = self.quantity if self.quantity is not None else 1
        price = self.unit_price if self.unit_price else 0.0
        self.penalty_amount = (qty or 0) * (price or 0.0)

    
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

    needs_repair = fields.Boolean(string='Cần sửa chữa?', default=True)
    needs_repair_display = fields.Selection(
        [
            ('yes', 'Cần sửa chữa'),
            ('no', 'Không cần sửa chữa'),
        ],
        string='Cần sửa chữa?',
        default='yes',
        compute='_compute_needs_repair_display',
        inverse='_inverse_needs_repair_display',
        store=True,
    )

    @api.onchange('ticket_id')
    def _onchange_ticket_id_default_vehicle(self):
        if self.ticket_id and self.ticket_id.vehicle_detail_ids:
            vehicles = self.ticket_id.vehicle_detail_ids.mapped('vehicle_id')
            if len(vehicles) == 1 and not self.vehicle_id:
                self.vehicle_id = vehicles[0]

    @api.depends('needs_repair')
    def _compute_needs_repair_display(self):
        for rec in self:
            rec.needs_repair_display = 'yes' if rec.needs_repair else 'no'

    def _inverse_needs_repair_display(self):
        if self.env.context.get('skip_needs_repair_inverse'):
            return
        for rec in self:
            target_bool = (rec.needs_repair_display == 'yes')
            if rec.needs_repair != target_bool:
                rec.needs_repair = target_bool

    service_id = fields.Many2one(
        'fleet.vehicle.log.services',
        string='Hồ sơ sửa chữa (Fleet)',
        readonly=True,
        copy=False,
    )

    def _sync_to_fleet_service(self):
        """Khi phiếu sự cố có 'Cần sửa chữa?', tự động đổ dữ liệu sang bảng Bảo dưỡng & Sửa chữa của Fleet"""
        if self.env.context.get('skip_sync_fleet'):
            return
        Service = self.env['fleet.vehicle.log.services'].sudo()
        for rec in self.with_context(skip_sync_fleet=True, skip_needs_repair_inverse=True):
            if rec.needs_repair and not rec.service_id and rec.vehicle_id:
                cust_name = False
                cust_phone = False
                if rec.ticket_id and rec.ticket_id.customer_id:
                    cust_name = rec.ticket_id.customer_id.name
                    cust_phone = rec.ticket_id.customer_id.phone or rec.ticket_id.customer_id.mobile

                desc = rec.damage_description or (rec.price_catalog_id.name if rec.price_catalog_id else '')
                full_desc = f"[{rec.name}] {desc}" if desc else f"Sự cố {rec.name}"

                service_type = self.env.ref('motorbike_fleet_management.service_type_electric_maintenance', raise_if_not_found=False)
                if not service_type:
                    service_type = self.env['fleet.service.type'].sudo().search([], limit=1)

                service_vals = {
                    'vehicle_id': rec.vehicle_id.id,
                    'maintenance_type': 'corrective',
                    'description': full_desc,
                    'customer_name': cust_name,
                    'customer_phone': cust_phone,
                    'amount': rec.penalty_amount or 0.0,
                    'date': rec.date_reported.date() if rec.date_reported else fields.Date.context_today(self),
                    'state': 'new',
                    'blocks_rental': True,
                    'notes': f"Tự động tạo từ Sự cố {rec.name} (Phiếu vận hành: {rec.ticket_id.name if rec.ticket_id else 'N/A'})",
                }
                if service_type:
                    service_vals['service_type_id'] = service_type.id

                # Đảm bảo cờ xe máy điện để hiển thị trên menu Bảo dưỡng & Sửa chữa của Fleet
                if hasattr(rec.vehicle_id, 'is_electric_motorbike') and not rec.vehicle_id.is_electric_motorbike:
                    try:
                        rec.vehicle_id.sudo().write({'is_electric_motorbike': True})
                    except Exception:
                        pass

                service = Service.create(service_vals)
                rec.sudo().with_context(skip_sync_fleet=True, skip_needs_repair_inverse=True).write({'service_id': service.id})
                rec.service_id = service

    def action_create_fleet_service(self):
        """Thủ công tạo phiếu bảo dưỡng / sửa chữa sang Fleet nếu chưa có"""
        for rec in self:
            if not rec.vehicle_id:
                raise UserError('Vui lòng chọn xe gặp sự cố trước khi tạo phiếu bảo dưỡng / sửa chữa.')
            rec.sudo().with_context(skip_sync_fleet=True).write({'needs_repair': True, 'needs_repair_display': 'yes'})
            rec.needs_repair = True
            rec.needs_repair_display = 'yes'
        self._sync_to_fleet_service()
        return True

    def action_open_fleet_service(self):
        """Mở hồ sơ bảo dưỡng & sửa chữa bên Fleet"""
        self.ensure_one()
        if not self.service_id:
            raise UserError('Sự cố này chưa được liên kết với hồ sơ bảo dưỡng & sửa chữa nào.')
        return {
            'name': 'Hồ sơ bảo dưỡng & sửa chữa',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.log.services',
            'res_id': self.service_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

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

    def unlink(self):
        """Không cho phép xóa sự cố đã được đồng bộ sang Fleet; icon đã bị ẩn nên không cần thông báo."""
        # Nếu có bản ghi đã đồng bộ, bỏ qua việc xóa (không thực hiện gì)
        records_to_unlink = self.filtered(lambda r: not r.service_id)
        return super(RentalIncidentLog, records_to_unlink).unlink()


