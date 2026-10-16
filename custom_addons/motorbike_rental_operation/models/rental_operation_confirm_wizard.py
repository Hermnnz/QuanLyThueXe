# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RentalOperationConfirmWizard(models.TransientModel):
    _name = 'rental.operation.confirm.wizard'
    _description = 'Xác nhận Thao tác Vận Hành Xe'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành')
    action_type = fields.Selection([
        ('start_delivery', 'Bắt đầu giao xe'),
        ('confirm_delivery', 'Xác nhận đã giao xe'),
        ('confirm_return', 'Xác nhận thu hồi xe'),
    ], string='Loại thao tác', required=True)
    vehicle_ids = fields.Many2many(
        'rental.operation.ticket.vehicle',
        'rental_op_confirm_veh_rel',
        'wizard_id',
        'vehicle_id',
        string='Danh sách xe',
    )
    message = fields.Text(string='Nội dung xác nhận', readonly=True)

    def action_apply(self):
        self.ensure_one()
        if self.action_type == 'start_delivery':
            self.vehicle_ids.action_start_delivery()
        elif self.action_type == 'confirm_delivery':
            self.vehicle_ids.action_confirm_delivery()
        elif self.action_type == 'confirm_return':
            self.vehicle_ids.action_confirm_return()
        return {'type': 'ir.actions.act_window_close'}
