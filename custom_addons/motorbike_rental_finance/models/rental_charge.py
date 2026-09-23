from odoo import fields, models 

class MotorbikeRentalCharge(models.Model):
    _name = "motorbike.rental.charge"
    _description = "Motorbike Rental Charge"

    name = fields.Char(
        string="Tên khoản phí",
        required=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Khách hàng",
        required=True,
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
    
    # TODO Week 7:
    # amount = quantity * unit_price
    # Chưa implement ở Week 5 vì phần tính toán tự động thuộc business logic.