# 1. Đầu file: Các dòng import
from odoo import fields, models


# 2. Khai báo Class và các thuộc tính Model ( _name , _description ...)
class AccountMove(models.Model):
    _inherit = "account.move"

    # 3. Khai báo các trường dữ liệu ( fields )
    # One2many Payment ở đây
    rental_payments_ids = fields.One2many(
        "motorbike.rental.payment",  # model đích
        "invoice_id",  # field many2one bên đích
        string="Thanh toán",  # tên hiển thị
    )

    # One2many Charge ở đây
    rental_charges_ids = fields.One2many(
        "motorbike.rental.charge",  # model đích
        "invoice_id",  # field many2one bên đích
        string="Khoản phí",  # tên hiển thị
    )

    # 4. Các hàm Constraints ( @api.constrains , _sql_constraints )

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )

    # 6. Các hàm Action / Nghiệp vụ (nút bấm button)