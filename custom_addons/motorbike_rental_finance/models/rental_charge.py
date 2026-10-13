# 1. Đầu file: Các dòng import
from odoo import api, fields, models
from odoo.exceptions import ValidationError


# 2. Khai báo Class và các thuộc tính Model ( _name , _description ...)
class MotorbikeRentalCharge(models.Model):
    _name = "motorbike.rental.charge"
    _description = "Motorbike Rental Charge"

    # 3. Khai báo các trường dữ liệu ( fields )
    name = fields.Char(
        string="Tên khoản phí",
        required=True,
    )

    customer_id = fields.Many2one(
        "res.partner",
        string="Khách hàng",
        required=True,
    )
    
    contract_id = fields.Many2one(
        "rental.contract",
        string="Hợp đồng thuê",
        ondelete="set null",
    )

    ticket_id = fields.Many2one(
        "rental.operation.ticket",
        string="Phiếu vận hành",
        ondelete="set null",
    )
    
    incident_id = fields.Many2one(
        "rental.operation.incident.log",
        string="Phiếu sự cố",
        ondelete="set null",
    )
     
    price_catalog_id = fields.Many2one(
        "motorbike.rental.price.catalog",
        string="Bảng giá áp dụng",
        required=True,
    )
    
    quantity=fields.Float(
        string="Số lượng",
        required=True,
        default=1.0,
    )
    
    currency_id=fields.Many2one(
        "res.currency",
        string="Loại tiền",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    
    unit_price=fields.Monetary(
        string="Đơn giá",
        required=True,
        currency_field="currency_id"
    )
    
    charge_date=fields.Date(
        string="Ngày ghi nhận",
        required=True,
        default=fields.Date.context_today,
    )
    
    state=fields.Selection(
        string="Trạng thái",
        selection=[("draft", "Bản nháp"), ("confirmed", "Đã xác nhận"), ("cancelled", "Đã hủy")],
        default="draft",
        required=True,
    )
    
    note=fields.Text(
        string="Ghi chú",
    )
    
    invoice_id=fields.Many2one(
        "account.move",
        string="Hóa đơn",
    )
    
    amount = fields.Monetary(
        string="Thành tiền",
        currency_field="currency_id",
        compute="_compute_amount",
        store=True,
    )

    # 4. Các hàm Constraints ( @api.constrains , _sql_constraints )
    @api.constrains('quantity','unit_price')
    def _check_positive_values(self):
        for record in self:
            if record.quantity <= 0 or record.unit_price <= 0:
                raise ValidationError("Số lượng và đơn giá phải là các giá trị dương!")

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )
    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for record in self:
            record.amount = record.quantity * record.unit_price
    
    
    @api.onchange('price_catalog_id')
    def _onchange_price_catalog_id(self):
        if self.price_catalog_id:
            self.unit_price = self.price_catalog_id.unit_price
            if not self.name:
                self.name = self.price_catalog_id.name

    # 6. Các hàm Action / Nghiệp vụ (nút bấm button)
    
    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'
    
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
        
    def action_draft(self):
        for record in self:
            record.state = 'draft'  