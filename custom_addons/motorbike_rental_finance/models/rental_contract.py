import math

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


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

    def _check_returned_before_invoice(self):  # Kiểm tra từng hợp đồng đã được thu hồi đủ xe trước khi cho lập hóa đơn.
        """Dùng chung một điều kiện thu hồi cho mọi đường lập hóa đơn thuê xe.

        Operations là nơi xác nhận giao/nhận. Finance chỉ đọc các dòng đó,
        không tự sửa trạng thái phiếu vận hành hoặc trạng thái xe Fleet.
        Hàm có thể nhận nhiều hợp đồng; một hợp đồng chưa đủ điều kiện
        sẽ làm thao tác lập/xác nhận hóa đơn bị từ chối bằng UserError.
        """
        for contract in self:
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

    @api.model_create_multi
    def create(self, vals_list):
        contracts = super().create(vals_list)
        # Creating a contract also prepares its receipt; only Finance can
        # confirm payment using the existing payment ACLs.
        payments = self.env["motorbike.rental.payment"].sudo()
        for contract in contracts:
            if contract.currency_id.is_zero(contract.deposit_amount):
                continue
            if payments.search_count([
                ("contract_id", "=", contract.id),
                ("transaction_type", "=", "deposit"),
            ]):
                continue
            payments.create({
                "customer_id": contract.customer_id.id,
                "contract_id": contract.id,
                "transaction_type": "deposit",
                "amount": contract.deposit_amount,
                "currency_id": contract.currency_id.id,
                "payment_method": "cash",
                "state": "draft",
                "note": "Phiếu thu cọc tự tạo từ hợp đồng %s." % contract.name,
            })
        return contracts

    def _sync_draft_deposit_payment(self):  # Đồng bộ hoặc dùng lại phiếu cọc chưa xác nhận của hợp đồng nháp, không tạo phiếu thứ hai.
        # self là tập hợp đồng Odoo đang xử lý, có thể gồm một hoặc nhiều bản ghi.
        # for ... in ... lần lượt lấy từng hợp đồng và đặt vào biến contract.
        for contract in self:

            # draft là tên kỹ thuật của trạng thái Nháp.
            # != nghĩa là "khác"; continue bỏ qua hợp đồng này và chuyển sang hợp đồng tiếp theo.
            if contract.state != "draft":
                continue

            # env["tên.model"] truy cập đối tượng quản lý dữ liệu của model thanh toán.
            # sudo cho phép hệ thống chuẩn bị phiếu nháp dù nhân viên sửa hợp đồng
            # chưa có quyền Finance, giống cách tự tạo cọc lúc tạo hợp đồng.
            # Hàm này không xác nhận đã thu tiền và không sửa phiếu đã xác nhận.
            payments = self.env["motorbike.rental.payment"].sudo()

            # search tìm các bản ghi thỏa đồng thời những điều kiện trong danh sách.
            # Mỗi bộ ba gồm (tên trường, phép so sánh, giá trị cần so sánh).
            deposits = payments.search([
                ("contract_id", "=", contract.id),  # contract.id là mã số hợp đồng đang sửa trong database.
                ("transaction_type", "=", "deposit"),  # deposit là giao dịch cọc; không lấy tiền thuê/hoàn/thu thêm.
            ])

            # filtered lọc bản ghi; lambda là cách viết hàm kiểm tra ngắn cho từng phiếu.
            # Một tập có bản ghi được Python hiểu là True, tập rỗng được hiểu là False.
            # Đã có phiếu cọc xác nhận thì không tự sửa hoặc tạo lại phiếu cọc:
            # số tiền đã thu là lịch sử thực tế, không được đổi theo số cọc mới trên hợp đồng.
            if deposits.filtered(lambda payment: payment.state == "confirmed"):
                continue

            # Dùng lại phiếu nháp hoặc đã hủy, không tạo phiếu cọc thứ hai.
            # Tên biến draft_deposits được giữ lại, nhưng gồm cả phiếu đã hủy có thể đưa về nháp.
            # in kiểm tra trạng thái có thuộc một trong hai giá trị bên dưới hay không.
            draft_deposits = deposits.filtered(
                lambda payment: payment.state in ("draft", "cancelled")
            )

            # is_zero kiểm tra số tiền bằng 0 theo độ làm tròn của đồng tiền hợp đồng.
            # Nếu không còn yêu cầu cọc thì giữ phiếu ở trạng thái đã hủy thay vì ghi số tiền 0,
            # vì model thanh toán yêu cầu số tiền trên mỗi phiếu phải lớn hơn 0.
            if contract.currency_id.is_zero(contract.deposit_amount):
                draft_deposits.write({"state": "cancelled"})  # write cập nhật trạng thái, không xóa phiếu.
                continue  # Đã xử lý trường hợp không thu cọc, không cần chạy nhánh tạo/cập nhật bên dưới.

            # len đếm số bản ghi. Nếu dữ liệu cũ có nhiều phiếu chưa xác nhận thì không tự sửa tất cả thành cùng số tiền,
            # vì làm vậy có thể nhân đôi hoặc nhân ba số cọc phải thu.
            # UserError dừng thao tác và hiện hướng dẫn để nhân viên xử lý dữ liệu chưa rõ ràng.
            if len(draft_deposits) > 1:
                raise UserError(
                    "Hợp đồng có nhiều phiếu cọc chưa xác nhận. "
                    "Vui lòng xử lý phiếu cọc trùng trước khi đổi tiền cọc."
                )

            # Dictionary là tập cặp tên trường và giá trị mới cần lưu.
            # .id lấy mã bản ghi khách/đồng tiền để gán vào trường liên kết Many2one.
            values = {
                "customer_id": contract.customer_id.id,  # Đồng bộ đúng khách đang ghi trên hợp đồng.
                "currency_id": contract.currency_id.id,  # Đồng bộ đúng đồng tiền hợp đồng.
                "amount": contract.deposit_amount,  # Lấy nguyên số tiền cọc mới trên hợp đồng.
            }

            if draft_deposits:  # Có đúng một phiếu nháp hoặc đã hủy sau các bước kiểm tra bên trên.
                # Cập nhật phiếu cũ, giữ nguyên mã phiếu và không tạo phiếu cọc thứ hai.
                # **values lấy các cặp tên trường/giá trị đã chuẩn bị vào dictionary mới.
                # state = draft đưa phiếu về nháp, chưa xác nhận đã thu tiền.
                draft_deposits.write({**values, "state": "draft"})

            else:  # Chưa có phiếu cọc; ví dụ lúc tạo hợp đồng cọc bằng 0 nhưng bây giờ bắt đầu yêu cầu cọc.
                # update bổ sung các cặp tên trường/giá trị vào dictionary đã chuẩn bị.
                values.update({
                    "contract_id": contract.id,  # Liên kết phiếu mới với hợp đồng đang sửa.
                    "transaction_type": "deposit",  # Giao dịch cọc, không phải một khoản phụ phí.
                    "payment_method": "cash",  # Mặc định tiền mặt; nhân viên vẫn chọn lại được trước khi thu.
                    "state": "draft",  # Chỉ chuẩn bị phiếu, chưa xác nhận khách đã nộp tiền.
                    "note": "Phiếu thu cọc tự tạo từ hợp đồng %s." % contract.name,  # %s được thay bằng mã hợp đồng.
                })
                payments.create(values)  # create tạo một bản ghi cọc nháp mới từ các giá trị đã chuẩn bị.

    def _check_upfront_payments(self):
        # Contract access was checked by write(). Read receipts for these
        # contracts only, so Rental users need no Finance write privileges.
        for contract in self:
            payments = self.env["motorbike.rental.payment"].sudo().search([
                ("contract_id", "=", contract.id),
                ("customer_id", "=", contract.customer_id.id),
                ("currency_id", "=", contract.currency_id.id),
                ("state", "=", "confirmed"),
                ("transaction_type", "in", ["deposit", "rental_payment"]),
            ]).filtered(lambda payment: math.isfinite(payment.amount) and payment.amount > 0)
            missing = []
            for transaction_type, required, label in [
                ("deposit", contract.deposit_amount, "tiền cọc"),
                ("rental_payment", contract.total_amount, "tiền thuê"),
            ]:
                received = sum(payments.filtered(
                    lambda payment: payment.transaction_type == transaction_type
                ).mapped("amount"))
                if float_compare(received, required,
                                 precision_rounding=contract.currency_id.rounding) < 0:
                    missing.append("%s: còn thiếu %s %s" % (
                        label, format(contract.currency_id.round(required - received),
                                      ",.%sf" % contract.currency_id.decimal_places),
                        contract.currency_id.name))
            if missing:
                raise UserError(
                    "Chưa thể ký hợp đồng %s. Vui lòng xác nhận thu đủ tiền thuê và cọc.\n%s"
                    % (contract.name, "\n".join(missing)))

    def write(self, vals):  # Đồng bộ cọc nháp và kiểm tra thu đủ tiền trước khi ký, xác nhận hóa đơn trước khi đóng hợp đồng.
        """write là hàm Odoo gọi khi cập nhật một hoặc nhiều bản ghi đã có.

        self là tập hợp đồng cần sửa. vals là dictionary (tập cặp khóa/giá trị)
        chứa các trường muốn sửa, ví dụ {"state": "done"} là đổi sang Hoàn tất.
        Kiểm tra ở write giúp cả nút trên giao diện lẫn thao tác cập nhật qua
        code đều phải tuân theo điều kiện kết thúc, thay vì chỉ ẩn nút Hoàn tất.
        """
        # get("state") lấy giá trị của khóa state; nếu lần lưu này không đổi trạng thái thì trả về None.
        # done là giá trị kỹ thuật của trạng thái Hoàn tất; chỉ nhánh này cần kiểm tra hóa đơn kết thúc.
        if vals.get("state") == "done":
            for contract in self:  # Lần lượt kiểm tra từng hợp đồng nếu Odoo đang cập nhật nhiều hợp đồng.
                contract._check_returned_before_invoice()  # Bắt buộc đã xác nhận thu hồi đầy đủ xe.

                # invoice_ids là tập hóa đơn liên kết với hợp đồng qua trường contract_id.
                # filtered lọc bản ghi; lambda invoice: ... là hàm ngắn kiểm tra mỗi hóa đơn.
                posted_invoices = contract.invoice_ids.filtered(
                    lambda invoice: (
                        invoice.move_type == "out_invoice"  # Chỉ tính hóa đơn khách hàng, không tính hóa đơn hoàn/nhà cung cấp.
                        and invoice.state == "posted"  # posted = đã xác nhận; hóa đơn nháp hoặc hủy không đủ điều kiện.
                    )
                )

                # not posted_invoices: tập rỗng nghĩa là chưa có hóa đơn được xác nhận.
                # or: chỉ cần một điều kiện chưa đạt là dừng, không cho đổi hợp đồng sang done.
                if (
                    not posted_invoices
                    or contract.settlement_status != "settled"  # settled là đã hoàn thành bước ghi nhận thu/hoàn tiền.
                    or not contract.currency_id.is_zero(contract.settlement_balance)  # Số dư phải bằng 0 theo đồng tiền.
                ):
                    raise UserError("Vui lòng xác nhận hóa đơn và hoàn tất thu/hoàn tiền trước.")

        # super() gọi hàm cập nhật kế thừa, bao gồm kiểm tra chuyển trạng thái trong module Core.
        # Chỉ lưu sau khi các điều kiện kết thúc ở trên đã đạt; lỗi thì không đổi trạng thái.
        result = super().write(vals)

        # Đồng bộ sau khi lưu để đọc đúng số cọc, khách và đồng tiền mới trên hợp đồng.
        # "in vals" kiểm tra lần lưu này có sửa trường tương ứng không.
        # or nghĩa là "hoặc": đổi một trong ba thông tin thì cần kiểm tra đồng bộ phiếu cọc.
        # Hàm được gọi tự bỏ qua hợp đồng không còn nháp và phiếu cọc đã xác nhận.
        if (
            "deposit_amount" in vals
            or "customer_id" in vals
            or "currency_id" in vals
        ):
            self._sync_draft_deposit_payment()

        if vals.get("state") == "confirmed":  # confirmed là Đã xác nhận/ký hợp đồng, khác với done là kết thúc thuê.
            # Giữ chốt chặn đã có: phải xác nhận thu đủ tiền thuê và cọc trước khi ký.
            # Kiểm tra sau super để đọc dữ liệu mới nhất; nếu thiếu tiền, UserError làm giao dịch bị hoàn tác.
            self._check_upfront_payments()
        return result  # Trả nguyên kết quả cập nhật của Odoo, không thay cách xử lý của các module khác.

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )
    def _get_confirmed_net_received(self):  # Tính tiền thực thu ròng của một hợp đồng từ các phiếu thu/hoàn đã xác nhận.
        """Trả về tiền đã nhận của khách trừ tiền đã hoàn cho khách.

        Tiền nhận gồm ba loại: cọc, thanh toán tiền thuê và thu thêm.
        Tiền hoàn chỉ được trừ khi phiếu hoàn đã được xác nhận; việc tạo
        phiếu hoàn nháp chưa có nghĩa là doanh nghiệp đã trả tiền cho khách.
        Giá trị cọc ghi trên hợp đồng là số phải thu, không chứng minh đã thu,
        nên hàm này chỉ đọc các phiếu tiền thực tế trong payment_ids.
        """
        self.ensure_one()  # Mỗi lần gọi chỉ tính một hợp đồng để không trộn tiền của nhiều khách/hợp đồng.

        # payment_ids chỉ chứa phiếu liên kết với hợp đồng hiện tại qua contract_id.
        # filtered giữ lại phiếu thỏa mãn đồng thời tất cả điều kiện bên dưới.
        payments = self.payment_ids.filtered(
            lambda payment: (
                payment.state == "confirmed"  # Chỉ tính tiền đã xác nhận; bỏ qua phiếu nháp và phiếu đã hủy.
                and payment.customer_id == self.customer_id  # Bỏ phiếu gắn nhầm khách dù cùng hợp đồng.
                and payment.currency_id == self.currency_id  # Không cộng trực tiếp các đồng tiền khác nhau.
                and math.isfinite(payment.amount)  # Loại NaN/vô cực để không làm hỏng kết quả cộng tiền.
                and payment.amount > 0  # Số tiền trên mỗi phiếu phải dương; loại giao dịch quyết định chiều thu/hoàn.
            )
        )

        # Ba loại phiếu này đều là tiền doanh nghiệp đã nhận từ khách.
        # mapped("amount") lấy danh sách số tiền; sum cộng chúng, trả về 0 nếu không có phiếu.
        received = sum(payments.filtered(
            lambda payment: payment.transaction_type in (
                "deposit",  # Tiền cọc thực tế đã nhận, có thể được thu qua nhiều phiếu.
                "rental_payment",  # Tiền thuê khách đã trả trước; phải trừ khi quyết toán để tránh thu lại.
                "additional_payment",  # Tiền khách đã nộp bổ sung để thanh toán phần còn thiếu.
            )
        ).mapped("amount"))

        # Tiền hoàn đã xác nhận là tiền đã trả ra, làm giảm số tiền đang giữ của khách.
        refunded = sum(payments.filtered(
            lambda payment: payment.transaction_type == "refund"  # Chỉ chọn phiếu hoàn từ tập phiếu hợp lệ ở trên.
        ).mapped("amount"))  # Cộng số tiền đã hoàn; phiếu hoàn nháp không nằm trong tập payments.

        return received - refunded  # Trả số tiền thực thu ròng, chưa làm tròn để chỉ làm tròn số dư cuối cùng.

    # Các trường bên dưới thay đổi thì Odoo phải tính lại số dư được lưu trong database.
    # Không phụ thuộc deposit_amount: thay số cọc phải thu không đồng nghĩa tiền thực thu thay đổi.
    @api.depends(
        "total_amount",  # Tiền thuê phải thanh toán thay đổi thì nghĩa vụ thanh toán thay đổi.
        "customer_id",  # Đổi khách trên hợp đồng thì cần đối chiếu lại chủ thể của các phiếu tiền.
        "currency_id",  # Đổi đồng tiền thì cần lọc lại phiếu và áp dụng độ làm tròn tương ứng.
        "charge_ids",  # Thêm, xóa hoặc chuyển phụ phí sang hợp đồng khác thì cần tính lại tổng phụ phí.
        "charge_ids.state",  # Xác nhận/hủy/đưa phụ phí về nháp làm thay đổi khoản phải thanh toán.
        "charge_ids.amount",  # Sửa số tiền phụ phí làm thay đổi tổng nghĩa vụ thanh toán.
        "payment_ids",  # Thêm, xóa hoặc chuyển phiếu tiền sang hợp đồng khác thì cần tính lại tiền thực thu.
        "payment_ids.state",  # Xác nhận/hủy/đưa phiếu về nháp làm thay đổi tiền được tính vào quyết toán.
        "payment_ids.amount",  # Sửa số tiền trên phiếu thì cần cập nhật số dư.
        "payment_ids.transaction_type",  # Đổi loại thu thành hoàn hoặc ngược lại sẽ đổi chiều dòng tiền.
        "payment_ids.customer_id",  # Sửa khách trên phiếu thì cần kiểm tra lại phiếu có khớp hợp đồng không.
        "payment_ids.currency_id",  # Sửa đồng tiền trên phiếu thì cần kiểm tra lại khả năng cộng vào số dư.
    )
    def _compute_settlement_preview(self):  # Tính tổng phụ phí đã duyệt và số dư còn phải thu thêm hoặc hoàn cho từng hợp đồng.
        """Số dư = tiền thuê + phụ phí đã duyệt - tiền thực thu ròng.

        Dương: khách còn phải trả thêm. Âm: doanh nghiệp còn phải hoàn khách.
        Bằng 0: các khoản phải thanh toán đã được bù đủ bởi tiền thực thu ròng.
        Ví dụ thuê 1 triệu, phụ phí 300 nghìn, đã thu thuê 1 triệu và cọc
        2 triệu: số dư là -1,7 triệu, tức cần hoàn lại khách 1,7 triệu.
        Sau khi xác nhận hoàn đủ 1,7 triệu, số dư được tính lại thành 0.
        """
        # Odoo có thể yêu cầu tính nhiều hợp đồng cùng lúc; phải gán đủ hai trường cho từng bản ghi.
        for contract in self:
            # Chỉ phụ phí đã xác nhận mới là khoản khách phải trả; bỏ qua phụ phí nháp/đã hủy.
            penalties = sum(
                contract.charge_ids.filtered(
                    lambda charge: charge.state == "confirmed"  # Giữ lại các khoản đã được duyệt.
                ).mapped("amount")  # Lấy số tiền từng khoản để cộng thành tổng phụ phí.
            )

            # Trừ cả tiền thuê đã thu trước và cọc thực thu, tránh tính tiền thuê lần thứ hai.
            # Khoản thu thêm/hoàn đã xác nhận cũng được phản ánh qua hàm tính tiền thực thu ròng.
            balance = (
                contract.total_amount  # Tiền thuê phải trả theo hợp đồng.
                + penalties  # Cộng phụ phí đã duyệt để ra toàn bộ nghĩa vụ thanh toán.
                - contract._get_confirmed_net_received()  # Trừ tiền đã nhận sau khi trừ các khoản đã hoàn.
            )

            contract.total_penalty_amount = penalties  # Cập nhật tổng phụ phí hiển thị trên hợp đồng.
            # Làm tròn theo quy tắc của đồng tiền, tránh tạo khoản thu/hoàn do sai số số thực.
            contract.settlement_balance = contract.currency_id.round(balance)

    # 6. Các hàm Action / Nghiệp vụ (nút bấm button)
    def action_settlement(self):  # Chặn quy trình quyết toán riêng cũ và hướng dẫn xác nhận thu/hoàn ngay trên hóa đơn.
        # action_settlement là tên hàm của nút quyết toán trước đây; giữ tên hàm để thao tác cũ
        # nếu còn gọi tới sẽ nhận được hướng dẫn rõ ràng, thay vì lỗi "không tìm thấy hàm".
        # raise nghĩa là phát sinh lỗi có chủ đích; UserError giúp Odoo hiện thông báo cho nhân viên.
        # Hàm này không tạo phiếu tiền và không đổi trạng thái hợp đồng.
        raise UserError("Vui lòng xác nhận thu/hoàn tiền ngay trên hóa đơn của hợp đồng.")
