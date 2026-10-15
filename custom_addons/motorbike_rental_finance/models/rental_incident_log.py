# -*- coding: utf-8 -*-
from odoo import api, fields, models

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
            # Điều kiện: Có tiền phạt và lỗi do khách hàng
            if incident.fault_party == 'customer' and incident.cost > 0:
                ticket = incident.ticket_id
                contract = ticket.contract_id if ticket else False
                customer = contract.customer_id if contract else False

                if customer:
                    # Bắn sang bảng motorbike.rental.charge của bạn
                    charge = self.env['motorbike.rental.charge'].create({
                        'name': f"{incident.price_catalog_id.name}: {incident.name}",
                        'customer_id': customer.id,
                        'contract_id': contract.id if contract else False,
                        'ticket_id': ticket.id if ticket else False,
                        'incident_id': incident.id,
                        'quantity': 1.0,
                        'unit_price': incident.cost,
                        'charge_date': fields.Date.context_today(self),
                        'state': 'draft', # Để ở bản Nháp cho Kế toán duyệt
                        'note': f"Mô tả sự cố: {incident.damage_description or 'Không có mô tả'}",
                    })
                    # Lưu lại ID để biết sự cố này đã tạo khoản phí nào
                    incident.charge_id = charge.id

        return records