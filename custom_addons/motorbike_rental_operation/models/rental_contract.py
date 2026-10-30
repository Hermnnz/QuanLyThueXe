# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RentalContract(models.Model):
    _inherit = 'rental.contract'

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
