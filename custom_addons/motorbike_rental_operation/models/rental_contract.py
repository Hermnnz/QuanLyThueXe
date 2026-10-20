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
        return super(RentalContract, self).write(vals)
