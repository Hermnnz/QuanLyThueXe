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

        # 3. Chuẩn bị các dòng chi tiết hóa đơn (hỗ trợ gộp nhiều phí vào 1 hóa đơn)
        invoice_lines = [
            Command.create({
                "name": rec.name,
                "quantity": rec.quantity,
                "price_unit": rec.unit_price,
            })
            for rec in self
        ]

        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": self[0].customer_id.id,
            "currency_id": self[0].currency_id.id,
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
    