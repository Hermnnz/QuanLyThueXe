    # 1. Đầu file: Các dòng import
import re  # re cung cấp công cụ nhận diện mẫu chuỗi, dùng để đọc số thứ tự trong mã thanh toán cũ.

from odoo import api, fields, models
# UserError dùng để dừng thao tác và hiện thông báo cho nhân viên.
from odoo.exceptions import UserError, ValidationError

# Dấu riêng cho luồng hóa đơn: object() tạo một đối tượng duy nhất trong bộ nhớ.
# Người dùng không thể tự truyền đúng đối tượng này từ giao diện để tạo phiếu thu/hoàn.
_INVOICE_SETTLEMENT = object()


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

    # constrains chạy khi tạo phiếu hoặc thay đổi loại giao dịch/trạng thái.
    @api.constrains("transaction_type", "state")
    def _check_invoice_settlement(self):  # Chỉ cho luồng hóa đơn ghi nhận phiếu thu thêm/hoàn tiền.
        for payment in self:  # Kiểm tra từng phiếu đang được lưu.
            if payment.transaction_type in ("refund", "additional_payment"):
                # context chứa thông tin truyền riêng cho thao tác đang chạy.
                # is not kiểm tra có đúng đối tượng nhận diện của luồng hóa đơn hay không.
                if self.env.context.get("_invoice_settlement") is not _INVOICE_SETTLEMENT:
                    raise UserError("Hãy xác nhận thu/hoàn tiền trên hóa đơn cuối hợp đồng.")

    def write(self, vals):  # Chặn chuyển phiếu vào hợp đồng hoàn tất, khóa cọc/tiền thuê đã xác nhận từ khi ký và khóa mọi phiếu đã xác nhận khi hoàn tất.
        # write là hàm Odoo gọi khi lưu thay đổi vào bản ghi đã tồn tại.
        # self là các phiếu tiền đang được sửa, có thể gồm nhiều phiếu.
        #
        # vals là dictionary: tập các cặp tên trường và giá trị mới.
        # Ví dụ {"amount": 500000} nghĩa là muốn đổi số tiền thành 500.000.

        # Chỉ kiểm tra khi dữ liệu lưu có chọn hợp đồng đích.
        if vals.get("contract_id"):
            # browse lấy bản ghi hợp đồng theo ID (mã số trong database).
            contract = self.env["rental.contract"].browse(vals["contract_id"])

            for record in self:  # Kiểm tra từng phiếu đang được sửa.
                # Chặn chuyển sang hợp đồng đã hoàn tất; giữ nguyên hợp đồng thì cho qua.
                if record.contract_id != contract and contract.state == "done":
                    raise UserError("Không thể chuyển phiếu vào hợp đồng đã hoàn tất.")

        for payment in self:  # Lần lượt kiểm tra từng phiếu đang được sửa.

            # Khóa mọi phiếu đã xác nhận khi hợp đồng hoàn tất (done).
            # Với cọc/tiền thuê, khóa sớm hơn: ngay khi hợp đồng đã ký (confirmed)
            # hoặc đang thuê (in_progress), vì các phiếu này chứng minh đã thu đủ tiền để ký.
            # or nghĩa là "hoặc", and nghĩa là "và"; in kiểm tra giá trị có trong nhóm hay không.
            locked_contract = (
                payment.contract_id.state == "done"
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
                    raise UserError(
                        "Phiếu tiền đã được chốt theo hợp đồng, "
                        "không được đổi số tiền, khách hàng, hợp đồng, "
                        "loại giao dịch, đồng tiền hoặc trạng thái. "
                        "Bạn vẫn có thể chỉnh sửa ghi chú."
                    )

        # super() gọi hàm lưu dữ liệu sẵn có của Odoo.
        # Chỉ chạy tới đây khi không có thay đổi bị cấm ở tất cả phiếu đang sửa.
        # Trường note (ghi chú) không nằm trong danh sách khóa nên vẫn lưu được.
        return super().write(vals)

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
            # settlement_balance là số dư: âm nghĩa là đang giữ dư tiền của khách và cần hoàn.
            # Dấu trừ phía trước đảo số âm thành số dương để ghi số tiền trên phiếu.
            # max(a, b) lấy số lớn hơn: nếu không cần hoàn thì kết quả là 0, không tạo số tiền âm.
            self.amount = max(-contract.settlement_balance, 0.0)

        elif self.transaction_type == "additional_payment":  # additional_payment là giao dịch thu thêm.
            # Số dư dương là khách còn thiếu tiền; số dư âm nghĩa là không có khoản cần thu thêm.
            self.amount = max(contract.settlement_balance, 0.0)

        else:  # else là nhánh còn lại: chưa chọn loại giao dịch nên chưa biết phải lấy khoản tiền nào.
            self.amount = 0.0  # Xóa số cũ để không giữ nhầm tiền của loại giao dịch trước.

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
    def create(self, vals_list):  # Chặn thêm thanh toán cho hợp đồng hoàn tất và tự cấp mã theo loại giao dịch, ngày thanh toán.
        # Kiểm tra trước khi cấp mã và tạo bản ghi thanh toán.
        for vals in vals_list:
            # browse lấy hợp đồng theo mã số; chưa chọn thì trả tập rỗng.
            contract = self.env["rental.contract"].browse(vals.get("contract_id"))
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
