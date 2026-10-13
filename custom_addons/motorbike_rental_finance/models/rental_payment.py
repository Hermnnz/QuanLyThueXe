    # 1. Đầu file: Các dòng import
from odoo import api, fields, models
from odoo.exceptions import ValidationError


    # 2. Khai báo Class và các thuộc tính Model ( _name , _description ...)
class MotorbikeRentalPayment(models.Model):
    _name = "motorbike.rental.payment"
    _description = "Motorbike Rental Payment"

    # 3. Khai báo các trường dữ liệu ( fields )
    name= fields.Char(
        string="Mã thanh toán", 
        required=True,
    )
    
    # ==> name cần tự động tính dựa trên loại giao dịch và ngày thanh toán (VD: DP-20230901-001, RP-20230901-001, RF-20230901-001, AP-20230901-001)
    
    customer_id = fields.Many2one(
        "res.partner",
        string = "Khách hàng",
        required = True,
    )
    
    contract_id= fields.Many2one(
        "rental.contract",
        string="Hợp đồng thuê",
        ondelete="set null"
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
    
    invoice_id=fields.Many2one(
        "account.move",
        string="Hóa đơn",
    )

# 4. Các hàm Constraints ( @api.constrains , _sql_constraints )
    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Số tiền thanh toán phải lớn hơn 0!")

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )

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
        
        