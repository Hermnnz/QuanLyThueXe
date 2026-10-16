# 1. Đầu file: Các dòng import
from odoo import api, fields, models, Command

# 2. Khai báo Class và các thuộc tính Model ( _name , _description ...)
class AccountMove(models.Model):
    _inherit = "account.move"

    # 3. Khai báo các trường dữ liệu ( fields )
    contract_id = fields.Many2one(
        "rental.contract",
        string="Hợp đồng thuê xe",
        index=True,
        ondelete="set null",
        copy=False,
    )
    rental_payments_ids = fields.One2many(
        "motorbike.rental.payment",
        "invoice_id",
        string="Thanh toán",
    )
    rental_charges_ids = fields.One2many(
        "motorbike.rental.charge",
        "invoice_id",
        string="Khoản phí",
    )

    # 4. Các hàm Constraints ( @api.constrains , _sql_constraints )
    

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )
    @api.onchange("contract_id")
    def _onchange_contract_id(self):
        if not self.contract_id:
            return
        contract = self.contract_id
        # Điền thông tin khách hàng và tiền tệ từ hợp đồng
        if contract.customer_id:
            self.partner_id = contract.customer_id
        if contract.currency_id:
            self.currency_id = contract.currency_id
        lines = [Command.clear()]
        # 2.1. Lấy TIỀN THUÊ XE từ Hợp đồng
        if contract.total_amount and contract.total_amount > 0:
            lines.append(Command.create({
                "name": f"Tiền thuê xe máy - Hợp đồng {contract.name}",
                "quantity": 1.0,
                "price_unit": contract.total_amount,
            }))
        # 2.2. Lấy CÁC KHOẢN PHỤ PHÍ ĐÃ XÁC NHẬN của hợp đồng này (chưa xuất hóa đơn)
        confirmed_charges = contract.charge_ids.filtered(
            lambda c: c.state == "confirmed" and (not c.invoice_id or c.invoice_id.state == "cancel")
        )
        for charge in confirmed_charges:
            lines.append(Command.create({
                "name": f"Phụ phí: {charge.name}",
                "quantity": charge.quantity,
                "price_unit": charge.unit_price,
                "charge_id": charge.id,
                "price_catalog_id": charge.price_catalog_id.id if charge.price_catalog_id else False,
            }))
        self.invoice_line_ids = lines

    # 6. Các hàm Action / Nghiệp vụ (nút bấm button)
    
    
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    # Khóa ngoại liên kết Khoản phát sinh
    charge_id = fields.Many2one(
        "motorbike.rental.charge",
        string="Khoản phát sinh",
    )
    # Khóa ngoại liên kết Mục bảng giá
    price_catalog_id = fields.Many2one(
        "motorbike.rental.price.catalog",
        string="Mục bảng giá",
    )
    @api.onchange("charge_id")
    def _onchange_charge_id(self):
        if self.charge_id:
            self.name = f"Phụ phí: {self.charge_id.name}"
            self.quantity = self.charge_id.quantity
            self.price_unit = self.charge_id.unit_price
    @api.onchange("price_catalog_id")
    def _onchange_price_catalog_id(self):
        if self.price_catalog_id:
            self.name = self.price_catalog_id.name
            self.price_unit = self.price_catalog_id.unit_price