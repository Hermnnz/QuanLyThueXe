# 1. Đầu file: Các dòng import
from odoo import Command, api, fields, models
from odoo.exceptions import UserError, ValidationError


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
        index=True,
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
        ondelete="restrict",
    )
    quantity = fields.Float(
        string="Số lượng",
        required=True,
        default=1.0,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Loại tiền",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    unit_price = fields.Monetary(
        string="Đơn giá",
        required=True,
        currency_field="currency_id",
    )
    charge_date = fields.Date(
        string="Ngày ghi nhận",
        required=True,
        default=fields.Date.context_today,
    )
    state = fields.Selection(
        string="Trạng thái",
        selection=[
            ("draft", "Bản nháp"),
            ("confirmed", "Đã xác nhận"),
            ("cancelled", "Đã hủy"),
        ],
        default="draft",
        required=True,
        copy=False,
    )
    note = fields.Text(
        string="Ghi chú",
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Hóa đơn",
        ondelete="set null",
        copy=False,
        readonly=True,
    )
    amount = fields.Monetary(
        string="Thành tiền",
        currency_field="currency_id",
        compute="_compute_amount",
        store=True,
    )

    # 4. Các hàm Constraints ( @api.constrains , _sql_constraints )
    @api.constrains("quantity", "unit_price")
    def _check_positive_values(self):
        for record in self:
            if record.quantity <= 0 or record.unit_price <= 0:
                raise ValidationError("Số lượng và đơn giá phải là các giá trị dương!")

    @api.constrains("contract_id", "customer_id")
    def _check_contract_customer(self):
        for record in self:
            if record.contract_id and record.contract_id.customer_id != record.customer_id:
                raise ValidationError("Khách hàng trên phiếu phí phải trùng với khách hàng của Hợp đồng thuê!")

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )
    @api.depends("quantity", "unit_price")
    def _compute_amount(self):
        for record in self:
            record.amount = record.quantity * record.unit_price

    @api.onchange("contract_id")
    def _onchange_contract_id(self):
        """Tự động điền Khách hàng và Tiền tệ khi chọn Hợp đồng."""
        if self.contract_id:
            self.customer_id = self.contract_id.customer_id
            if self.contract_id.currency_id:
                self.currency_id = self.contract_id.currency_id

    @api.onchange("price_catalog_id")
    def _onchange_price_catalog_id(self):
        if self.price_catalog_id:
            self.unit_price = self.price_catalog_id.unit_price
            self.name = self.price_catalog_id.name

    # 6. Các hàm Action / Nghiệp vụ (nút bấm button)
    def action_confirm(self):
        for record in self:
            if record.contract_id and record.contract_id.settlement_status == "settled":
                raise UserError("Không thể xác nhận thêm phí cho hợp đồng đã quyết toán!")
            record.state = "confirmed"

    def action_cancel(self):
        for record in self:
            if record.invoice_id and record.invoice_id.state != "cancel":
                raise UserError("Không thể hủy khoản phí đã xuất hóa đơn! Vui lòng hủy hóa đơn trước.")
            if record.contract_id and record.contract_id.settlement_status == "settled":
                raise UserError("Không thể hủy khoản phí của hợp đồng đã quyết toán!")
            record.state = "cancelled"

    def action_draft(self):
        for record in self:
            if record.invoice_id and record.invoice_id.state != "cancel":
                raise UserError("Không thể đưa về nháp khoản phí đã gắn với hóa đơn đang hiệu lực!")
            if record.contract_id and record.contract_id.settlement_status == "settled":
                raise UserError("Không thể chỉnh sửa khoản phí của hợp đồng đã quyết toán!")
            record.state = "draft"

    def action_create_invoice(self):
        """Hỗ trợ xuất hóa đơn cho 1 hoặc gộp nhiều khoản phí của cùng 1 khách hàng."""
        if not self:
            return

        # 1. Nếu chỉ chọn 1 bản ghi và đã có hóa đơn chưa bị hủy -> mở hóa đơn đó lên
        if len(self) == 1 and self.invoice_id and self.invoice_id.state != "cancel":
            return {
                "name": "Hóa đơn khách hàng",
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "res_id": self.invoice_id.id,
                "view_mode": "form",
                "target": "current",
            }

        # 2. Kiểm tra điều kiện hợp lệ trước khi tạo hóa đơn
        if any(rec.state != "confirmed" for rec in self):
            raise UserError("Tất cả các khoản phí phải ở trạng thái 'Đã xác nhận' trước khi tạo hóa đơn!")
        if any(rec.invoice_id and rec.invoice_id.state != "cancel" for rec in self):
            raise UserError("Có khoản phí đã được xuất hóa đơn rồi, không thể tạo trùng!")
        if len(self.mapped("customer_id")) > 1:
            raise UserError("Chỉ có thể gộp hóa đơn cho các khoản phí của cùng một khách hàng!")
        if len(self.mapped("currency_id")) > 1:
            raise UserError("Các khoản phí phải cùng một loại tiền tệ mới có thể gộp chung hóa đơn!")

        # 3. Chuẩn bị các dòng chi tiết hóa đơn (Đồng bộ đầy đủ charge_id & price_catalog_id với account_move.py)
        invoice_lines = [
            Command.create({
                "name": f"Phụ phí: {rec.name}",
                "quantity": rec.quantity,
                "price_unit": rec.unit_price,
                "charge_id": rec.id,
                "price_catalog_id": rec.price_catalog_id.id if rec.price_catalog_id else False,
            })
            for rec in self
        ]

        # Không gắn contract_id ở đây để tránh việc hóa đơn thiếu tiền xe tự động đóng hợp đồng
        # Hóa đơn quyết toán đóng hợp đồng chuẩn sẽ được xuất từ menu Hóa đơn (chọn Hợp đồng có cả tiền thuê xe)
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": self[0].customer_id.id,
            "currency_id": self[0].currency_id.id,
            "contract_id": False,
            "invoice_date": fields.Date.context_today(self),
            "invoice_line_ids": invoice_lines,
        }

        # 4. Tạo hóa đơn và liên kết ngược lại các phiếu phí
        invoice = self.env["account.move"].create(invoice_vals)
        self.write({"invoice_id": invoice.id})

        return {
            "name": "Hóa đơn khách hàng",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }