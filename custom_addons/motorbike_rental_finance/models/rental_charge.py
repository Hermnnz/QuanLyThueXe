# 1. Đầu file: Các dòng import
from odoo import api, fields, models
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

    @api.model_create_multi
    def create(self, vals_list):  # Chặn tạo phụ phí cho hợp đồng đã hoàn tất.
        for vals in vals_list:
            # browse lấy hợp đồng theo mã số; chưa chọn thì trả tập rỗng.
            contract = self.env["rental.contract"].browse(vals.get("contract_id"))
            if contract.state == "done":
                raise UserError("Hợp đồng đã hoàn tất, không thể tạo thêm phụ phí.")

        return super().create(vals_list)  # Đủ điều kiện thì tạo như bình thường.

    def write(self, vals):  # Chặn chuyển phụ phí vào hợp đồng hoàn tất; phụ phí đã thuộc hợp đồng hoàn tất chỉ được sửa ghi chú.
        # write là hàm Odoo gọi khi lưu thay đổi.
        # self là các khoản phụ phí đang được sửa.
        # vals chứa tên trường và giá trị mới muốn lưu.

        # Chỉ kiểm tra khi dữ liệu lưu có chọn hợp đồng đích.
        if vals.get("contract_id"):
            # browse lấy bản ghi hợp đồng theo ID (mã số trong database).
            contract = self.env["rental.contract"].browse(vals["contract_id"])

            for record in self:  # Kiểm tra từng phiếu đang được sửa.
                # Chặn chuyển sang hợp đồng đã hoàn tất; giữ nguyên hợp đồng thì cho qua.
                if record.contract_id != contract and contract.state == "done":
                    raise UserError("Không thể chuyển phiếu vào hợp đồng đã hoàn tất.")

        for charge in self:  # Lần lượt kiểm tra từng khoản phụ phí.

            # contract_id là hợp đồng liên kết với khoản phụ phí.
            # done là giá trị kỹ thuật của trạng thái Hoàn tất.
            if charge.contract_id.state == "done":

                # Duyệt dictionary bằng vòng for sẽ lấy từng tên trường.
                # Ví dụ vals = {"unit_price": 500000, "note": "Ghi chú mới"}
                # thì field_name lần lượt là "unit_price" và "note".
                for field_name in vals:

                    # note là trường Ghi chú.
                    # != nghĩa là "khác": chỉ cần có trường khác ghi chú
                    # thì chặn toàn bộ lần lưu này.
                    if field_name != "note":
                        # raise UserError dừng thao tác trước khi lưu và hiện thông báo cho nhân viên.
                        raise UserError(
                            "Hợp đồng đã hoàn tất. "
                            "Khoản phụ phí chỉ được chỉnh sửa ghi chú."
                        )

        # super() gọi cách lưu sẵn có của Odoo.
        # Chỉ lưu khi tất cả khoản phụ phí đều vượt qua kiểm tra.
        return super().write(vals)

    def unlink(self):  # Không cho xóa phụ phí thuộc hợp đồng đã hoàn tất.
        # unlink là hàm Odoo gọi khi người dùng hoặc code yêu cầu xóa bản ghi.
        # Phải kiểm tra cả thao tác xóa một khoản và xóa nhiều khoản cùng lúc.

        for charge in self:
            if charge.contract_id.state == "done":
                # raise UserError dừng trước khi xóa và hiện thông báo.
                raise UserError(
                    "Không thể xóa khoản phụ phí của hợp đồng đã hoàn tất."
                )

        # Chỉ thực hiện xóa nếu không có khoản nào thuộc hợp đồng hoàn tất.
        # Các quyền xóa và kiểm tra sẵn có của Odoo vẫn được áp dụng.
        return super().unlink()

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

    def action_create_invoice(self):  # Chặn tạo hóa đơn riêng cho phụ phí.
        # Giữ hàm để các nơi còn gọi nút cũ cũng bị chặn.
        # UserError dừng thao tác và hiện hướng dẫn cho nhân viên.
        raise UserError(
            "Phụ phí phải được gộp vào hóa đơn cuối hợp đồng. "
            "Vui lòng tạo hóa đơn và chọn hợp đồng tương ứng."
        )
