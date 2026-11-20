import math

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from .rental_payment import _CONTRACT_CONFIRM  # Dấu nội bộ: chỉ nút Ký hợp đồng được xác nhận hai phiếu thu ban đầu.


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
    
    upfront_received_check = fields.Boolean(string="Đã nhận cọc và tiền thuê", copy=False)  # Sao chép hợp đồng không sao chép dấu tích đã nhận tiền.
    
    upfront_payment_method = fields.Selection(  # Phương thức thanh toán
        [("cash", "Tiền mặt"), ("bank_transfer", "Chuyển khoản"), ("credit_card", "Thẻ")],  # Các giá trị kỹ thuật phải khớp với phiếu tiền.
        string="Phương thức nhận tiền",  # Tên hiển thị cạnh ô xác nhận đã nhận đủ tiền.
        copy=False,  # Sao chép hợp đồng không tự nhận lại phương thức của giao dịch cũ.
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




    """ 
    tự tạo hoặc cập nhật phiếu thu tiền thuê theo hợp đồng:

- Chỉ xử lý hợp đồng còn **Nháp**.
- Nếu đã có phiếu **xác nhận thu tiền** thì giữ nguyên.
- Nếu chưa thu: cập nhật phiếu cũ hoặc tạo phiếu Nháp mới theo tổng tiền hợp đồng.
- Nếu tổng tiền bằng 0: hủy phiếu Nháp hiện có.

Mục đích: **giữ phiếu thu khớp với hợp đồng khi chỉnh sửa, chưa xác nhận khách đã trả tiền**.""" 

    def _sync_draft_rent_payment(self):  # Tạo hoặc cập nhật phiếu tiền thuê Nháp.
        Payment = self.env["motorbike.rental.payment"].sudo()  # Lấy model phiếu tiền.
        for contract in self:  # Xử lý từng hợp đồng.
            if contract.state != "draft":  # Hợp đồng đã ký thì không sửa phiếu.
                continue  # Chuyển sang hợp đồng tiếp theo.

            rents = Payment.search([("contract_id", "=", contract.id), ("transaction_type", "=", "rental_payment")])  # Tìm phiếu thuê đã có.
            if rents.filtered(lambda p: p.state == "confirmed"):  # Đã xác nhận thu tiền thì giữ nguyên.
                continue  

            rent = rents.filtered(lambda p: p.state in ("draft", "cancelled"))[:1]  # Dùng lại phiếu Nháp hoặc Đã hủy.
            amount = contract.total_amount  # Lấy tổng tiền thuê từ hợp đồng.

            if contract.currency_id.is_zero(amount):  # Chưa có xe hoặc tổng tiền bằng 0.
                if rent and rent.state == "draft":  # Nếu đang có phiếu Nháp.
                    rent.action_cancel()  # Hủy phiếu Nháp, không xóa dữ liệu.
                continue  # Không tạo phiếu số tiền 0.

            values = {"customer_id": contract.customer_id.id, "currency_id": contract.currency_id.id, "amount": amount}  # Lấy đúng khách, tiền tệ và số tiền.
            if rent:  # Đã có phiếu chưa thu tiền.
                rent.write({**values, "state": "draft"})  # Cập nhật phiếu cũ.
            else:  # Chưa có phiếu tiền thuê. (tạo phiếu thuê)
                Payment.create({**values, "contract_id": contract.id, "transaction_type": "rental_payment", "payment_method": "cash", "state": "draft"})  # Tạo phiếu Nháp.




    """Khi tạo hợp đồng mới, tự tạo **phiếu thu cọc** nếu có tiền cọc và chưa có phiếu, đồng thời chuẩn bị **phiếu thu tiền thuê**.
       Các phiếu đều ở trạng thái **Nháp**, chưa xác nhận đã thu tiền."""
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
        contracts._sync_draft_rent_payment()  # Tạo phiếu nếu hợp đồng đã có xe và giá.
        return contracts




    """
    Hàm này **đồng bộ phiếu thu cọc khi sửa hợp đồng Nháp**:

    - Có phiếu chưa xác nhận: cập nhật theo tiền cọc mới, dùng lại cả phiếu đã hủy.
    - Chưa có phiếu: tạo phiếu Nháp mới.
    - Tiền cọc bằng 0: hủy các phiếu chưa xác nhận.
    - Có nhiều phiếu chưa xác nhận: báo lỗi để xử lý trùng.
    - Đã có phiếu xác nhận thu cọc: giữ nguyên.
    """
    def _sync_draft_deposit_payment(self):  # Đồng bộ hoặc dùng lại phiếu cọc chưa xác nhận của hợp đồng nháp, không tạo phiếu thứ hai.
        for contract in self:
            if contract.state != "draft":
                continue

            # sudo cho phép hệ thống chuẩn bị phiếu nháp dù nhân viên sửa hợp đồng
            # Hàm này không xác nhận đã thu tiền và không sửa phiếu đã xác nhận.
            payments = self.env["motorbike.rental.payment"].sudo()

            # Mỗi bộ ba gồm (tên trường, phép so sánh, giá trị cần so sánh).
            deposits = payments.search([
                ("contract_id", "=", contract.id),  # contract.id là mã số hợp đồng đang sửa trong database.
                ("transaction_type", "=", "deposit"),  # deposit là giao dịch cọc; không lấy tiền thuê/hoàn/thu thêm.
            ])

            # Đã có phiếu cọc xác nhận thì không tự sửa hoặc tạo lại phiếu cọc:
            # số tiền đã thu là lịch sử thực tế, không được đổi theo số cọc mới trên hợp đồng.
            if deposits.filtered(lambda payment: payment.state == "confirmed"):
                continue

            # Dùng lại phiếu nháp hoặc đã hủy, không tạo phiếu cọc thứ hai.
            # in kiểm tra trạng thái có thuộc một trong hai giá trị bên dưới hay không.
            draft_deposits = deposits.filtered(
                lambda payment: payment.state in ("draft", "cancelled")
            )

            # is_zero kiểm tra số tiền bằng 0 theo độ làm tròn của đồng tiền hợp đồng.
            # Nếu không còn yêu cầu cọc thì giữ phiếu ở trạng thái đã hủy thay vì ghi số tiền 0,
            # vì model thanh toán yêu cầu số tiền trên mỗi phiếu phải lớn hơn 0.
            if contract.currency_id.is_zero(contract.deposit_amount):
                draft_deposits.write({"state": "cancelled"})  # write cập nhật trạng thái, không xóa phiếu.
                continue  

            # len đếm số bản ghi. Nếu dữ liệu cũ có nhiều phiếu chưa xác nhận thì không tự sửa tất cả thành cùng số tiền,
            # vì làm vậy có thể nhân đôi hoặc nhân ba số cọc phải thu.
            if len(draft_deposits) > 1:
                raise UserError(
                    "Hợp đồng có nhiều phiếu cọc chưa xác nhận. "
                    "Vui lòng xử lý phiếu cọc trùng trước khi đổi tiền cọc."
                )

            # Dictionary là tập cặp tên trường và giá trị mới cần lưu.
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
                values.update({
                    "contract_id": contract.id,  # Liên kết phiếu mới với hợp đồng đang sửa.
                    "transaction_type": "deposit", 
                    "payment_method": "cash",  
                    "state": "draft",  
                    "note": "Phiếu thu cọc tự tạo từ hợp đồng %s." % contract.name,  # %s được thay bằng mã hợp đồng.
                })
                payments.create(values)  # create tạo một bản ghi cọc nháp mới từ các giá trị đã chuẩn bị.



    """
    Hàm này kiểm tra đã thu đủ tiền cọc và tiền thuê trước khi ký hợp đồng.

    Chỉ tính phiếu đã xác nhận, đúng hợp đồng, khách hàng và đồng tiền. 
    Nếu thiếu khoản nào, hệ thống chặn ký và báo số tiền còn thiếu của khoản đó
    """
    
    def _check_upfront_payments(self):
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

    @api.onchange("deposit_amount", "line_ids", "start_date", "end_date", "customer_id", "currency_id")  # Theo dõi thông tin ảnh hưởng tiền hoặc khách.
    def _onchange_upfront_details(self):  # Bỏ tích dấu ngay khi nhân viên sửa thông tin trên form hợp đồng.
        self.upfront_received_check = False  # Buộc nhân viên kiểm tra lại hai khoản trước khi ký.


        """
    Hàm này **xác nhận thu tiền rồi mới ký hợp đồng**:

    - Yêu cầu tích đã nhận tiền và chọn phương thức thanh toán.
    - Kiểm tra có đúng một phiếu cọc và một phiếu tiền thuê, khớp khách hàng,
    đồng tiền và số tiền.
    - Tự xác nhận các phiếu còn Nháp, sau đó ký hợp đồng.

    Nếu có lỗi, toàn bộ thao tác được hoàn tác.
        """
    def action_confirm(self):  # Xác nhận hai phiếu đã thu rồi mới xác nhận hợp đồng.
        for contract in self:  # Xử lý từng hợp đồng được chọn.
            if not contract.upfront_received_check:  # Chưa tích xác nhận đã nhận cả cọc và tiền thuê thì chưa được ký.
                raise UserError("Phải xác nhận đã nhận cọc và tiền thuê.")  # Báo rõ lý do cho nhân viên.
            if not contract.upfront_payment_method:  # Chưa ghi nhận khách đã trả bằng tiền mặt, chuyển khoản hay thẻ.
                raise UserError("Vui lòng chọn phương thức nhận cọc và tiền thuê.")  # Không để hai phiếu giữ mặc định Tiền mặt sai thực tế.
            for kind, required in (("deposit", contract.deposit_amount), ("rental_payment", contract.total_amount)):  # Kiểm tra lần lượt cọc và tiền thuê.
                receipts = contract.payment_ids.filtered(lambda p: p.transaction_type == kind and p.state in ("draft", "confirmed"))  # Chỉ lấy phiếu đúng loại chưa hủy.
                if len(receipts) != 1 or contract.currency_id.is_zero(required):  # Mỗi khoản phải có đúng một phiếu với số tiền dương.
                    raise UserError("Hợp đồng phải có đúng một phiếu cọc và một phiếu tiền thuê có số tiền lớn hơn 0.")  # Không nhận phiếu thiếu hoặc trùng.
                receipt = receipts[0]  # Lấy phiếu duy nhất vừa được kiểm tra.
                if receipt.customer_id != contract.customer_id or receipt.currency_id != contract.currency_id or float_compare(receipt.amount, required, precision_rounding=contract.currency_id.rounding):  # Đối chiếu khách, đồng tiền và số tiền.
                    raise UserError("Thông tin hoặc số tiền trên phiếu chưa khớp hợp đồng.")  # Không xác nhận phiếu sai dữ liệu.
                if receipt.state == "draft":  # Phiếu đã xác nhận ở Finance thì giữ nguyên, không ghi nhận lần hai.
                    receipt.payment_method = contract.upfront_payment_method  # Ghi phương thức vừa chọn vào phiếu còn nháp.
                    receipt.with_context(_contract_confirm=_CONTRACT_CONFIRM).action_confirm()  # Truyền dấu nội bộ để xác nhận phiếu nháp trong cùng thao tác ký.
        return super().action_confirm()  # Ký hợp đồng sau khi hai phiếu đã xác nhận; lỗi sẽ hoàn tác toàn bộ thao tác.

    
    
    """Hàm này kiểm tra xe đã bắt đầu được giao chưa 
    trước khi cho hủy hợp đồng và hoàn cọc.
    Nếu có bất kỳ xe nào khác trạng thái Chờ giao, 
    hệ thống chặn hủy và yêu cầu thu hồi xe, kết thúc hợp đồng qua hóa đơn"""
    
    def _check_cancel_before_delivery(self):  # Kiểm tra hợp đồng chưa bắt đầu giao bất kỳ xe nào trước khi cho hoàn cọc và hủy.
        for contract in self:  # Một thao tác có thể kiểm tra nhiều hợp đồng, nên xét từng hợp đồng.
            tickets = self.env["rental.operation.ticket"].sudo().search([("contract_id", "=", contract.id)])  # Tìm tất cả phiếu vận hành, kể cả phiếu người dùng không xem được.
            lines = tickets.mapped("vehicle_detail_ids")  # Gom các dòng xe từ toàn bộ phiếu vừa tìm được.
            # any trả về True ngay khi gặp một dòng có trạng thái khác waiting (chờ giao).
            if any(line.status != "waiting" for line in lines):  # Chỉ waiting nghĩa là chưa bắt đầu giao xe.
                raise UserError("Xe đã bắt đầu được giao; hãy thu hồi xe và kết thúc hợp đồng qua hóa đơn.")  # Không hủy trực tiếp khi đã giao xe.



        """
        Hàm xử lý hủy hợp đồng:
        Đã ký, chưa giao xe: mở phiếu hoàn cọc, dùng lại phiếu Nháp nếu có; 
            chưa hủy hợp đồng ngay và không hoàn tiền thuê.
        Còn Nháp: chưa thu tiền thì hủy hợp đồng và phiếu thu Nháp; 
             đã thu tiền thì yêu cầu xử lý tiền trước.
        Đã bắt đầu giao xe hoặc ở trạng thái khác: chặn hủy.
        """
    def action_cancel(self):  # Hủy hợp đồng nháp hoặc mở phiếu hoàn cọc nếu đã ký nhưng chưa giao xe.
        if self.filtered(lambda contract: contract.state == "confirmed"):  # Hợp đồng đã ký phải hoàn cọc thật trước khi hủy.
            self.ensure_one()  # Giao diện phiếu hoàn tiền chỉ mở cho một hợp đồng mỗi lần.
            self._check_cancel_before_delivery()  # Chặn nếu bất kỳ xe nào đã rời trạng thái chờ giao.
            # filtered giữ các phiếu thỏa điều kiện sau lambda; ở đây chỉ lấy loại Hoàn tiền.
            refunds = self.payment_ids.filtered(lambda payment: payment.transaction_type == "refund")  # Tìm phiếu hoàn cọc đã có của hợp đồng.
            if refunds.filtered(lambda payment: payment.state == "confirmed"):  # Không mở thêm phiếu nếu đã ghi nhận hoàn tiền.
                raise UserError("Hợp đồng đã có phiếu hoàn cọc được xác nhận.")  # Tránh ghi nhận hoàn cọc lần hai.
            # [:1] chỉ lấy phiếu đầu tiên; tập rỗng vẫn an toàn nếu chưa có phiếu nháp.
            draft_refund = refunds.filtered(lambda payment: payment.state == "draft")[:1]  # Dùng lại phiếu nháp nếu người dùng từng thoát khỏi form.
            if draft_refund:  # Phiếu nháp cũ có thể đang chứa số tiền hoặc thông tin khách không đúng.
                draft_refund.write({"amount": self.deposit_amount, "customer_id": self.customer_id.id, "currency_id": self.currency_id.id})  # Điền lại đúng cọc, khách và tiền tệ trước khi mở form.
            return {  # Trả hành động mở form phiếu tiền có sẵn của Finance.
                "type": "ir.actions.act_window",  # Odoo hiểu đây là lệnh mở một màn hình.
                "name": "Hoàn cọc trước khi hủy hợp đồng",  # Tiêu đề để nhân viên hiểu bước đang làm.
                "res_model": "motorbike.rental.payment",  # Mở đúng model phiếu tiền.
                "view_mode": "form",  # Hiển thị form để chọn cách hoàn tiền và xác nhận.
                "views": [(self.env.ref("motorbike_rental_finance.view_motorbike_rental_payment_form").id, "form")],  # Dùng form Finance hiện có.
                "res_id": draft_refund.id or False,  # Có phiếu nháp thì mở lại; chưa có thì mở form tạo mới.
                "target": "current",  # Mở ngay trong màn hình hiện tại.
                "context": {  # Điền sẵn dữ liệu của hợp đồng vào phiếu mới.
                    "default_contract_id": self.id,  # Gắn phiếu với hợp đồng đang hủy.
                    "default_transaction_type": "refund",  # Đây là phiếu hoàn tiền cho khách.
                    "default_customer_id": self.customer_id.id,  # Lấy đúng khách của hợp đồng.
                    "default_currency_id": self.currency_id.id,  # Lấy đúng đồng tiền của hợp đồng.
                    "default_amount": self.deposit_amount,  # Hoàn toàn bộ cọc, không hoàn tiền thuê.
                    "default_payment_method": "cash",  # Gợi ý tiền mặt; nhân viên có thể chọn cách hoàn thực tế.
                },
            }
        if self.filtered(lambda contract: contract.state != "draft"):  # Đang thuê/đã xong/đã hủy không được hủy từ nút này.
            raise UserError("Chỉ được hủy hợp đồng nháp hoặc hợp đồng đã ký nhưng chưa giao xe.")  # Hướng người dùng về đúng luồng.
        drafts = self.filtered(lambda contract: contract.state == "draft")  # Chỉ gom các hợp đồng chưa ký.
        receipts = self.env["motorbike.rental.payment"].sudo().search([("contract_id", "in", drafts.ids), ("transaction_type", "in", ("deposit", "rental_payment"))]) if drafts else self.env["motorbike.rental.payment"]  # Tìm phiếu cọc và tiền thuê của các hợp đồng nháp.
        if receipts.filtered(lambda payment: payment.state == "confirmed"):  # Đã thu tiền thật thì không được âm thầm hủy hợp đồng.
            raise UserError("Hợp đồng đã thu tiền; cần xử lý khoản tiền này trước khi hủy.")  # Giữ nguyên lịch sử thu tiền.
        result = super().action_cancel()  # Hủy hợp đồng theo quy tắc hiện có của Core.
        receipts.filtered(lambda payment: payment.state == "draft").action_cancel()  # Hủy phiếu còn nháp, không xóa dữ liệu.
        return result  # Trả kết quả về giao diện Odoo.



    """
    Hàm này **chặn xóa hợp đồng đã có phiếu tiền**, kể cả phiếu Nháp hoặc Đã hủy,
    để giữ liên kết và lịch sử giao dịch.
    Nếu không có phiếu tiền thì tiếp tục xóa theo quy tắc của hệ thống."""
    
    def unlink(self):  # Odoo gọi hàm này khi người dùng yêu cầu xóa một hoặc nhiều hợp đồng.
        # sudo cho phép kiểm tra cả phiếu tiền mà người đang xóa hợp đồng không có quyền xem.
        # search_count đếm mọi phiếu thuộc các hợp đồng này, kể cả phiếu nháp hoặc đã hủy.
        payment_count = self.env["motorbike.rental.payment"].sudo().search_count([
            ("contract_id", "in", self.ids),  # self.ids là mã số của tất cả hợp đồng sắp bị xóa.
        ])
        if payment_count:  # Đã có phiếu tiền thì giữ hợp đồng để không làm phiếu mất liên kết.
            raise UserError("Hợp đồng đã có phiếu tiền, không thể xóa; hãy xử lý và hủy hợp đồng.")
        return super().unlink()  # Không có phiếu tiền thì dùng quy tắc xóa hợp đồng của Core.


    """
        Hàm này chạy mỗi khi cập nhật hợp đồng, để:

    Ký hợp đồng: kiểm tra đã thu đủ cọc và tiền thuê.
    Hoàn tất hợp đồng: yêu cầu thu hồi đủ xe, có hóa đơn đã xác nhận, hoàn tất thu/hoàn tiền và số dư bằng 0.
    Sửa tiền cọc, xe, ngày thuê, khách hoặc đồng tiền: cập nhật các phiếu thu Nháp tương ứng.
    Nếu không đủ điều kiện thì báo lỗi và không lưu thay đổi.

        """
    def write(self, vals):  # Đồng bộ cọc nháp và kiểm tra thu đủ tiền trước khi ký, xác nhận hóa đơn trước khi đóng hợp đồng.
       
        # get("state") lấy giá trị của khóa state; nếu lần lưu này không đổi trạng thái thì trả về None.
        # done là giá trị kỹ thuật của trạng thái Hoàn tất; chỉ nhánh này cần kiểm tra hóa đơn kết thúc.
        if vals.get("state") == "done":
            for contract in self:  # Lần lượt kiểm tra từng hợp đồng nếu Odoo đang cập nhật nhiều hợp đồng.
                self.env["account.move"]._check_returned_before_invoice(contract)  # Bắt buộc đã xác nhận thu hồi đầy đủ xe.

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
            or "line_ids" in vals  # Thêm/bỏ xe làm cọc tự tính thay đổi; phải cập nhật phiếu cọc nháp theo.
            or "customer_id" in vals
            or "currency_id" in vals
        ):
            self._sync_draft_deposit_payment()

        if vals.get("state") == "confirmed":  # confirmed là Đã xác nhận/ký hợp đồng, khác với done là kết thúc thuê.
            # Giữ chốt chặn đã có: phải xác nhận thu đủ tiền thuê và cọc trước khi ký.
            # Kiểm tra sau super để đọc dữ liệu mới nhất; nếu thiếu tiền, UserError làm giao dịch bị hoàn tác.
            self._check_upfront_payments()
        if {"line_ids", "start_date", "end_date", "customer_id", "currency_id"} & vals.keys():  # Thông tin tính tiền thay đổi.
            self._sync_draft_rent_payment()  # Cập nhật phiếu khi hợp đồng còn Nháp.
        return result  # Trả nguyên kết quả cập nhật của Odoo, không thay cách xử lý của các module khác.




    # 5. Các hàm tính toán ( @api.depends , @api.onchange )
    
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
    # Đồng bộ các trường hợp đồng từ kết quả quyết toán của model hóa đơn.
    
    def _compute_settlement_preview(self): 
        """
        Lấy kết quả quyết toán từ model hóa đơn và cập nhật tổng phụ phí,
        số dư trên hợp đồng.
        """
        Invoice = self.env["account.move"]
        for contract in self:
            penalties, balance = Invoice._get_rental_settlement_totals(contract)
            contract.total_penalty_amount = penalties
            contract.settlement_balance = balance
