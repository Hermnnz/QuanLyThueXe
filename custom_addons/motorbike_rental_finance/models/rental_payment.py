    # 1. Đầu file: Các dòng import
import re  # re cung cấp công cụ nhận diện mẫu chuỗi, dùng để đọc số thứ tự trong mã thanh toán cũ.

from odoo import api, fields, models
# UserError dùng để dừng thao tác và hiện thông báo cho nhân viên.
from odoo.exceptions import UserError, ValidationError

# Dấu riêng cho luồng hóa đơn: object() tạo một đối tượng duy nhất trong bộ nhớ.
# Người dùng không thể tự truyền đúng đối tượng này từ giao diện để tạo phiếu thu/hoàn.
_INVOICE_SETTLEMENT = object()

# Dấu riêng cho lúc ký hợp đồng: nút Xác nhận trên hợp đồng mới được chốt hai phiếu thu ban đầu.
_CONTRACT_CONFIRM = object()


    # 2. Khai báo Class và các thuộc tính Model ( _name , _description ...)
class MotorbikeRentalPayment(models.Model):
    _name = "motorbike.rental.payment"
    _description = "Motorbike Rental Payment"

    # 3. Khai báo các trường dữ liệu ( fields )
    name = fields.Char(
        string="Mã thanh toán", 
        required=True,
        copy=False,
        default="/",
        readonly=True,
    )
    
    # ==> name cần tự động tính dựa trên loại giao dịch và ngày thanh toán (VD: DP-20230901-001, RP-20230901-001, RF-20230901-001, AP-20230901-001)
    
    customer_id = fields.Many2one(
        "res.partner",
        string = "Khách hàng",
        required = True,
    )
    
    contract_id= fields.Many2one(
        "rental.contract",
        string="Hợp đồng thuê",
        ondelete="set null"
    )
    
    transaction_type = fields.Selection(
        string="Loại giao dịch",
        selection=[("deposit", "Cọc"), ("rental_payment", "Thanh toán"), ("refund", "Hoàn tiền"), ("additional_payment", "Thu thêm")],
        required=True,
    )
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Loại tiền",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    
    amount = fields.Monetary(
        string="Số tiền",
        required=True,
        currency_field="currency_id"
    )
    
    # amount cần luôn dương 
    
    payment_method = fields.Selection(
        string="Phương thức thanh toán",
        selection = [("cash", "Tiền mặt"), ("bank_transfer", "Chuyển khoản ngân hàng"), ("credit_card", "Thẻ tín dụng")],
        required=True,
    )
    
    payment_date = fields.Date(
        string="Ngày thanh toán",
        required=True,
        default=fields.Date.context_today,
    )
    
    reference=fields.Char(
        string="Mã tham chiếu",
    )
    
    state=fields.Selection(
        string="Trạng thái",
        selection=[("draft", "Bản nháp"), ("confirmed", "Đã xác nhận"), ("cancelled", "Đã hủy")],
        default="draft",
        required=True,
    )
    
    note = fields.Text(
        string="Ghi chú",
    )
    
    invoice_id=fields.Many2one(
        "account.move",
        string="Hóa đơn",
    )

# 4. Các hàm Constraints ( @api.constrains , _sql_constraints )
    def init(self):  # Tạo ràng buộc chống trùng cọc khi cài hoặc cập nhật module.
        # UNIQUE INDEX: database không cho hai phiếu cọc cùng contract_id.
        # IF NOT EXISTS: đã có ràng buộc này thì không tạo lại.
        # WHERE: chỉ áp dụng cho cọc có hợp đồng, kể cả phiếu đã hủy.
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS rental_payment_one_deposit
            ON motorbike_rental_payment (contract_id)
            WHERE transaction_type = 'deposit'
              AND contract_id IS NOT NULL
        """)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Số tiền thanh toán phải lớn hơn 0!")

    # constrains yêu cầu Odoo kiểm tra khi tạo phiếu hoặc sửa các trường bên dưới.
    @api.constrains("contract_id", "transaction_type")
    def _check_single_deposit(self):  # Mỗi hợp đồng chỉ được có một phiếu cọc, kể cả phiếu đã hủy.
        for payment in self:  # Kiểm tra từng phiếu vừa được tạo hoặc cập nhật.
            if payment.contract_id and payment.transaction_type == "deposit":
                # sudo để kiểm tra cả phiếu mà nhân viên không có quyền xem.
                # search_count đếm các phiếu cùng hợp đồng và có loại giao dịch là cọc.
                # Không lọc trạng thái: phiếu nháp, đã xác nhận và đã hủy đều được tính.
                count = self.sudo().search_count([
                    ("contract_id", "=", payment.contract_id.id),
                    ("transaction_type", "=", "deposit"),
                ])
                if count > 1:  # Có phiếu cọc thứ hai thì báo lỗi, Odoo hoàn tác lần lưu.
                    raise ValidationError("Mỗi hợp đồng chỉ được có một phiếu cọc.")

    # Odoo chạy kiểm tra này khi tạo phiếu hoặc đổi hợp đồng/loại giao dịch.
    @api.constrains("contract_id", "transaction_type")
    def _check_single_rental_payment(self):  # Mỗi hợp đồng chỉ có một phiếu thu tiền thuê, kể cả phiếu đã hủy.
        for payment in self:  # Xét từng phiếu vừa được tạo hoặc sửa.
            if payment.contract_id and payment.transaction_type == "rental_payment":  # Chỉ xét tiền thuê có hợp đồng.
                # sudo cho phép đếm cả phiếu nhân viên hiện tại không được quyền xem.
                count = self.sudo().search_count([
                    ("contract_id", "=", payment.contract_id.id),  # Cùng hợp đồng với phiếu đang xét.
                    ("transaction_type", "=", "rental_payment"),  # Chỉ đếm phiếu thu tiền thuê.
                ])
                if count > 1:  # Phiếu thứ hai sẽ làm thu trùng tiền thuê.
                    raise ValidationError("Mỗi hợp đồng chỉ được có một phiếu thu tiền thuê.")

    # constrains chạy khi tạo phiếu hoặc thay đổi loại giao dịch/trạng thái.
    @api.constrains("transaction_type", "state")
    def _check_invoice_settlement(self):  # Chỉ cho hóa đơn quyết toán tiền, trừ phiếu hoàn cọc trước khi giao xe.
        for payment in self:  # Kiểm tra từng phiếu đang được lưu.
            if payment.transaction_type in ("refund", "additional_payment"):
                if payment.transaction_type == "refund" and payment.contract_id.state == "confirmed":  # Hợp đồng đã ký nhưng chưa giao có thể hoàn cọc để hủy.
                    payment.contract_id._check_cancel_before_delivery()  # Không cho dùng ngoại lệ này nếu xe đã bắt đầu giao.
                    continue  # Phiếu hoàn cọc này không cần đi qua hóa đơn cuối kỳ.
                # context chứa thông tin truyền riêng cho thao tác đang chạy.
                # is not kiểm tra có đúng đối tượng nhận diện của luồng hóa đơn hay không.
                if self.env.context.get("_invoice_settlement") is not _INVOICE_SETTLEMENT:
                    raise UserError("Hãy xác nhận thu/hoàn tiền trên hóa đơn cuối hợp đồng.")

    def write(self, vals):  # Kiểm tra khi sửa phiếu tiền: chặn mở phiếu của hợp đồng đã hủy và giữ nguyên các khoản đã chốt.
        # write là hàm Odoo gọi khi lưu thay đổi vào bản ghi đã tồn tại.
        # self là các phiếu tiền đang được sửa, có thể gồm nhiều phiếu.
        #
        # vals là dictionary: tập các cặp tên trường và giá trị mới.
        # Ví dụ {"amount": 500000} nghĩa là muốn đổi số tiền thành 500.000.

        if vals.get("state") == "cancelled" and any(payment.state == "confirmed" for payment in self):  # Có phiếu đã ghi nhận thu tiền.
            raise UserError("Phiếu đã xác nhận thu không được hủy trực tiếp.")  # Giữ nguyên khoản tiền đã thu.

        if vals.get("state") == "confirmed" and self.env.context.get("_contract_confirm") is not _CONTRACT_CONFIRM:  # Không có dấu nội bộ từ nút Ký hợp đồng.
            for payment in self:  # Kiểm tra từng phiếu đang được xác nhận.
                if payment.contract_id and payment.transaction_type in ("deposit", "rental_payment"):  # Chỉ khóa hai khoản thu trước của hợp đồng.
                    raise UserError("Hãy tích đã nhận đủ cọc và tiền thuê, rồi xác nhận trên hợp đồng.")  # Tránh chốt lẻ từng phiếu trong Finance.

        # Hai nút "Về bản nháp" và "Xác nhận" đều đổi trường state qua hàm write này.
        # get lấy trạng thái mới nếu lần lưu có gửi state; in kiểm tra nó có phải nháp/đã xác nhận.
        if vals.get("state") in ("draft", "confirmed"):
            for payment in self:  # Một lần lưu có thể xử lý nhiều phiếu, nên phải kiểm tra từng phiếu.
                if payment.contract_id.state == "cancelled":  # Hợp đồng đã hủy thì không được ghi nhận thu tiền nữa.
                    raise UserError("Hợp đồng đã hủy, không thể mở lại hoặc xác nhận phiếu tiền.")

        # Chỉ kiểm tra khi dữ liệu lưu có chọn hợp đồng đích.
        if vals.get("contract_id"):
            # browse lấy bản ghi hợp đồng theo ID (mã số trong database).
            contract = self.env["rental.contract"].browse(vals["contract_id"])

            for record in self:  # Kiểm tra từng phiếu đang được sửa.
                # Chặn chuyển sang hợp đồng đã hoàn tất; giữ nguyên hợp đồng thì cho qua.
                if record.contract_id != contract and contract.state == "done":
                    raise UserError("Không thể chuyển phiếu vào hợp đồng đã hoàn tất.")

        for payment in self:  # Lần lượt kiểm tra từng phiếu đang được sửa.

            # Khóa mọi phiếu đã xác nhận khi hợp đồng hoàn tất (done) hoặc đã hủy (cancelled).
            # Với cọc/tiền thuê, khóa sớm hơn: ngay khi hợp đồng đã ký (confirmed)
            # hoặc đang thuê (in_progress), vì các phiếu này chứng minh đã thu đủ tiền để ký.
            # or nghĩa là "hoặc", and nghĩa là "và"; in kiểm tra giá trị có trong nhóm hay không.
            locked_contract = (
                payment.contract_id.state in ("done", "cancelled")  # Phiếu hoàn cọc sau hủy cũng là lịch sử tiền đã chốt.
                or (
                    payment.contract_id.state in ("confirmed", "in_progress")
                    and payment.transaction_type in ("deposit", "rental_payment")
                )
            )

            # != nghĩa là "khác"; not đảo điều kiện đúng/sai.
            # Phiếu chưa xác nhận hoặc chưa thuộc diện khóa thì kiểm tra phiếu tiếp theo.
            if payment.state != "confirmed" or not locked_contract:
                continue  # Chuyển sang phiếu tiếp theo trong vòng lặp.

            # Lưu giá trị HIỆN TẠI của các trường không được thay đổi.
            # Phải đọc trước khi lưu để không thể chuyển phiếu sang hợp đồng
            # khác rồi dùng hợp đồng mới để né điều kiện khóa.
            locked_values = {
                "amount": payment.amount,  # Số tiền đã xác nhận.
                "customer_id": payment.customer_id.id,  # Mã khách hàng; .id lấy mã số bản ghi trong database.
                "contract_id": payment.contract_id.id,  # Mã hợp đồng đang liên kết với phiếu tiền.
                "transaction_type": payment.transaction_type,  # Loại giao dịch: cọc/thuê/hoàn/thu thêm.
                "currency_id": payment.currency_id.id,  # Đồng tiền; đổi đồng tiền cũng làm sai ý nghĩa số tiền.
                "state": payment.state,  # Khóa trạng thái để không hủy hoặc đưa phiếu về nháp.
                "payment_date": fields.Date.to_string(payment.payment_date),  # Khóa ngày thu/hoàn đã ghi nhận.
                "payment_method": payment.payment_method,  # Khóa phương thức khách đã trả hoặc được hoàn tiền.
                "reference": payment.reference or False,  # Khóa mã tham chiếu của giao dịch.
                "invoice_id": payment.invoice_id.id or False,  # Khóa hóa đơn liên kết với phiếu tiền.
            }

            # items() lấy từng cặp tên trường và giá trị trong dictionary.
            # Python tách mỗi cặp thành hai biến:
            # field_name là tên trường; current_value là giá trị hiện tại.
            for field_name, current_value in locked_values.items():

                # "in vals" kiểm tra lần lưu này có gửi trường đó lên không.
                # Chỉ chặn nếu giá trị mới thực sự khác giá trị hiện tại.
                # Gửi lại cùng một giá trị thì không bị coi là sửa.
                if field_name in vals and vals[field_name] != current_value:
                    # raise phát sinh lỗi có chủ đích; dừng trước khi Odoo ghi thay đổi.
                    raise UserError("Phiếu tiền đã chốt; chỉ được sửa ghi chú.")  # Báo ngắn gọn quy tắc áp dụng cho mọi trường đã khóa.

        # super() gọi hàm lưu dữ liệu sẵn có của Odoo.
        # Chỉ chạy tới đây khi không có thay đổi bị cấm ở tất cả phiếu đang sửa.
        # Trường note (ghi chú) không nằm trong danh sách khóa nên vẫn lưu được.
        return super().write(vals)

    def unlink(self):  # Chặn xóa phiếu đã xác nhận để không mất dấu vết tiền thuê, cọc và khoản hoàn.
        if self.filtered(lambda payment: payment.state == "confirmed"):  # Trong tập sắp xóa có ít nhất một phiếu đã chốt.
            raise UserError("Phiếu tiền đã xác nhận không được xóa; bạn vẫn có thể sửa ghi chú.")  # Dừng trước khi xóa bất kỳ phiếu nào.
        return super().unlink()  # Chỉ phiếu chưa xác nhận mới đi qua quy tắc xóa sẵn có của Odoo.

    # 5. Các hàm tính toán ( @api.depends , @api.onchange )

    # @api.onchange là khai báo yêu cầu Odoo chạy hàm khi người dùng đổi trường trên form.
    # Đổi hợp đồng hoặc loại giao dịch đều cần lấy lại thông tin và số tiền tương ứng.
    # Hàm này điền dữ liệu trên màn hình; Odoo chỉ lưu khi nhân viên bấm Lưu.
    # Các luồng tạo tiền bằng code (tự tạo cọc/xác nhận hóa đơn) vẫn truyền giá trị như trước.
    @api.onchange("contract_id", "transaction_type")
    def _onchange_contract_payment(self):  # Tự điền khách hàng, đồng tiền và số tiền theo hợp đồng cùng loại giao dịch được chọn.
        # self là bản ghi thanh toán đang hiển thị trên form Odoo.
        # contract là biến giữ đối tượng hợp đồng nhân viên vừa chọn, không chỉ mã số hợp đồng.
        contract = self.contract_id

        if not contract:  # not nghĩa là "không có": chưa chọn hoặc vừa bỏ chọn hợp đồng.
            self.customer_id = False  # False xóa liên kết khách cũ, tránh giữ nhầm khách của hợp đồng trước.
            # env là môi trường Odoo; env.company là công ty đang thao tác.
            # Khi chưa có hợp đồng thì tạm dùng đồng tiền công ty, không giữ đồng tiền hợp đồng cũ.
            self.currency_id = self.env.company.currency_id
            self.amount = 0.0  # Chưa có hợp đồng thì chưa xác định được số tiền cần thu/hoàn.
            return  # Dừng hàm tại đây, không chạy các nhánh lấy dữ liệu hợp đồng bên dưới.

        # Các trường Many2one lưu liên kết tới bản ghi khác, ví dụ khách hàng và đồng tiền.
        # Gán đối tượng tương ứng từ hợp đồng để Odoo tự hiển thị tên khách/tên tiền tệ.
        self.customer_id = contract.customer_id  # Lấy khách của hợp đồng, không cho nhân viên gõ lại tên.
        self.currency_id = contract.currency_id  # Lấy đúng đồng tiền dùng trên hợp đồng.

        # == là phép so sánh bằng; dấu = ở dòng gán self.amount là phép gán giá trị.
        if self.transaction_type == "deposit":  # deposit là tên kỹ thuật của giao dịch thu tiền cọc.
            self.amount = contract.deposit_amount  # Lấy nguyên số cọc yêu cầu trên hợp đồng.

        elif self.transaction_type == "rental_payment":  # elif nghĩa là "nếu không thì kiểm tra điều kiện tiếp".
            self.amount = contract.total_amount  # Thu toàn bộ tiền thuê ghi trên hợp đồng.

        elif self.transaction_type == "refund":  # refund là giao dịch hoàn tiền cho khách.
            if contract.state == "confirmed":  # Đã ký nhưng chưa giao xe: chỉ hoàn khoản cọc ghi trên hợp đồng.
                self.amount = contract.deposit_amount  # Giữ toàn bộ tiền thuê đã nhận; không hoàn tiền thuê.
            else:  # Đang thuê: tiền cần hoàn do hóa đơn và các khoản phụ phí quyết định.
                self.amount = max(-contract.settlement_balance, 0.0)  # Đổi số dư âm thành số tiền hoàn dương.

        elif self.transaction_type == "additional_payment":  # additional_payment là giao dịch thu thêm.
            # Số dư dương là khách còn thiếu tiền; số dư âm nghĩa là không có khoản cần thu thêm.
            self.amount = max(contract.settlement_balance, 0.0)

        else:  # else là nhánh còn lại: chưa chọn loại giao dịch nên chưa biết phải lấy khoản tiền nào.
            self.amount = 0.0  # Xóa số cũ để không giữ nhầm tiền của loại giao dịch trước.

    # 6. Các hàm Action / Nghiệp vụ (nút bấm button)
    
    def action_confirm(self):  # Xác nhận phiếu tiền; phiếu hoàn cọc trước giao xe sẽ tự hủy hợp đồng sau khi hoàn.
        for record in self:  # Xử lý từng phiếu được chọn trên màn hình Finance hoặc hợp đồng.
            contract = record.contract_id  # Giữ hợp đồng liên kết để kiểm tra nhánh hoàn cọc.
            if record.transaction_type == "refund" and contract.state == "confirmed":  # Đây là trường hợp khách hủy sau ký, trước giao xe.
                contract._check_cancel_before_delivery()  # Kiểm tra lại ngay lúc xác nhận, phòng khi xe vừa được giao.
                deposits = contract.payment_ids.filtered(lambda payment: payment.transaction_type == "deposit" and payment.state == "confirmed")  # Tìm cọc thực tế đã thu.
                if len(deposits) != 1:  # Thiếu hoặc trùng phiếu cọc thì chưa biết khoản cần hoàn.
                    raise UserError("Hợp đồng phải có đúng một phiếu cọc đã xác nhận trước khi hoàn.")  # Dừng trước khi ghi nhận hoàn tiền.
                if record.customer_id != contract.customer_id or record.currency_id != contract.currency_id:  # Phiếu phải thuộc đúng khách và đồng tiền của hợp đồng.
                    raise UserError("Khách hàng hoặc đồng tiền trên phiếu hoàn không khớp hợp đồng.")  # Không hoàn sai người hoặc sai loại tiền.
                if not contract.currency_id.is_zero(record.amount - contract.deposit_amount):  # So sánh theo độ làm tròn của đồng tiền.
                    raise UserError("Phải hoàn đúng toàn bộ tiền cọc của hợp đồng.")  # Không hoàn thiếu hoặc vượt cọc.
                other_refunds = contract.payment_ids.filtered(lambda payment: payment.transaction_type == "refund" and payment.state == "confirmed" and payment != record)  # Tìm phiếu hoàn khác đã chốt.
                if other_refunds:  # Đã hoàn một lần thì không được ghi nhận lần hai.
                    raise UserError("Hợp đồng đã có phiếu hoàn cọc được xác nhận.")  # Tránh hoàn trùng.
                record.state = "confirmed"  # Chỉ chốt phiếu sau khi nhân viên đã hoàn cọc thực tế.
                contract.write({"state": "cancelled", "settlement_status": "settled"})  # Hoàn xong mới hủy hợp đồng; tiền thuê vẫn giữ nguyên.
            else:  # Các phiếu khác tiếp tục dùng quy trình xác nhận hiện có.
                record.state = "confirmed"  # Phiếu cọc/thuê cần dấu từ nút Ký hợp đồng; hóa đơn dùng luồng riêng.

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
    
    def action_draft(self):
        for record in self:
            record.state = 'draft'  
          
          
            
    @api.model
    def _initialize_payment_sequences(self):  # Đặt bộ cấp số tiếp nối số thứ tự lớn nhất trong mã cũ khi cài hoặc cập nhật module.
        # @api.model cho biết hàm làm việc ở cấp model, không cần chọn một phiếu tiền cụ thể.
        # Hàm được gọi từ XML cấu hình, không chạy lại mỗi lần nhân viên tạo thanh toán.
        # Mã bắt đầu bằng dấu _ là hàm nội bộ; không phải nút cho người dùng gọi trên form.

        # Dictionary ánh xạ tiền tố mã sang XML ID của bộ cấp số tương ứng.
        # XML ID là tên định danh bản ghi cấu hình trong file rental_payment_sequence.xml.
        sequence_ids = {
            "DP": "seq_rental_payment_deposit",  # Bộ cấp số cho tiền cọc.
            "RP": "seq_rental_payment_rental",  # Bộ cấp số cho tiền thuê.
            "RF": "seq_rental_payment_refund",  # Bộ cấp số cho tiền hoàn.
            "AP": "seq_rental_payment_additional",  # Bộ cấp số cho tiền thu thêm.
        }

        # sudo chỉ dùng để đọc đủ mã cũ khi cấu hình bộ đếm, không sửa các bản ghi tiền cũ.
        payments = self.sudo()
        for prefix, xml_id in sequence_ids.items():  # items() lấy từng cặp (tiền tố, XML ID) trong dictionary.
            # env.ref tìm bản ghi bằng XML ID đầy đủ: tên_module.tên_bản_ghi.
            sequence = self.env.ref("motorbike_rental_finance.%s" % xml_id).sudo()

            # Biểu thức mẫu nhận dạng mã như DP-20261020-015.
            # [0-9]{8} là đúng 8 chữ số của ngày; ([0-9]+) là nhóm số thứ tự cuối mã.
            # Chữ r trước chuỗi là cách viết chuỗi nguyên gốc dùng cho biểu thức mẫu.
            pattern = re.compile(prefix + r"-[0-9]{8}-([0-9]+)")
            largest_number = 0  # Chưa thấy mã cũ thì coi số lớn nhất đã dùng là 0.

            # =like tìm chuỗi theo mẫu; dấu % nghĩa là phần ký tự còn lại có thể bất kỳ.
            # Tìm theo tiền tố mã, không lọc trạng thái: phiếu đã hủy cũng không được cấp lại mã.
            for payment in payments.search([("name", "=like", prefix + "-%")]):
                # fullmatch chỉ chấp nhận khi toàn bộ mã đúng mẫu; bỏ qua mã đặt tay theo định dạng khác.
                match = pattern.fullmatch(payment.name or "")
                if match:
                    # group(1) lấy phần số thứ tự đã đánh dấu bằng ngoặc; int chuyển chuỗi thành số nguyên.
                    # max giữ số lớn nhất trên tất cả ngày, vì bộ đếm mới không đặt lại mỗi ngày.
                    largest_number = max(largest_number, int(match.group(1)))

            # Xóa giá trị tạm trong cache để Odoo đọc đúng số tiếp theo của bộ đếm trong database.
            sequence.invalidate_recordset(["number_next_actual"])
            # Chỉ tăng nếu cần, không bao giờ đặt bộ đếm lùi về số đã dùng.
            if sequence.number_next_actual <= largest_number:
                sequence.write({"number_next_actual": largest_number + 1})

    # model_create_multi cho phép Odoo tạo nhiều thanh toán trong một lần gọi hàm.
    @api.model_create_multi
    def create(self, vals_list):  # Chặn phiếu mới cho hợp đồng đã hủy/hoàn tất, kiểm tra tiền thuê và tự cấp mã phiếu.
        # Kiểm tra trước khi cấp mã và tạo bản ghi thanh toán.
        for vals in vals_list:
            # browse lấy hợp đồng theo mã số; chưa chọn thì trả tập rỗng.
            contract = self.env["rental.contract"].browse(vals.get("contract_id"))
            # Nếu hợp đồng đã hủy, không tạo thêm bất kỳ phiếu tiền nào gắn với hợp đồng đó.
            if contract.state == "cancelled":
                raise UserError("Không thể tạo phiếu tiền cho hợp đồng đã hủy.")  # Dừng trước khi lưu phiếu mới.
            # Chỉ kiểm tra hai khoản thu ban đầu nếu phiếu gắn với một hợp đồng.
            if contract:
                # Lấy loại giao dịch mà người dùng hoặc hệ thống đang tạo.
                transaction_type = vals.get("transaction_type")
                # Tiền cọc và tiền thuê phải được lập lúc hợp đồng còn nháp.
                if transaction_type in ("deposit", "rental_payment") and contract.state != "draft":
                    # Sau khi ký hoặc bắt đầu thuê, không sinh thêm phiếu thu ban đầu.
                    raise UserError("Chỉ được tạo phiếu cọc và phiếu thu tiền thuê khi hợp đồng còn nháp.")
            if contract.state == "done":
                raise UserError("Hợp đồng đã hoàn tất, không thể tạo thêm thanh toán.")

        # vals_list là danh sách dictionary; mỗi dictionary chứa thông tin một bản ghi cần tạo.
        # Mỗi loại giao dịch dùng bộ đếm riêng, khớp code cấu hình trong file XML.
        sequence_codes = {
            "deposit": "motorbike.rental.payment.deposit",
            "rental_payment": "motorbike.rental.payment.rental",
            "refund": "motorbike.rental.payment.refund",
            "additional_payment": "motorbike.rental.payment.additional",
        }

        # set() tạo tập hợp giá trị không trùng nhau; dùng để giữ các mã trong cùng lần tạo.
        # Tập hợp này tính cả mã truyền sẵn từ dữ liệu mẫu hoặc nhập dữ liệu.
        reserved_names = set()
        for vals in vals_list:
            if vals.get("name") and vals["name"] != "/":
                reserved_names.add(vals["name"])  # add đưa mã đã có vào tập mã cần tránh cấp trùng.

        # Bộ cấp số chuẩn có quyền đọc cho người dùng nội bộ; không nâng quyền để cấp số mới.
        sequences = self.env["ir.sequence"]
        for vals in vals_list:
            # Có mã cụ thể thì giữ nguyên, ví dụ mã của bản ghi mẫu khi cập nhật module.
            # Không đổi mã cũ và không cấp lại mã cho bản ghi đã có tên.
            if vals.get("name") and vals["name"] != "/":
                continue

            # get lấy code bộ cấp số từ loại giao dịch; không tìm thấy thì trả về None.
            sequence_code = sequence_codes.get(vals.get("transaction_type"))
            if not sequence_code:
                raise ValidationError("Vui lòng chọn loại giao dịch thanh toán hợp lệ.")

            # to_date đổi chuỗi YYYY-MM-DD hoặc giá trị ngày thành đối tượng ngày Python.
            # Nếu chưa truyền ngày thì dùng ngày hiện tại theo múi giờ của người dùng Odoo.
            payment_date = fields.Date.to_date(vals.get("payment_date")) or fields.Date.context_today(self)

            # with_context bổ sung thông tin cho riêng lần gọi bộ cấp số này.
            # ir_sequence_date khiến phần YYYYMMDD trong tiền tố lấy từ ngày thanh toán,
            # kể cả khi nhập một giao dịch của ngày trước; không lấy nhầm ngày hôm nay.
            dated_sequences = sequences.with_context(ir_sequence_date=fields.Date.to_string(payment_date))

            # while True lặp cho tới khi tìm được mã chưa sử dụng; break ở dưới sẽ kết thúc vòng lặp.
            while True:
                # next_by_code xin số tiếp theo từ bộ cấp số chuẩn của Odoo/PostgreSQL.
                # Hai nhân viên gọi cùng lúc sẽ được cấp hai số khác nhau.
                payment_name = dated_sequences.next_by_code(sequence_code, sequence_date=payment_date)
                if not payment_name:
                    raise UserError("Chưa có cấu hình cấp mã thanh toán. Vui lòng cập nhật module Finance.")

                # Kiểm tra thêm mã cũ hoặc mã truyền sẵn, không dùng phép đếm + 1 để sinh số nữa.
                # sudo chỉ để nhìn thấy mã đã tồn tại dù bản ghi đó bị giới hạn quyền đọc.
                # reserved_names còn ngăn trùng với bản ghi chưa được lưu trong cùng vals_list.
                if (
                    payment_name not in reserved_names
                    and not self.sudo().search_count([("name", "=", payment_name)])
                ):
                    break  # Mã chưa được dùng, có thể đưa vào bản ghi mới.

            vals["name"] = payment_name  # Gán mã mới vào dữ liệu sẽ lưu.
            reserved_names.add(payment_name)  # Giữ mã này để các bản ghi còn lại trong lần tạo không dùng lại.

        # super() tạo bản ghi theo cách chuẩn của Odoo, vẫn kiểm tra quyền và các ràng buộc số tiền.
        # Bộ cấp số standard có thể bỏ qua một số nếu thao tác bị lỗi/hoàn tác, nhưng không cấp lại số đó.
        return super().create(vals_list)
