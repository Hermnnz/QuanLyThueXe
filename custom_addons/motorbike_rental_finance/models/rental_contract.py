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
    
   

    def action_settlement(self):
        #Hàm tự động quyết toán khi trả xe: Tiền xe + Tiền phạt so với Tiền cọc
        for contract in self:
            # 1. Tiền thuê xe gốc
            rent_fee = contract.total_amount or 0.0
            
            # 2. Tổng tiền phạt/phụ phí (chỉ tính những khoản đã xác nhận)
            penalties = sum(contract.charge_ids.filtered(lambda c: c.state == 'confirmed').mapped('amount'))
            
            # 3. Tiền cọc ban đầu
            deposit = contract.deposit_amount or 0.0

            # 4. Tính chênh lệch: (Tiền xe + Phạt) - Cọc
            balance = (rent_fee + penalties) - deposit

            # GỢI Ý ĐẾN ĐÂY:
            
            if balance < 0:
                # Thối tiền thừa cho khách
                payment = self.env['motorbike.rental.payment'].create({
                    'name': f"RF-{fields.Date.today()}-{contract.id}",
                    'customer_id': contract.customer_id.id,
                    'contract_id': contract.id,
                    'transaction_type': 'refund',
                    'amount': abs(balance),
                    'currency_id': contract.currency_id.id,
                    'payment_method': 'cash',  # Hoặc phương thức khác tùy nhu cầu
                    'payment_date': fields.Date.today(),
                })
                return {
                    'name': 'Phiếu thanh toán quyết toán',
                    'type': 'ir.actions.act_window',
                    'res_model': 'motorbike.rental.payment',
                    'res_id': payment.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            elif balance > 0:
                # Thu thêm phần thiếu
                payment = self.env['motorbike.rental.payment'].create({
                    'name': f"AP-{fields.Date.today()}-{contract.id}",
                    'customer_id': contract.customer_id.id,
                    'contract_id': contract.id,
                    'transaction_type': 'additional_payment',
                    'amount': balance,
                    'currency_id': contract.currency_id.id,
                    'payment_method': 'cash',  # Hoặc phương thức khác tùy nhu cầu
                    'payment_date': fields.Date.today(),
                })
                return {
                    'name': 'Phiếu thanh toán quyết toán',
                    'type': 'ir.actions.act_window',
                    'res_model': 'motorbike.rental.payment',
                    'res_id': payment.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            else:
                # Báo thông báo đã cấn trừ vừa đủ
              return {
                  'type': 'ir.actions.client',
                  'tag': 'display_notification',
                  'params': {
                      'title': 'Quyết toán hoàn tất',
                      'message': 'Đã đủ, không cần thanh toán thêm hay hoàn tiền.',
                      'type': 'success',
                      'sticky': False,
                  }
              }