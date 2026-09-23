from odoo import fields, models

class MotorbikeRentalPayment(models.Model):
    _name = "motorbike.rental.payment"
    _description = "Motorbike Rental Payment"
    
    name= fields.Char(
        string="Mã thanh toán", 
        required=True,
    )
    
    # ==> name cần tự động tính dựa trên loại giao dịch và ngày thanh toán (VD: DP-20230901-001, RP-20230901-001, RF-20230901-001, AP-20230901-001)
    
    partner_id = fields.Many2one(
        "res.partner",
        string = "Khách hàng",
        required = True,
    )
    
    transaction_type = fields.Selection(
        string="Loại giao dịch",
        selection=[("deposit", "Cọc"), ("rental_payment", "Thanh toán"), ("refund", "Hoàn tiền"), ("additional_payment", "Thu thêm")],
        required=True,
    )
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Loại tiền",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    
    amount = fields.Monetary(
        string="Số tiền",
        required=True,
        currency_field="currency_id"
    )
    
    # amount cần luôn dương 
    
    payment_method = fields.Selection(
        string="Phương thức thanh toán",
        selection = [("cash", "Tiền mặt"), ("bank_transfer", "Chuyển khoản ngân hàng"), ("credit_card", "Thẻ tín dụng")],
        required=True,
    )
    
    payment_date = fields.Date(
        string="Ngày thanh toán",
        required=True,
        default=fields.Date.context_today,
    )
    
    reference=fields.Char(
        string="Mã tham chiếu",
    )
    
    state=fields.Selection(
        string="Trạng thái",
        selection=[("draft", "Bản nháp"), ("confirmed", "Đã xác nhận"), ("cancelled", "Đã hủy")],
        default="draft",
        required=True,
    )
    
    note = fields.Text(
        string="Ghi chú",
    )