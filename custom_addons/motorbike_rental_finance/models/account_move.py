# 1. Đầu file: Các dòng import
import math

from odoo import api, fields, models, Command
from odoo.exceptions import UserError  # UserError: dừng thao tác và hiện thông báo dễ đọc cho người dùng.
from .rental_payment import _INVOICE_SETTLEMENT  # Lấy dấu riêng để hóa đơn tự tạo phiếu thu/hoàn.


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
    rental_charges_ids = fields.One2many(
        "motorbike.rental.charge",
        "invoice_id",
        string="Khoản phí",
    )

    # Tiền đã nhận ban đầu lấy từ phiếu cọc và phiếu thuê thực tế đã xác nhận.
    rental_received_amount = fields.Monetary(
        string="Tiền đã nhận",
        compute="_compute_rental_received_amount",  # Odoo tự tính, người dùng không nhập tay.
        currency_field="currency_id",  # Hiển thị theo đồng tiền của hóa đơn.
    )

    
    
    """Tính tiền cọc và tiền thuê ban đầu đã xác nhận để hiển thị trên hóa đơn."""
    
    @api.depends(
        "contract_id", "contract_id.customer_id", "currency_id",
        "contract_id.payment_ids", "contract_id.payment_ids.state",
        "contract_id.payment_ids.amount", "contract_id.payment_ids.transaction_type",
        "contract_id.payment_ids.customer_id", "contract_id.payment_ids.currency_id",
    )
    def _compute_rental_received_amount(self):  # Cộng cọc và tiền thuê ban đầu đã thực thu của hợp đồng.
        for move in self:  # Một lần tính có thể xử lý nhiều hóa đơn.
            contract = move.contract_id  # Lấy hợp đồng được chọn trên hóa đơn.
            # Chỉ lấy phiếu đã xác nhận, đúng khách và đồng tiền; bỏ phiếu nháp, hủy, thu thêm và hoàn tiền.
            payments = contract.payment_ids.filtered(
                lambda payment: payment.state == "confirmed"
                and payment.transaction_type in ("deposit", "rental_payment")
                and payment.customer_id == contract.customer_id
                and payment.currency_id == move.currency_id
            ) if contract else self.env["motorbike.rental.payment"]
            move.rental_received_amount = sum(payments.mapped("amount"))  # Cộng số tiền trên các phiếu hợp lệ.





    # Monetary là kiểu trường lưu/hiển thị số tiền trong Odoo.
    # string là nhãn tiếng Việt trên giao diện; tên biến tiếng Anh là tên kỹ thuật trong code.
    # compute chỉ định tên hàm tính giá trị, nên nhân viên không phải nhập số tiền này.
    # currency_field chỉ ra trường chứa đồng tiền để Odoo hiển thị và làm tròn tiền đúng cách.
    rental_balance = fields.Monetary(
        string="Chênh lệch quyết toán",  # balance = số dư: dương thì thu thêm, âm thì hoàn khách.
        compute="_compute_rental_settlement",  # settlement = quyết toán; gọi hàm tính ở bên dưới.
        currency_field="currency_id",  # Dùng đồng tiền đang chọn trên hóa đơn.
    )
    rental_settlement_amount = fields.Monetary(
        string="Số tiền thu/hoàn",  # amount = số tiền; trường này luôn hiển thị số không âm.
        compute="_compute_rental_settlement",  # Cùng hàm tính với rental_balance để hai số luôn khớp.
        currency_field="currency_id",
    )

    # at_post nghĩa là "tại lúc xác nhận hóa đơn". Đây là số tiền đã chốt để lưu lại lịch sử.
    # Sau khi ghi phiếu hoàn, số dư hợp đồng sẽ về 0 nhưng số đã chốt trên hóa đơn không đổi.
    rental_balance_at_post = fields.Monetary(
        string="Chênh lệch đã chốt",
        currency_field="currency_id",
        readonly=True,  # readonly: người dùng chỉ được xem; hàm xử lý vẫn ghi được giá trị bằng code.
        copy=False,  # copy=False: sao chép hóa đơn không mang theo số tiền đã chốt của hóa đơn cũ.
    )
    rental_money_confirmed = fields.Boolean(
        string="Đã xác nhận thu/hoàn tiền",
        copy=False,  # Boolean là ô tích True/False; hóa đơn sao chép phải được xác nhận tiền lại.
    )
    rental_payment_method = fields.Selection(
        # Selection là danh sách lựa chọn; mỗi cặp gồm (giá trị lưu trong dữ liệu, nhãn hiển thị).
        selection=[
            ("cash", "Tiền mặt"),
            ("bank_transfer", "Chuyển khoản ngân hàng"),
            ("credit_card", "Thẻ tín dụng"),
        ],
        string="Phương thức thu/hoàn",
        default="cash",  # default là giá trị mặc định; nhân viên có thể chọn lại trước khi xác nhận.
        copy=False,  # Không tự dùng lại phương thức của hóa đơn được sao chép.
    )



    # 4. Các hàm Constraints ( @api.constrains , _sql_constraints )
    """
    hàm kiểm tra đã xác nhận thu hồi hết xe của các hợp đồng liên quan đến hóa đơn chưa.
    Nếu chưa đủ thì báo lỗi, chặn thao tác đang thực hiện.
    """
    @api.model
    def _check_returned_before_invoice(self, contracts):  # Kiểm tra hợp đồng thu đủ xe chưa trước khi lập hóa đơn
        for contract in contracts:
            # Một hợp đồng có thể có nhiều phiếu; phải xét tất cả phiếu
            # liên quan, không chỉ lấy phiếu đầu tiên hoặc phiếu đã xong.
            tickets = self.env['rental.operation.ticket'].search([
                ('contract_id', '=', contract.id),
            ])
            operation_lines = tickets.mapped('vehicle_detail_ids')

            # Đối chiếu danh sách xe thực tế: một phiếu đã trả hết xe của
            # riêng nó vẫn chưa đủ nếu còn xe hợp đồng chưa có dòng vận hành.        
            contract_vehicles = contract.line_ids.mapped('vehicle_id')
            operation_vehicles = operation_lines.mapped('vehicle_id')
            missing_vehicles = contract_vehicles - operation_vehicles

            # Không cho qua trường hợp danh sách rỗng. Với các dòng đã có,
            # chỉ 'returned' là xác nhận thu hồi; waiting/delivering/renting
            # đều còn thiếu bước nhận trả. Không suy ra đã trả từ trạng thái
            # Fleet, vì xe trả về vẫn có thể đang pending_inspection.
            if (
                not contract_vehicles
                or not operation_lines
                or missing_vehicles
                or any(line.status != 'returned' for line in operation_lines)
            ):
                raise UserError(
                    'Chưa thể lập hóa đơn cho hợp đồng %s. '
                    'Cần xác nhận thu hồi đầy đủ các xe trước.'
                    % contract.name
                )


    @api.model
    def _create_rental_invoice_after_return(self, contracts):
        """Tạo hóa đơn nháp sau thu hồi đủ xe, bỏ qua hợp đồng đã có hóa đơn chưa hủy.

        Hóa đơn gồm tiền thuê và phụ phí đã duyệt chưa nằm trên hóa đơn hiệu lực.
        Giữ quyền hệ thống cho việc tự tạo nháp; kế toán xác nhận theo quyền của mình.
        """
        for contract in contracts:
            contract = contract.sudo()
            if contract.invoice_ids.filtered(
                lambda invoice: invoice.move_type == "out_invoice" and invoice.state != "cancel"
            ):
                continue
            self._check_returned_before_invoice(contract)
            charges = contract.charge_ids.filtered(
                lambda charge: charge.state == "confirmed"
                and (not charge.invoice_id or charge.invoice_id.state == "cancel")
            )
            lines = [Command.create({
                "name": f"Tiền thuê - {contract.name}",
                "quantity": 1,
                "price_unit": contract.total_amount,
            })]
            lines += [Command.create({
                "name": f"Phụ phí: {charge.name}",
                "quantity": charge.quantity,
                "price_unit": charge.unit_price,
                "charge_id": charge.id,
            }) for charge in charges]
            self.sudo().create({
                "move_type": "out_invoice",
                "contract_id": contract.id,
                "partner_id": contract.customer_id.id,
                "currency_id": contract.currency_id.id,
                "invoice_date": fields.Date.context_today(self),
                "invoice_line_ids": lines,
                "rental_charges_ids": [Command.set(charges.ids)],
            })



        """
        Hàm này tìm các hợp đồng liên quan đến hóa đơn, 
        rồi gọi hàm kiểm tra thu hồi đủ xe phía trên.
        """
    def _check_rental_return_before_invoice(self):  # Tìm các hợp đồng của hóa đơn và kiểm tra đã thu hồi đủ xe.
        for move in self.filtered(lambda record: record.move_type == 'out_invoice'):
            # Dùng phép hợp recordset (|) để không kiểm tra trùng hợp đồng.
            # Phải xét Charge trên dòng hóa đơn và liên kết ngược vì đường
            # tạo hóa đơn từ Charge hiện chủ động để contract_id=False.
            contracts = (
                move.contract_id
                | move.invoice_line_ids.mapped('charge_id.contract_id')
                | move.rental_charges_ids.mapped('contract_id')
            )
            self._check_returned_before_invoice(contracts)




        """
        khi tạo hoặc cập nhật hóa đơn có các trường được liệt kê, 
        hãy tự chạy hàm kiểm tra ngay bên dưới.
        vd: Khi tạo hóa đơn nháp thì tự chạy kiểm tra, chưa thu hết xe thì đéo cho tạo
        """
    @api.constrains(
        'contract_id', 'move_type', 'invoice_line_ids', 'rental_charges_ids'
    )
    def _check_rental_invoice_return(self):  # Chặn lưu hóa đơn thuê xe nếu các hợp đồng liên quan chưa thu hồi đủ xe.
        self._check_rental_return_before_invoice()






        """
        Hàm này bảo vệ hóa đơn khách hàng đã xác nhận và gắn với hợp đồng đã hoàn tất:

        Không cho hủy hoặc đưa hóa đơn về Nháp.
        Không cho gỡ hay đổi hợp đồng liên kết.
        Không cho đổi loại hóa đơn.
        Mục đích là giữ nguyên hóa đơn đã dùng để kết thúc hợp đồng, tránh thay đổi làm sai dữ liệu đã chốt.
        Các cập nhật khác vẫn theo quy tắc của Odoo
        """
    def write(self, vals):  # Chặn hủy hoặc đưa về nháp hóa đơn đã xác nhận của hợp đồng hoàn tất.
        # write là hàm Odoo gọi khi lưu thay đổi vào bản ghi đã tồn tại.
        # self là tập hóa đơn đang được sửa, có thể gồm nhiều hóa đơn.
        #
        # vals là dictionary: tập tên trường và giá trị mới muốn lưu.
        # Ví dụ:
        # {"state": "draft"}  nghĩa là muốn đưa hóa đơn về nháp.
        # {"state": "cancel"} nghĩa là muốn hủy hóa đơn.

        for move in self:  # Lần lượt kiểm tra từng hóa đơn đang được sửa.

            # Chỉ khóa khi đồng thời thỏa cả ba điều kiện:
            # 1. out_invoice: hóa đơn bán hàng cho khách.
            # 2. posted: hóa đơn đã được xác nhận.
            # 3. done: hợp đồng liên kết đã hoàn tất.
            # Nếu chưa chọn hợp đồng thì điều kiện cuối không thỏa,
            # nên hóa đơn thông thường không bị áp dụng quy tắc này.
            is_closed_rental_invoice = (
                move.move_type == "out_invoice"
                and move.state == "posted"
                and move.contract_id.state == "done"
            )

            # continue bỏ qua hóa đơn không thuộc trường hợp cần khóa,
            # rồi chuyển sang kiểm tra hóa đơn tiếp theo.
            if not is_closed_rental_invoice:
                continue

            # get("state") lấy trạng thái mới mà thao tác đang yêu cầu.
            # Nếu không sửa trạng thái thì get trả về None.
            #
            # in kiểm tra giá trị có nằm trong nhóm cho trước không:
            # draft là Nháp; cancel là Đã hủy.
            if vals.get("state") in ("draft", "cancel"):
                # raise UserError dừng thao tác trước khi lưu
                # và hiện thông báo rõ ràng cho nhân viên.
                raise UserError(
                    "Hóa đơn này đã được xác nhận để kết thúc hợp đồng. "
                    "Không thể hủy hoặc đưa hóa đơn về nháp."
                )

            # Không cho gỡ hoặc đổi hợp đồng của hóa đơn đã chốt.
            # Nếu cho gỡ liên kết trước, người dùng có thể bỏ hợp đồng
            # rồi thực hiện hủy ở lần lưu sau để vượt điều kiện bên trên.
            #
            # "contract_id" in vals: lần lưu này có yêu cầu sửa hợp đồng.
            # .id là mã số bản ghi hợp đồng hiện tại trong database.
            # != nghĩa là khác: gửi lại cùng hợp đồng thì vẫn được.
            if (
                "contract_id" in vals
                and vals["contract_id"] != move.contract_id.id
            ):
                raise UserError(
                    "Không thể gỡ hoặc đổi hợp đồng trên hóa đơn "
                    "đã dùng để kết thúc hợp đồng."
                )

            # Giữ nguyên loại hóa đơn để không thể đổi sang loại khác,
            # rồi dùng loại mới để né quy tắc khóa ở lần lưu tiếp theo.
            if (
                "move_type" in vals
                and vals["move_type"] != move.move_type
            ):
                raise UserError(
                    "Không thể đổi loại hóa đơn đã dùng để kết thúc hợp đồng."
                )

        # super() gọi hàm lưu sẵn có của Odoo.
        # Chỉ chạy sau khi tất cả hóa đơn đều vượt qua kiểm tra.
        # Các điều kiện và quyền sửa khác của Odoo vẫn được giữ nguyên.
        return super().write(vals)





    """
    Xác nhận hóa đơn và quyết toán hợp đồng:
    - Kiểm tra đã thu hồi đủ xe, hợp đồng đang thuê, đúng khách và đồng tiền.
    - Không xác nhận nhiều hóa đơn kết thúc cho cùng hợp đồng trong một lần.
    - Không còn phụ phí nháp; tổng hóa đơn bằng tiền thuê cộng phụ phí đã duyệt.
    - Nếu số dư khác 0, yêu cầu xác nhận đã thu/hoàn tiền và chọn phương thức.
    - Xác nhận hóa đơn, lưu số dư đã chốt, tạo phiếu thu/hoàn nếu cần,
    rồi đánh dấu đã quyết toán và hoàn tất hợp đồng.
    """
    
    def action_post(self):
        """Xác nhận hóa đơn, ghi phiếu thu hoặc hoàn và đóng hợp đồng thuê."""
        # 1. Kiểm tra đã trả đủ xe, kể cả hóa đơn liên kết qua phụ phí.
        self._check_rental_return_before_invoice()
        rental_invoices = self.filtered(
            lambda move: move.move_type == "out_invoice" and move.contract_id and move.state == "draft"
        )
        if len(rental_invoices.mapped("contract_id")) != len(rental_invoices):
            raise UserError("Mỗi hợp đồng chỉ được xác nhận một hóa đơn kết thúc.")

        # 2. Kiểm tra từng hóa đơn và giữ số dư trước khi ghi phiếu làm số dư về 0.
        settlements = [(move, move._check_rental_settlement_before_post()) for move in rental_invoices]

        # 3. Để Odoo xác nhận và đánh số hóa đơn theo quy trình gốc.
        result = super().action_post()

        # 4. Ghi phiếu thu hoặc hoàn rồi mới đóng từng hợp đồng.
        for move, balance in settlements:
            move._finish_rental_settlement(balance)
        return result



    
    
    
    

    """
    Kiểm tra trước khi xác nhận hóa đơn:
    - Hợp đồng đang thuê; khách hàng và đồng tiền khớp hợp đồng.
    - Không còn phụ phí nháp; tổng hóa đơn bằng tiền thuê cộng phụ phí đã duyệt.
    - Nếu số dư khác 0, phải xác nhận đã thu/hoàn tiền và chọn phương thức.
    Không đạt thì báo lỗi; đạt thì trả về số dư để xử lý thu thêm hoặc hoàn khách.
"""

    def _check_rental_settlement_before_post(self):
        """Kiểm tra điều kiện quyết toán và trả về số cần thu hoặc hoàn trên hợp đồng."""
        contract = self.contract_id
        currency = contract.currency_id
        if contract.state != "in_progress":
            raise UserError("Chỉ được kết thúc hợp đồng đang thuê.")
        if self.partner_id != contract.customer_id or self.currency_id != currency:
            raise UserError("Khách hàng và tiền tệ trên hóa đơn phải khớp hợp đồng.")
        if contract.charge_ids.filtered(lambda charge: charge.state == "draft"):
            raise UserError("Vui lòng xác nhận hoặc hủy phụ phí nháp trước.")

        penalties, balance = self._get_rental_settlement_totals(contract)
        expected_total = contract.total_amount + penalties
        if not currency.is_zero(self.amount_total - expected_total):
            raise UserError("Tổng hóa đơn phải bằng tiền thuê và phụ phí đã duyệt.")

        # Dương là còn thiếu, âm là còn dư, bằng 0 thì không cần xác nhận thu/hoàn.
        if not currency.is_zero(balance):
            if not self.rental_money_confirmed:
                raise UserError("Vui lòng xác nhận đã thu thêm hoặc hoàn đủ tiền cho khách.")
            if not self.rental_payment_method:
                raise UserError("Vui lòng chọn phương thức thu/hoàn.")
        return balance




    
    """
    Hoàn tất quyết toán sau khi xác nhận hóa đơn:
    - Lưu số dư đã chốt để giữ lịch sử thu/hoàn trên hóa đơn.
    - Số dư dương: tạo phiếu thu thêm; âm: tạo phiếu hoàn; bằng 0: không tạo phiếu.
    - Phiếu được xác nhận ngay, gắn đúng khách, hợp đồng, hóa đơn và phương thức thu/hoàn.
    - Đánh dấu đã quyết toán và chuyển hợp đồng sang Hoàn tất.
    """

    def _finish_rental_settlement(self, balance):
        """Lưu số tiền đã chốt, ghi phiếu tiền và hoàn tất hợp đồng."""
        contract = self.contract_id
        # Hóa đơn giữ số đã chốt để xem lại sau khi số dư hợp đồng về 0.
        self.rental_balance_at_post = balance

        if not contract.currency_id.is_zero(balance):
            # Dấu nội bộ cho phép luồng hóa đơn ghi phiếu theo quyền Finance của người dùng.
            self.env["motorbike.rental.payment"].with_context(
                _invoice_settlement=_INVOICE_SETTLEMENT
            ).create({
                "customer_id": contract.customer_id.id,
                "contract_id": contract.id,
                "invoice_id": self.id,
                "transaction_type": "additional_payment" if balance > 0 else "refund",
                "amount": abs(balance),
                "currency_id": contract.currency_id.id,
                "payment_method": self.rental_payment_method,
                "state": "confirmed",
                "note": "Thu/hoàn tiền khi xác nhận hóa đơn %s." % self.name,
            })

        # Hợp đồng kiểm tra lại hóa đơn và số dư trước khi chuyển sang Hoàn tất.
        contract.settlement_status = "settled"
        contract.action_done()

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )
    # @api.depends là decorator (dòng khai báo bổ sung cho hàm bên dưới).
    # Nó báo cho Odoo biết những trường nào thay đổi thì phải tính lại các trường compute.
    

    @api.model
    def _get_rental_settlement_totals(self, contract):
        """Tính phụ phí đã duyệt và số dư thu/hoàn từ dữ liệu gốc của hợp đồng.

        Số dư = Tiền thuê + Phụ phí - (Cọc + Thuê đã thu + Thu thêm - Đã hoàn).
        Chỉ tính phiếu hợp lệ đã xác nhận; dương là thu thêm, âm là hoàn khách.
        Không tạo phiếu tiền và không cần có hóa đơn đã lưu để tính.
        """
        if not contract:
            return 0.0, 0.0
        contract.ensure_one()
        payments = contract.payment_ids.filtered(
            lambda payment: (
                payment.state == "confirmed"
                and payment.customer_id == contract.customer_id
                and payment.currency_id == contract.currency_id
                and math.isfinite(payment.amount)
                and payment.amount > 0
            )
        )
        received = sum(payments.filtered(
            lambda payment: payment.transaction_type in (
                "deposit", "rental_payment", "additional_payment",
            )
        ).mapped("amount"))
        refunded = sum(payments.filtered(
            lambda payment: payment.transaction_type == "refund"
        ).mapped("amount"))
        penalties = sum(contract.charge_ids.filtered(
            lambda charge: charge.state == "confirmed"
        ).mapped("amount"))
        balance = contract.currency_id.round(
            contract.total_amount + penalties - (received - refunded)
        )
        return penalties, balance





    """Hiển thị tiền cần thu/hoàn khi hóa đơn nháp;
    sau xác nhận giữ nguyên số tiền đã chốt để xem lại lịch sử."""

    @api.depends(
        "contract_id", "contract_id.total_amount", "contract_id.customer_id",
        "contract_id.currency_id", "contract_id.currency_id.rounding",
        "contract_id.charge_ids", "contract_id.charge_ids.state",
        "contract_id.charge_ids.amount", "contract_id.payment_ids",
        "contract_id.payment_ids.state", "contract_id.payment_ids.amount",
        "contract_id.payment_ids.transaction_type",
        "contract_id.payment_ids.customer_id", "contract_id.payment_ids.currency_id",
        "state",  # Chuyển khỏi nháp thì chuyển sang hiển thị con số đã chốt.
        "rental_balance_at_post",  # Ghi số đã chốt thì cập nhật ngay số tiền đang hiển thị.
    )
    def _compute_rental_settlement(self):  # Tính số thu/hoàn hiện tại khi hóa đơn nháp và giữ số đã chốt sau khi xác nhận.
        for move in self:  # self có thể chứa nhiều hóa đơn; phải gán đủ giá trị cho từng hóa đơn.
            if move.state == "draft":  # == là phép so sánh bằng, khác với dấu = dùng để gán giá trị.
                # Tính trực tiếp từ dữ liệu gốc; chưa chọn hợp đồng thì trả về 0.
                _, balance = move._get_rental_settlement_totals(move.contract_id)
            else:  # else là nhánh còn lại: hóa đơn không còn ở trạng thái nháp.
                balance = move.rental_balance_at_post  # Đọc số đã chốt, không đọc số dư hợp đồng lúc này.

            move.rental_balance = balance  # Giữ dấu âm/dương để XML quyết định hiện phần thu hay phần hoàn.
            move.rental_settlement_amount = abs(balance)  # abs(-1.700.000) = 1.700.000, dễ đọc trên giao diện.




    """
         @api.onchange: chạy khi người dùng đổi thông tin trên form, 
        để tự điền hoặc điều chỉnh dữ liệu trước khi lưu.
            
        Hàm này tự bỏ tích “Đã xác nhận thu/hoàn tiền” khi thông tin hóa đơn 
        Nháp thay đổi, như khách hàng, dòng hóa đơn, số dư hoặc phương thức thanh toán.
            
        Mục đích là buộc nhân viên kiểm tra và tích xác nhận lại theo thông tin mới, tránh giữ xác nhận cũ.
    """


    @api.onchange(
        "contract_id", "partner_id", "currency_id",
        "invoice_date", "invoice_date_due", "invoice_payment_term_id",
        "invoice_line_ids", "journal_id", "ref", "narration",
        "rental_payment_method", "rental_balance",
    )
    def _onchange_reset_money_confirmation(self):  # Bỏ tích xác nhận tiền khi thông tin hóa đơn thay đổi.
        if self.state == "draft":  # Chỉ áp dụng khi hóa đơn còn nháp.
            self.rental_money_confirmed = False  # False là bỏ tích.





        """
        Khi chọn hoặc đổi hợp đồng, hàm tự điền khách hàng, đồng tiền và thay các dòng hóa đơn bằng tiền thuê cùng phụ phí đã xác nhận.
        Phụ phí thuộc hóa đơn chưa hủy sẽ được bỏ qua để tránh tính trùng.
        Nếu bỏ chọn hợp đồng, hàm xóa các dòng hóa đơn và liên kết phụ phí, nhưng vẫn giữ khách hàng và đồng tiền
        """

    @api.onchange("contract_id")
    def _onchange_contract_id(self):
        # Nếu bỏ chọn hợp đồng -> Xóa các dòng chi tiết và liên kết phụ phí
        if not self.contract_id:
            self.invoice_line_ids = [Command.clear()]
            self.rental_charges_ids = [Command.clear()]
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
        # Gắn liên kết ngược để cập nhật charge.invoice_id, chống xuất hóa đơn trùng
        self.rental_charges_ids = [Command.set(confirmed_charges.ids)]

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

    
    
    
    
    
    """
    Đoạn này kiểm tra đã thu hồi đủ xe khi lưu dòng hóa đơn có phụ phí.

    Ví dụ: hợp đồng thuê 3 xe, mới trả 2 xe. Khi đưa phụ phí của hợp đồng vào hóa đơn và lưu, hệ thống báo lỗi;
    phải xác nhận thu hồi xe còn lại mới lưu được.
    """
    @api.constrains('charge_id', 'move_id')
    def _check_rental_return_before_invoice_line(self):  # Kiểm tra hóa đơn cha khi một dòng được gắn Charge hoặc chuyển sang hóa đơn khác.
        self.mapped('move_id')._check_rental_return_before_invoice()




        """
        Hàm này tự điền thông tin vào dòng hóa đơn khi chọn phụ phí, gồm: 
        tên, số lượng, đơn giá và danh mục giá lấy từ phụ phí đó.

        Ví dụ chọn phí “Hỏng gương”, số lượng 1, đơn giá 200.000 đồng → dòng hóa đơn tự nhận các thông tin tương ứng.
        """
    @api.onchange("charge_id")
    def _onchange_charge_id(self):
        if self.charge_id:
            self.name = f"Phụ phí: {self.charge_id.name}"
            self.quantity = self.charge_id.quantity
            self.price_unit = self.charge_id.unit_price
            self.price_catalog_id = self.charge_id.price_catalog_id




        """
        Hàm này tự điền tên và đơn giá vào dòng hóa đơn khi chọn danh mục giá, 
        nhưng chỉ khi dòng đó chưa liên kết với phụ phí.

        Nếu đã chọn phụ phí thì không ghi đè, để giữ thông tin lấy từ phụ phí đó.
        """
    @api.onchange("price_catalog_id")
    def _onchange_price_catalog_id(self):
        if self.price_catalog_id and not self.charge_id:
            self.name = self.price_catalog_id.name
            self.price_unit = self.price_catalog_id.unit_price
