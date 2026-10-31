# -*- coding: utf-8 -*-
from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError

class RentalContract(models.Model):
    _inherit = 'rental.contract'

    def action_confirm(self):
        """Ký hợp đồng thành công rồi tạo một phiếu vận hành Chưa thực hiện."""
        result = super().action_confirm()  # Chỉ tạo phiếu sau khi hợp đồng và hai khoản tiền đã được xác nhận.
        Ticket = self.env['rental.operation.ticket']  # Model lưu phiếu vận hành.
        VehicleLine = self.env['rental.operation.ticket.vehicle']  # Model đọc tình trạng ngoại quan xe.

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

    def action_done(self):
        """Hợp đồng chỉ hoàn tất khi tất cả các xe được thu hồi thành công"""
        for contract in self:
            ticket = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)], limit=1)
            if ticket:
                not_returned = ticket.vehicle_detail_ids.filtered(lambda v: v.status != 'returned')
                if not_returned:
                    vehicle_names = ', '.join(not_returned.mapped(lambda v: v.vehicle_id.name or 'Xe') or ['xe'])
                    raise UserError(_('Không thể hoàn tất hợp đồng %(contract)s! Các xe sau chưa được thu hồi thành công: %(vehicles)s. Hợp đồng chỉ hoàn tất khi tất cả các xe được thu hồi thành công.') % {
                        'contract': contract.name,
                        'vehicles': vehicle_names,
                    })
        return super(RentalContract, self).action_done()

    def action_cancel(self):
        res = super(RentalContract, self).action_cancel() if hasattr(super(RentalContract, self), 'action_cancel') else True
        for contract in self:
            tickets = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)])
            tickets.action_contract_cancelled()
        return res

    def write(self, vals):
        if vals.get('state') == 'done':
            for contract in self:
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
        if vals.get('state') == 'cancelled':
            for contract in self:
                tickets = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)])
                tickets.action_contract_cancelled()
        return res


class RentalContractLine(models.Model):
    _inherit = 'rental.contract.line'

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('allow_vehicle_exchange'):
            for vals in vals_list:
                if vals.get('vehicle_type_id') and 'daily_rate' not in vals:
                    vehicle_type = self.env['rental.vehicle.type'].browse(vals['vehicle_type_id'])
                    vals['daily_rate'] = vehicle_type.daily_rate
            return models.Model.create(self, vals_list)
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('allow_vehicle_exchange'):
            return models.Model.write(self, vals)
        return super().write(vals)

    def unlink(self):
        if self.env.context.get('allow_vehicle_exchange'):
            return models.Model.unlink(self)
        return super().unlink()
