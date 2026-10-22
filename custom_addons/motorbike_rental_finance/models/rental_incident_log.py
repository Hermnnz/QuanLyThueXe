# -*- coding: utf-8 -*-
from odoo import api, fields, models
# UserError dừng thao tác và hiện thông báo cho nhân viên.
from odoo.exceptions import UserError

class RentalIncidentLog(models.Model):
    _inherit = 'rental.operation.incident.log'

    # Trường lưu vết khoản tiền phạt đã sinh ra
    charge_id = fields.Many2one(
        'motorbike.rental.charge',
        string='Khoản phụ phí bồi thường',
        readonly=True,   # Khong cho phép gõ tay
        copy=False,     # Không copy khi duplicate biên bản sự cố
    )

    # BẮT SỰ KIỆN: Lắng nghe mỗi khi có bản ghi Sự cố được tạo ra
    @api.model_create_multi
    def create(self, vals_list):
        # 1. Để cho Giang tạo biên bản sự cố bình thường trước
        records = super().create(vals_list)

        # 2. Finance tự động lắng nghe và bốc dữ liệu sang bảng của mình
        for incident in records:
            # Lấy số tiền phạt: Giang đã đổi 'cost' thành 'penalty_amount'
            penalty = incident.penalty_amount or (incident.price_catalog_id.unit_price if incident.price_catalog_id else 0.0)

            # Điều kiện: Có tiền phạt và lỗi do khách hàng
            if incident.fault_party == 'customer' and penalty > 0:
                ticket = incident.ticket_id
                contract = ticket.contract_id if ticket else False
                customer = contract.customer_id if contract else False

                if customer:
                    charge_name = f"{incident.price_catalog_id.name}: {incident.name}" if incident.price_catalog_id else f"Phạt sự cố: {incident.name}"
                    
                    # Bắn sang bảng motorbike.rental.charge
                    charge = self.env['motorbike.rental.charge'].create({
                        'name': charge_name,
                        'customer_id': customer.id,
                        'contract_id': contract.id if contract else False,
                        'currency_id': contract.currency_id.id,  # Lấy đồng tiền của hợp đồng.
                        'ticket_id': ticket.id if ticket else False,
                        'incident_id': incident.id,
                        'price_catalog_id': incident.price_catalog_id.id if incident.price_catalog_id else False,
                        'quantity': 1.0,
                        'unit_price': penalty,
                        'charge_date': fields.Date.context_today(self),
                        'state': 'draft', # Để ở bản Nháp cho Kế toán duyệt
                        'note': f"Mô tả sự cố: {incident.damage_description or 'Không có mô tả'}",
                    })
                    # Lưu lại ID để biết sự cố này đã tạo khoản phí nào
                    incident.charge_id = charge.id

        return records

    def write(self, vals):  # Đồng bộ tiền phạt sang phụ phí nháp và chặn đổi tiền khi phụ phí đã chốt.
        # self là tập các sự cố đang được sửa.
        # vals là dictionary chứa tên trường và giá trị mới.
        # Ví dụ {"penalty_amount": 500000} là đổi tiền phạt thành 500.000.

        # Danh sách lưu những khoản phí cần cập nhật sau khi lưu sự cố.
        # [] là danh sách Python rỗng.
        charges_to_update = []

        # Chỉ kiểm tra số tiền nếu lần lưu này có sửa trường tiền phạt.
        if "penalty_amount" in vals:
            for incident in self:  # Lần lượt kiểm tra từng sự cố.
                charge = incident.charge_id  # Khoản phụ phí đã liên kết với sự cố.

                # Chưa có khoản phí liên kết thì không có bản ghi để đồng bộ.
                if not charge:
                    continue  # Bỏ qua sự cố này, chuyển sang sự cố tiếp theo.

                # Gửi lại cùng số tiền thì không phải thay đổi.
                # == là phép so sánh bằng, khác dấu = dùng để gán giá trị.
                if vals["penalty_amount"] == incident.penalty_amount:
                    continue

                # confirmed là Đã xác nhận.
                # invoice_id có giá trị nghĩa là phí đã gắn với một hóa đơn.
                # or nghĩa là "hoặc": chỉ cần một điều kiện đúng thì phải chặn.
                if charge.state == "confirmed" or charge.invoice_id:
                    raise UserError(
                        "Không thể sửa tiền phạt vì khoản phụ phí "
                        "đã được xác nhận hoặc đã gắn với hóa đơn."
                    )

                # Chỉ khoản phí nháp mới được cập nhật tiền.
                # Khoản phí đã hủy giữ nguyên lịch sử.
                if charge.state == "draft":
                    # append thêm một phần tử vào danh sách.
                    # Mỗi phần tử là một tuple: cặp (khoản phí, số tiền mới).
                    charges_to_update.append(
                        (charge, vals["penalty_amount"])
                    )

        # super() gọi cách lưu sự cố sẵn có của Odoo/Operations.
        # Phải kiểm tra ở phía trên trước khi gọi để không lưu số tiền bị cấm.
        result = super().write(vals)

        if "fault_party" in vals:  # Chỉ xử lý khi người vận hành đổi bên chịu lỗi.
            for incident in self:  # Một lần lưu có thể sửa nhiều sự cố.
                charge = incident.charge_id  # Lấy phụ phí đang liên kết với sự cố.
                if incident.fault_party != "customer" and charge and charge.state != "cancelled":  # Lỗi công ty có phí chưa hủy.
                    if charge.state != "draft" or charge.invoice_id:  # Phí đã chốt không được tự đổi thành 0đ.
                        raise UserError("Phụ phí đã chốt, không thể đổi bên chịu lỗi.")  # Lỗi sẽ hoàn tác cả thay đổi bên chịu lỗi.
                    charge.action_cancel()  # Hủy phí nháp; khoản khách bị trừ từ sự cố này trở thành 0đ.

        # Python tách từng cặp đã lưu thành hai biến:
        # charge là khoản phụ phí; new_amount là số tiền phạt mới.
        for charge, new_amount in charges_to_update:

            # Mỗi sự cố được ghi thành một khoản phí, giống lúc tự tạo phí.
            # Thành tiền = số lượng 1 × đơn giá bằng tiền phạt mới.
            charge.write({
                "quantity": 1.0,  # Một khoản bồi thường cho sự cố này.
                "unit_price": new_amount,  # Đơn giá mới, ví dụ 500.000.
            })

            # Không cần tự gán charge.amount.
            # Đây là trường compute: Odoo tự tính lại khi quantity/unit_price đổi.

        if {"quantity", "unit_price", "price_catalog_id"} & vals.keys():  # Nếu lần lưu có đổi số lượng, đơn giá hoặc bảng giá.
            for incident in self:  # Xử lý lần lượt từng sự cố đang được lưu.
                charge = incident.charge_id  # Lấy phụ phí Finance đã tạo cho sự cố này.
                if not charge or charge.state == "cancelled":  # Không có phí hoặc phí đã hủy thì bỏ qua.
                    continue  # Chuyển sang sự cố tiếp theo.

                amount = incident.penalty_amount  # Lấy tiền phạt mới mà Operations vừa tính lại.
                if incident.currency_id.is_zero(amount - charge.amount):  # So sánh hai số tiền theo cách làm tròn của đồng tiền.
                    continue  # Tiền không đổi nên không cần sửa phụ phí.

                if charge.state != "draft" or charge.invoice_id:  # Phí đã chốt hoặc đã gắn hóa đơn thì không cho đổi.
                    raise UserError("Phụ phí đã chốt, không thể đổi tiền phạt.")  # Báo lỗi và dừng lần lưu.

                if incident.currency_id.is_zero(amount):  # Nếu tiền phạt mới bằng 0.
                    charge.action_cancel()  # Hủy phụ phí nháp nhưng giữ lại phiếu để xem lịch sử.
                else:  # Nếu vẫn còn tiền cần thu.
                    charge.write({"quantity": 1.0, "unit_price": amount})  # Cập nhật phụ phí bằng đúng tiền phạt mới.

        # Giữ cơ chế đồng bộ trạng thái đang có.
        # Chỉ chạy khi lần lưu này có thay đổi trạng thái sự cố.
        if "status" in vals:
            for incident in self:
                charge = incident.charge_id

                if not charge:  # Không có khoản phí thì không cần đổi trạng thái phí.
                    continue

                # resolved nghĩa là sự cố Đã giải quyết.
                # Khi đó chuyển khoản phụ phí nháp sang Đã xác nhận.
                if incident.status == "resolved" and charge.state == "draft":
                    charge.state = "confirmed"

                # elif là nhánh kiểm tra tiếp khi điều kiện phía trên không đúng.
                # Nếu sự cố không còn Đã giải quyết thì đưa phí đã xác nhận về nháp,
                # giữ nguyên hành vi hiện có của hệ thống.
                elif incident.status != "resolved" and charge.state == "confirmed":
                    charge.state = "draft"

        # Trả nguyên kết quả lưu của Odoo.
        return result
