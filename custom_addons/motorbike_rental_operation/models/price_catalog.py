# -*- coding: utf-8 -*-
from odoo import fields, models, api

class MotorbikeRentalPriceCatalog(models.Model):
    _name = "motorbike.rental.price.catalog"
    _description = "Bảng giá Phụ phí & Bồi thường Sự cố"

    incident_code = fields.Char(string="Mã sự cố", required=True, copy=False, readonly=True, default="Mới")
    name = fields.Char(string="Tên khoản giá/sự cố", required=True)
    code = fields.Char(string="Ký hiệu", copy=True, help="Ký hiệu viết tắt (VD: BT-MU-BH, DV-GIAO-XE)")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('incident_code') or vals.get('incident_code') == 'Mới':
                vals['incident_code'] = self.env['ir.sequence'].next_by_code('motorbike.rental.price.catalog.incident') or 'Mới'
        return super(MotorbikeRentalPriceCatalog, self).create(vals_list)

    def _compute_display_name(self):
        for rec in self:
            inc_str = f"[{rec.incident_code}] " if rec.incident_code and rec.incident_code != 'Mới' else ""
            sym_str = f"({rec.code}) " if rec.code else ""
            rec.display_name = f"{inc_str}{sym_str}{rec.name}"

    
    category = fields.Selection([
        ("service", "Dịch vụ"),
        ("surcharge", "Phụ phí"),
        ("compensation", "Bồi thường hư hỏng")
    ], string="Loại bảng giá", required=True, default="compensation")
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Loại tiền",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    unit_price = fields.Monetary(string="Đơn giá", required=True, currency_field="currency_id")
    
    unit = fields.Selection([
        ("time", "Lần"),
        ("hour", "Giờ"),
        ("day", "Ngày"),
        ("item", "Cái"),
        ("set", "Bộ")
    ], string="Đơn vị", required=True, default="item")
    
    effective_from = fields.Date(string="Ngày bắt đầu áp dụng")
    effective_to = fields.Date(string="Ngày kết thúc áp dụng")
    
    active = fields.Boolean(string="Đang áp dụng", default=True)
    note = fields.Text(string="Ghi chú")
