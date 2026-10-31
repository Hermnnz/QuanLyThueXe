from odoo import Command, fields, models  # Tạo dòng hóa đơn, lấy ngày hiện tại và kế thừa model Odoo.


class RentalOperationTicketVehicle(models.Model):
    _inherit = "rental.operation.ticket.vehicle"  # Bổ sung nghiệp vụ Finance vào dòng xe vận hành.

    def write(self, vals):
        """Tạo một hóa đơn nháp khi xác nhận thu hồi xe cuối cùng của hợp đồng."""
        result = super().write(vals)  # Để Operation cập nhật trạng thái xe và phiếu trước.
        if vals.get("status") != "returned":  # Sửa thông tin khác không sinh hóa đơn.
            return result

        for ticket in self.mapped("ticket_id").filtered(lambda t: t.state == "done"):
            contract = ticket.contract_id  # Mỗi phiếu vận hành gắn với một hợp đồng.
            if contract.invoice_ids.filtered(
                lambda inv: inv.move_type == "out_invoice" and inv.state != "cancel"
            ):
                continue  # Đã có hóa đơn còn hiệu lực thì không tạo thêm.

            contract._check_returned_before_invoice()  # Chỉ lập hóa đơn khi đủ xe đã thu hồi.
            charges = contract.charge_ids.filtered(
                lambda c: c.state == "confirmed"
                and (not c.invoice_id or c.invoice_id.state == "cancel")
            )  # Chỉ lấy phụ phí đã duyệt và chưa nằm trên hóa đơn còn hiệu lực.

            lines = [Command.create({
                "name": f"Tiền thuê - {contract.name}",
                "quantity": 1,
                "price_unit": contract.total_amount,
            })]  # Lấy tổng tiền thuê một lần; dòng xe thay thế không cộng thêm tiền.
            lines += [Command.create({
                "name": f"Phụ phí: {c.name}",
                "quantity": c.quantity,
                "price_unit": c.unit_price,
                "charge_id": c.id,
            }) for c in charges]  # Mỗi phụ phí đã duyệt trở thành một dòng hóa đơn.

            self.env["account.move"].create({
                "move_type": "out_invoice",  # Hóa đơn bán hàng cho khách.
                "contract_id": contract.id,  # Liên kết với hợp đồng vừa trả đủ xe.
                "partner_id": contract.customer_id.id,  # Lấy đúng khách của hợp đồng.
                "currency_id": contract.currency_id.id,  # Dùng đồng tiền của hợp đồng.
                "invoice_date": fields.Date.context_today(self),  # Ngày lập theo múi giờ người dùng.
                "invoice_line_ids": lines,  # Gồm tiền thuê và phụ phí đã duyệt.
                "rental_charges_ids": [Command.set(charges.ids)],  # Đánh dấu phụ phí đã đưa vào hóa đơn.
            })  # Hóa đơn mới mặc định ở trạng thái Nháp.
        return result  # Giữ nguyên kết quả của thao tác thu hồi xe.
