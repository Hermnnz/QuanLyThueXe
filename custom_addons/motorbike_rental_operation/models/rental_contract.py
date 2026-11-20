# -*- coding: utf-8 -*-
"""Mở rộng Model Hợp đồng thuê xe (rental.contract) cho module vận hành.

- Khi Hợp đồng được xác nhận (action_confirm -> confirmed):
  + Tự động sinh ra 1 Phiếu vận hành tổng (rental.operation.ticket) ở trạng thái Chưa thực hiện.
  + Tự động nạp toàn bộ danh sách xe trong hợp đồng vào bảng Chi tiết xe vận hành.
- Khi Hợp đồng bị hủy (cancelled):
  + Đồng bộ khóa Phiếu vận hành liên kết sang trạng thái Hợp đồng bị hủy (contract_cancelled).
- Cho phép thêm/xóa dòng xe hợp đồng (rental.contract.line) khi có cờ allow_vehicle_exchange.
"""

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError

class RentalContract(models.Model):
    _inherit = 'rental.contract' # Kế thừa mở rộng
 
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # TỰ ĐỘNG TẠO PHIẾU VẬN HÀNH KHI CÓ HỢP ĐỒNG MỚI ĐƯỢC XÁC NHẬN
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
    def action_confirm(self):
        """Ký hợp đồng thành công rồi tạo một phiếu vận hành Chưa thực hiện."""

        # action_confirm là hàm được viết trong motorbike_rental_core gồm các kiểm tra liên quan, SUPER CHINHS LAF MODEL CORE CHA
        result = super().action_confirm()  # Chỉ tạo phiếu sau khi hợp đồng và hai khoản tiền đã được xác nhận.
        
        Ticket = self.env['rental.operation.ticket']  # Model lưu phiếu vận hành.
        VehicleLine = self.env['rental.operation.ticket.vehicle']  # Lấy model chi tiết xe vận hành

        for contract in self:  # Một thao tác có thể xác nhận nhiều hợp đồng.

            if Ticket.search_count([('contract_id', '=', contract.id)]):
                continue  # Đã có phiếu của hợp đồng này thì không tạo trùng.

            # Đổi giờ thuê của hợp đồng sang múi giờ người dùng để hiển thị trên dòng xe.
            start = fields.Datetime.context_timestamp(contract, contract.start_date) 
            end = fields.Datetime.context_timestamp(contract, contract.end_date)

            Ticket.create({
                'contract_id': contract.id,  # Phiếu gắn với đúng hợp đồng vừa ký.
                'vehicle_detail_ids': [Command.create({
                    'vehicle_id': line.vehicle_id.id,  # Xe cần giao cho khách.
                    'vehicle_price': line.daily_rate,  # Giá ngày lấy từ dòng hợp đồng.
                    'delivery_date': start.date(),  # Ngày giao dự kiến.
                    'delivery_time': start.strftime('%H:%M'),  # Giờ giao dự kiến.
                    'return_date': end.date(),  # Ngày thu hồi dự kiến.
                    'return_time': end.strftime('%H:%M'),  # Giờ thu hồi dự kiến.
                    'date_checkout': contract.start_date,  # Thời điểm giao đầy đủ để đối chiếu.
                    'date_checkin': contract.end_date,  # Thời điểm trả đầy đủ để đối chiếu.
                    'qty_charger': 1 if line.vehicle_id.is_electric_motorbike else 0,  # Xe điện có bộ sạc.
                    'delivery_visual_note': VehicleLine._get_vehicle_exterior_condition(line.vehicle_id),  # Lưu ngoại quan trước lúc giao.
                }) for line in contract.line_ids if line.vehicle_id],
            })  # Các xe mới ở Chờ giao nên phiếu ở Chưa thực hiện.

        return result  # Giữ nguyên kết quả nút Xác nhận hợp đồng. 
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    #  NGAWN CANJ HOPWJ DODONGF HOANF TAATS KHI XE CHUAW THU HOOIF XONG
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
    def action_done(self):
        """Hợp đồng chỉ hoàn tất khi tất cả các xe được thu hồi thành công"""
        for contract in self:
            ticket = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)], limit=1) # laays phieeus vanaj hafnh cuar hopjw dodngf
            if ticket:
                not_returned = ticket.vehicle_detail_ids.filtered(lambda v: v.status != 'returned') # laasy casc xe chuaw dduwojc thu hooif
                if not_returned:
                    vehicle_names = ', '.join(not_returned.mapped(lambda v: v.vehicle_id.name or 'Xe') or ['xe'])
                    raise UserError(_('Không thể hoàn tất hợp đồng %(contract)s! Các xe sau chưa được thu hồi thành công: %(vehicles)s. Hợp đồng chỉ hoàn tất khi tất cả các xe được thu hồi thành công.') % {
                        'contract': contract.name,
                        'vehicles': vehicle_names,
                    })
        return super(RentalContract, self).action_done()
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # 
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
    def action_cancel(self): # Không bắt buộc cấm hủy nếu có xe đã đi giao vì có thể phát sinh nhiều trường hợp ngoại lệ (khách vi phạm, sự cố)
        res = super(RentalContract, self).action_cancel() if hasattr(super(RentalContract, self), 'action_cancel') else True
        for contract in self:
            tickets = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)])
            tickets.action_contract_cancelled()
        return res
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



    def write(self, vals):
        if vals.get('state') == 'done': # Nếu chuyển trạng thái sang done
            for contract in self: # Kiểm tra giống action_done: tất cả xe phải được thu hồi
                ticket = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)], limit=1)
                if ticket:
                    not_returned = ticket.vehicle_detail_ids.filtered(lambda v: v.status != 'returned')
                    if not_returned:
                        vehicle_names = ', '.join(not_returned.mapped(lambda v: v.vehicle_id.name or 'Xe') or ['xe'])
                        raise UserError(_('Không thể hoàn tất hợp đồng %(contract)s! Các xe sau chưa được thu hồi thành công: %(vehicles)s. Hợp đồng chỉ hoàn tất khi tất cả các xe được thu hồi thành công.') % {
                            'contract': contract.name,
                            'vehicles': vehicle_names,
                        })
        res = super(RentalContract, self).write(vals)

        # Nếu chuyển trạng thái sang cancelled thì khóa phiếu vận hành
        if vals.get('state') == 'cancelled':
            for contract in self:
                tickets = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)])
                tickets.action_contract_cancelled() # Khóa phiếu vận hành sang contract_cancelled
        return res



# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# KẾ THỪA CHI TIẾT HỢP ĐỒNG (DÒNG XE TRONG HỢP ĐỒNG)
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<  
class RentalContractLine(models.Model):
    _inherit = 'rental.contract.line'

    # Được cấp quyền đổi xe mới được đưa vào chi tiết hợp đồng
    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('allow_vehicle_exchange'): 
            for vals in vals_list:
                if vals.get('vehicle_type_id') and 'daily_rate' not in vals: # Nếu có loại xe mà chưa có giá ngày thì bổ sung giá ngày
                    vehicle_type = self.env['rental.vehicle.type'].browse(vals['vehicle_type_id'])
                    vals['daily_rate'] = vehicle_type.daily_rate
            return models.Model.create(self, vals_list) # Giúp vượt qua hàm bắt lỗi ở contract (nếu hợp đồng đã xác nhận không cho bổ sung). Lệnh này chạy thẳng lệnh INSERT vào trong DB
        return super().create(vals_list) # Nếu không được cấp quyền đổi xe thì gọi đến hàm create của Core để kiểm tra và ngăn chặn

    def write(self, vals):
        if self.env.context.get('allow_vehicle_exchange'): # Cho phép sửa dòng xe khi thực hiện đổi xe (vượt qua kiểm tra khóa của Core)
            return models.Model.write(self, vals) 
        return super().write(vals)

    def unlink(self): 
        if self.env.context.get('allow_vehicle_exchange'): # Cho phép xóa dòng xe cũ khi thực hiện đổi xe (vượt qua kiểm tra khóa của Core)
            return models.Model.unlink(self)
        return super().unlink()

   