# 1. Đầu file: Các dòng import
from odoo import api, fields, models
from odoo.exceptions import UserError


# 2. Khai báo Class và các thuộc tính Model ( _name , _description ...)
class RentalContract(models.Model):
    _inherit = "rental.contract"

    # 3. Khai báo các trường dữ liệu ( fields )
    charge_ids = fields.One2many(
        "motorbike.rental.charge",
        "contract_id",
        string="Các khoản phụ phí",
    )
    payment_ids = fields.One2many(
        "motorbike.rental.payment",
        "contract_id",
        string="Lịch sử thanh toán",
    )
    invoice_ids = fields.One2many(
        "account.move",
        "contract_id",
        string="Hóa đơn",
    )
    settlement_status = fields.Selection(
        selection=[
            ("unsettled", "Chưa quyết toán"),
            ("settled", "Đã quyết toán"),
        ],
        string="Trạng thái quyết toán",
        default="unsettled",
        readonly=True,
        copy=False,
    )

    total_penalty_amount = fields.Monetary(
        string="Tổng phụ phí (Đã duyệt)",
        currency_field="currency_id",
        compute="_compute_settlement_preview",
        store=True,
    )
    settlement_balance = fields.Monetary(
        string="Chênh lệch quyết toán",
        currency_field="currency_id",
        compute="_compute_settlement_preview",
        store=True,
        help="Dương (+): Khách cần trả thêm | Âm (-): Hoàn tiền thừa cho khách | 0: Vừa đủ",
    )

    # 4. Các hàm Constraints ( @api.constrains , _sql_constraints )

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )
    @api.depends("total_amount", "deposit_amount", "charge_ids.state", "charge_ids.amount")
    def _compute_settlement_preview(self):
        """Tính trước tổng phạt và số dư quyết toán để hiển thị trên Form Hợp đồng."""
        for contract in self:
            rent_fee = contract.total_amount or 0.0
            penalties = sum(
                contract.charge_ids.filtered(lambda c: c.state == "confirmed").mapped("amount")
            )
            deposit = contract.deposit_amount or 0.0
            contract.total_penalty_amount = penalties
            contract.settlement_balance = (rent_fee + penalties) - deposit

    # 6. Các hàm Action / Nghiệp vụ (nút bấm button)
    def action_settlement(self):
        self.ensure_one()

        # 1. Chốt chặn trạng thái hợp đồng nháp hoặc hủy
        if self.state in ("draft", "cancelled"):
            raise UserError("Không thể quyết toán hợp đồng đang ở trạng thái Nháp hoặc Đã hủy!")

        if self.settlement_status == "settled":
            raise UserError("Hợp đồng này đã được quyết toán rồi!")

        draft_charges = self.charge_ids.filtered(lambda c: c.state == "draft")
        if draft_charges:
            raise UserError(
                "Vẫn còn khoản phụ phí/phạt đang ở trạng thái Nháp. "
                "Vui lòng xác nhận hoặc hủy các khoản phí này trước khi quyết toán!"
            )

        # 2. Tính toán số tiền: (Tiền xe + Phạt đã xác nhận) - Cọc
        rent_fee = self.total_amount or 0.0
        penalties = sum(self.charge_ids.filtered(lambda c: c.state == "confirmed").mapped("amount"))
        deposit = self.deposit_amount or 0.0
        balance = (rent_fee + penalties) - deposit

        # 3. Lấy đơn vị tiền tệ an toàn (fallback về tiền tệ công ty)
        currency = self.currency_id or self.env.company.currency_id

        # Đánh dấu hợp đồng đã quyết toán
        self.settlement_status = "settled"

        # 4. Xử lý khi số dư bằng 0
        if currency.is_zero(balance):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Quyết toán hoàn tất",
                    "message": "Đã cấn trừ vừa đủ giữa tiền thuê và tiền cọc, không cần thu thêm hay hoàn tiền.",
                    "type": "success",
                    "sticky": False,
                    "next": {"type": "ir.actions.client", "tag": "reload"},
                },
            }

        # 5. Phân nhánh tạo phiếu Hoàn tiền (balance < 0) hoặc Thu thêm (balance > 0)
        tx_type = "refund" if balance < 0 else "additional_payment"
        payment = self.env["motorbike.rental.payment"].create({
            "customer_id": self.customer_id.id,
            "contract_id": self.id,
            "transaction_type": tx_type,
            "amount": abs(balance),
            "currency_id": currency.id,
            "payment_method": "cash",
            "payment_date": fields.Date.context_today(self),
        })

        return {
            "name": "Phiếu thanh toán quyết toán",
            "type": "ir.actions.act_window",
            "res_model": "motorbike.rental.payment",
            "res_id": payment.id,
            "view_mode": "form",
            "target": "current",
        }