# 1. Đầu file: Các dòng import
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

    def _check_rental_return_before_invoice(self):  # Tìm các hợp đồng của hóa đơn và kiểm tra đã thu hồi đủ xe.
        """Kiểm tra cả hóa đơn chọn hợp đồng và hóa đơn tạo từ phụ phí.

        Chỉ áp dụng cho hóa đơn khách hàng (out_invoice). Hóa đơn thông
        thường không liên quan hợp đồng/Charge thuê xe có tập hợp đồng rỗng
        nên không bị áp dụng điều kiện thu hồi của phân hệ thuê xe.
        """
        for move in self.filtered(lambda record: record.move_type == 'out_invoice'):
            # Dùng phép hợp recordset (|) để không kiểm tra trùng hợp đồng.
            # Phải xét Charge trên dòng hóa đơn và liên kết ngược vì đường
            # tạo hóa đơn từ Charge hiện chủ động để contract_id=False.
            contracts = (
                move.contract_id
                | move.invoice_line_ids.mapped('charge_id.contract_id')
                | move.rental_charges_ids.mapped('contract_id')
            )
            contracts._check_returned_before_invoice()

    # Constraint chạy ở server khi tạo/lưu hoặc thay liên kết nghiệp vụ;
    # không chỉ dựa vào onchange hay điều kiện ẩn nút trên giao diện.
    @api.constrains(
        'contract_id', 'move_type', 'invoice_line_ids', 'rental_charges_ids'
    )
    def _check_rental_invoice_return(self):  # Chặn lưu hóa đơn thuê xe nếu các hợp đồng liên quan chưa thu hồi đủ xe.
        self._check_rental_return_before_invoice()

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
            #
            # and nghĩa là "và": phải thỏa tất cả điều kiện.
            # Nếu chưa chọn hợp đồng thì điều kiện cuối không thỏa,
            # nên hóa đơn thông thường không bị áp dụng quy tắc này.
            is_closed_rental_invoice = (
                move.move_type == "out_invoice"
                and move.state == "posted"
                and move.contract_id.state == "done"
            )

            # not nghĩa là phủ định điều kiện.
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

    def action_post(self):  # Xác nhận hóa đơn, tự ghi phiếu thu thêm/hoàn tiền và đóng hợp đồng khi đủ điều kiện.
        """Gom việc kết thúc thuê xe vào một lần bấm Xác nhận hóa đơn.

        self là tập hóa đơn Odoo đang xử lý, có thể gồm một hoặc nhiều hóa đơn.
        move là biến đại diện cho một hóa đơn; contract là hợp đồng của hóa đơn đó.
        Trình tự: kiểm tra -> xác nhận hóa đơn -> ghi tiền -> đóng hợp đồng.
        Các bước dùng chung một giao dịch database (transaction). Nếu một bước
        phát sinh lỗi và lỗi được trả về cho người dùng, Odoo hoàn tác các thay đổi
        trong giao dịch; không giữ một hóa đơn xác nhận dở hoặc phiếu tiền tạo dở.
        """
        # Dấu chấm gọi hàm của đối tượng self. Dùng lại kiểm tra thu hồi đủ xe đã có,
        # bao gồm cả hóa đơn liên kết gián tiếp với hợp đồng thông qua phụ phí.
        self._check_rental_return_before_invoice()

        # filtered giữ lại những bản ghi thỏa điều kiện; không tạo/xóa hóa đơn trong database.
        # lambda move: ... là hàm ngắn nhận một hóa đơn và trả về True (giữ) hoặc False (bỏ qua).
        # and nghĩa là "và": phải thỏa cả ba điều kiện thì mới kết thúc hợp đồng ở đây.
        rental_invoices = self.filtered(
            lambda move: (
                move.move_type == "out_invoice"  # out_invoice = hóa đơn bán hàng cho khách.
                and move.contract_id  # Phải có chọn hợp đồng; hóa đơn riêng từ phụ phí không tự đóng hợp đồng.
                and move.state == "draft"  # draft = nháp; chỉ chốt tiền khi hóa đơn đang chờ xác nhận.
            )
        )

        # mapped("contract_id") lấy tập hợp đồng và tự loại bản ghi trùng; len đếm số bản ghi.
        # Nếu số hợp đồng ít hơn số hóa đơn thì có hai hóa đơn cùng kết thúc một hợp đồng.
        if len(rental_invoices.mapped("contract_id")) != len(rental_invoices):
            raise UserError("Mỗi hợp đồng chỉ được xác nhận một hóa đơn kết thúc.")

        # [] là danh sách Python rỗng. Ta sẽ lưu từng cặp (hóa đơn, số dư trước khi ghi tiền).
        # Cần giữ số dư cũ vì phiếu thu/hoàn tạo ở bước sau sẽ làm số dư hợp đồng về 0.
        settlements = []

        for move in rental_invoices:  # for ... in ...: lần lượt xử lý từng hóa đơn trong tập đã lọc.
            contract = move.contract_id  # Lấy đối tượng hợp đồng, không chỉ mã số id của nó.
            currency = contract.currency_id  # currency = đồng tiền; dùng để so sánh số tiền đúng độ làm tròn.

            # != nghĩa là "khác"; in_progress là giá trị kỹ thuật của trạng thái "Đang thuê".
            # Điều kiện này cũng ngăn xác nhận thêm một hóa đơn kết thúc sau khi hợp đồng đã đóng.
            if contract.state != "in_progress":
                raise UserError("Chỉ được kết thúc hợp đồng đang thuê.")

            # partner_id là khách hàng trên hóa đơn; customer_id là khách hàng trên hợp đồng.
            # or nghĩa là "hoặc": chỉ cần sai khách hoặc sai đồng tiền là phải dừng thao tác.
            if (
                move.partner_id != contract.customer_id
                or move.currency_id != currency
            ):
                raise UserError("Khách hàng và tiền tệ trên hóa đơn phải khớp hợp đồng.")

            # filtered trả tập rỗng nếu không còn phụ phí nháp; tập có bản ghi được hiểu là True.
            # Phụ phí nháp chưa được chốt nên không thể kết thúc hợp đồng ngay lúc này.
            if contract.charge_ids.filtered(lambda charge: charge.state == "draft"):
                raise UserError("Vui lòng xác nhận hoặc hủy phụ phí nháp trước.")

            # expected_total = tổng tiền dự kiến: tiền thuê cộng toàn bộ phụ phí đã duyệt.
            # amount_total là tổng tiền cuối cùng trên hóa đơn, bao gồm thuế nếu có.
            # Luồng này đang áp dụng tổng hóa đơn = tiền thuê + phụ phí, không thêm khoản thuế/giảm giá riêng.
            expected_total = contract.total_amount + contract.total_penalty_amount
            # is_zero kiểm tra "bằng 0 theo độ làm tròn của tiền tệ", tránh so sánh số thực trực tiếp bằng ==.
            # Nếu hiệu hai tổng không bằng 0 thì hóa đơn bị thiếu/thừa tiền so với hợp đồng.
            if not currency.is_zero(move.amount_total - expected_total):
                raise UserError("Tổng hóa đơn phải bằng tiền thuê và phụ phí đã duyệt.")

            # settlement_balance đã tính cả tiền thuê trả trước, cọc và các khoản thu/hoàn đã xác nhận.
            balance = contract.settlement_balance

            if not currency.is_zero(balance):  # Chỉ yêu cầu xác nhận tiền khi còn chênh lệch cần xử lý.
                if not move.rental_money_confirmed:  # not đảo điều kiện: chưa tích ô xác nhận thì dừng.
                    raise UserError("Vui lòng xác nhận đã thu thêm hoặc hoàn đủ tiền cho khách.")
                if not move.rental_payment_method:  # Phải biết khoản thu/hoàn được xử lý bằng cách nào.
                    raise UserError("Vui lòng chọn phương thức thu/hoàn.")

            # append thêm một phần tử vào danh sách. (move, balance) là tuple, tức một cặp giá trị.
            settlements.append((move, balance))

        # super() gọi cách xác nhận hóa đơn gốc của Odoo và các phần mở rộng kế thừa trước lớp này.
        # Phải giữ bước này để Odoo tạo bút toán, đánh số hóa đơn và kiểm tra quyền/quy tắc kế toán.
        result = super().action_post()  # Lưu kết quả để trả nguyên kết quả đó về giao diện ở cuối hàm.

        # Python tách từng cặp đã lưu thành hai biến move và balance; không đọc lại số dư sau khi ghi tiền.
        for move, balance in settlements:
            contract = move.contract_id  # Lấy lại hợp đồng của hóa đơn vừa được xác nhận.
            # Gán trường Odoo bằng dấu = sẽ ghi giá trị; không chỉ đổi một biến Python trong bộ nhớ.
            move.rental_balance_at_post = balance

            if not contract.currency_id.is_zero(balance):  # Nếu vừa đủ tiền thì không tạo phiếu có số tiền 0.
                # env là môi trường Odoo; env["tên.model"] truy cập đối tượng quản lý dữ liệu của model đó.
                # create({...}) tạo một bản ghi từ dictionary, tức tập các cặp "tên trường": giá trị.
                # Không dùng sudo(): nhân viên phải có quyền Finance để ghi nhận khoản tiền này.
                # with_context truyền dấu nhận diện cho riêng thao tác tự tạo phiếu từ hóa đơn.
                self.env["motorbike.rental.payment"].with_context(
                    _invoice_settlement=_INVOICE_SETTLEMENT
                ).create({
                    "customer_id": contract.customer_id.id,  # .id lấy mã số database của khách hàng.
                    "contract_id": contract.id,  # Liên kết khoản tiền với hợp đồng đang kết thúc.
                    "invoice_id": move.id,  # Liên kết khoản tiền với đúng hóa đơn vừa xác nhận.
                    # Cú pháp A if điều_kiện else B: chọn A nếu đúng, ngược lại chọn B.
                    "transaction_type": (
                        "additional_payment" if balance > 0 else "refund"  # Dương: thu thêm; âm: hoàn khách.
                    ),
                    "amount": abs(balance),  # abs lấy trị tuyệt đối; số tiền trên phiếu luôn dương.
                    "currency_id": contract.currency_id.id,  # Dùng đúng đồng tiền của hợp đồng/hóa đơn.
                    "payment_method": move.rental_payment_method,  # Phương thức nhân viên vừa chọn.
                    "state": "confirmed",  # confirmed = đã xác nhận; nhân viên đã xác nhận tiền ngay trên hóa đơn.
                    "note": "Thu/hoàn tiền khi xác nhận hóa đơn %s." % move.name,  # %s được thay bằng số hóa đơn.
                })

            # Phải ghi nhận khoản tiền trước để số dư hợp đồng về 0, sau đó mới đánh dấu "Đã quyết toán".
            contract.settlement_status = "settled"  # settled = đã quyết toán; không gán khi phiếu tiền còn nháp.
            contract.action_done()  # Gọi hàm kết thúc hợp đồng của Core; vẫn đi qua kiểm tra trong write().

        return result  # Trả kết quả xác nhận gốc để giao diện Odoo tiếp tục xử lý như bình thường.

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )
    # @api.depends là decorator (dòng khai báo bổ sung cho hàm bên dưới).
    # Nó báo cho Odoo biết những trường nào thay đổi thì phải tính lại các trường compute.
    @api.depends(
        "contract_id.settlement_balance",  # Số dư của hợp đồng thay đổi thì hóa đơn nháp phải cập nhật số thu/hoàn.
        "state",  # Chuyển khỏi nháp thì chuyển sang hiển thị con số đã chốt.
        "rental_balance_at_post",  # Ghi số đã chốt thì cập nhật ngay số tiền đang hiển thị.
    )
    def _compute_rental_settlement(self):  # Tính số thu/hoàn hiện tại khi hóa đơn nháp và giữ số đã chốt sau khi xác nhận.
        """Tách số dùng để biết chiều giao dịch và số dùng để nhân viên đọc.

        Ví dụ balance = -1.700.000: cần hoàn khách, amount = 1.700.000.
        Nếu hoàn đủ tiền thì số dư hợp đồng trở về 0. Hóa đơn đã xác nhận
        vẫn đọc số đã chốt để biết lúc đó đã hoàn khách 1.700.000.
        """
        for move in self:  # self có thể chứa nhiều hóa đơn; phải gán đủ giá trị cho từng hóa đơn.
            if move.state == "draft":  # == là phép so sánh bằng, khác với dấu = dùng để gán giá trị.
                # or 0.0 nghĩa là dùng 0 nếu chưa chọn hợp đồng hoặc chưa có giá trị số dư.
                balance = move.contract_id.settlement_balance or 0.0
            else:  # else là nhánh còn lại: hóa đơn không còn ở trạng thái nháp.
                balance = move.rental_balance_at_post  # Đọc số đã chốt, không đọc số dư hợp đồng lúc này.

            move.rental_balance = balance  # Giữ dấu âm/dương để XML quyết định hiện phần thu hay phần hoàn.
            move.rental_settlement_amount = abs(balance)  # abs(-1.700.000) = 1.700.000, dễ đọc trên giao diện.

    # Odoo yêu cầu liệt kê các trường cần lắng nghe trong onchange.
    # Không liệt kê chính ô xác nhận, tránh vừa tích đã bị bỏ tích.
    @api.onchange(
        "contract_id", "partner_id", "currency_id",
        "invoice_date", "invoice_date_due", "invoice_payment_term_id",
        "invoice_line_ids", "journal_id", "ref", "narration",
        "rental_payment_method", "rental_balance",
    )
    def _onchange_reset_money_confirmation(self):  # Bỏ tích xác nhận tiền khi thông tin hóa đơn thay đổi.
        if self.state == "draft":  # Chỉ áp dụng khi hóa đơn còn nháp.
            self.rental_money_confirmed = False  # False là bỏ tích.

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

    # Dòng hóa đơn có thể được thêm/sửa trực tiếp qua ORM/RPC, không đi
    # qua write() trên hóa đơn cha. Kiểm tra tại dòng để bao phủ đường này.
    @api.constrains('charge_id', 'move_id')
    def _check_rental_return_before_invoice_line(self):  # Kiểm tra hóa đơn cha khi một dòng được gắn Charge hoặc chuyển sang hóa đơn khác.
        self.mapped('move_id')._check_rental_return_before_invoice()

    @api.onchange("charge_id")
    def _onchange_charge_id(self):
        if self.charge_id:
            self.name = f"Phụ phí: {self.charge_id.name}"
            self.quantity = self.charge_id.quantity
            self.price_unit = self.charge_id.unit_price
            self.price_catalog_id = self.charge_id.price_catalog_id

    @api.onchange("price_catalog_id")
    def _onchange_price_catalog_id(self):
        if self.price_catalog_id and not self.charge_id:
            self.name = self.price_catalog_id.name
            self.price_unit = self.price_catalog_id.unit_price
