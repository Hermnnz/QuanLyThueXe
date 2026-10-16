from odoo import api, fields, models
from odoo.exceptions import UserError

class RentalContract(models.Model):
    _inherit = "rental.contract"

    # Nối ngược các khoản phí và thanh toán của hợp đồng này
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
    
    settlement_status = fields.Selection([
        ('unsettled', 'Chưa quyết toán'),
        ('settled', 'Đã quyết toán'),
    ], string='Trạng thái quyết toán', default='unsettled', readonly=True, copy=False)
    
   

    def action_settlement(self):
        self.ensure_one()

        # 1. Chống bấm trùng & kiểm tra phụ phí chưa duyệt
        if self.settlement_status == 'settled':
            raise UserError("Hợp đồng này đã được quyết toán rồi!")

        draft_charges = self.charge_ids.filtered(lambda c: c.state == 'draft')
        if draft_charges:
            raise UserError(
                "Vẫn còn khoản phụ phí/phạt đang ở trạng thái Nháp. "
                "Vui lòng xác nhận hoặc hủy các khoản phí này trước khi quyết toán!"
            )

        # 2. Tính toán số tiền: (Tiền xe + Phạt đã xác nhận) - Cọc
        rent_fee = self.total_amount or 0.0  #tiền thuê xe gốc, nếu false hoặc none thì mặc định 0.0
        
        
        # Lọc ra các khoản phụ phí đã được xác nhận và Gom toàn bộ số tiền của các khoản phí đã duyệt thành 1 danh sách
        penalties = sum(self.charge_ids.filtered(lambda c: c.state == 'confirmed').mapped('amount'))
        
        deposit = self.deposit_amount or 0.0
        
        balance = (rent_fee + penalties) - deposit

        # Đánh dấu hợp đồng đã quyết toán
        self.settlement_status = 'settled'

        # 3. Xử lý khi số dư bằng 0 (Dùng is_zero của tiền tệ để tránh sai số float)
        if self.currency_id.is_zero(balance):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Quyết toán hoàn tất',
                    'message': 'Đã cấn trừ vừa đủ giữa tiền thuê và tiền cọc, không cần thu thêm hay hoàn tiền.',
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},  # Tự động làm mới giao diện
                }
            }

        # 4. Phân nhánh tạo phiếu Hoàn tiền (balance < 0) hoặc Thu thêm (balance > 0)
        tx_type = 'refund' if balance < 0 else 'additional_payment'
        payment = self.env['motorbike.rental.payment'].create({
            'customer_id': self.customer_id.id,
            'contract_id': self.id,
            'transaction_type': tx_type,
            'amount': abs(balance),
            'currency_id': self.currency_id.id,
            'payment_method': 'cash',
            'payment_date': fields.Date.context_today(self),
        })

        return {
            'name': 'Phiếu thanh toán quyết toán',
            'type': 'ir.actions.act_window',
            'res_model': 'motorbike.rental.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }