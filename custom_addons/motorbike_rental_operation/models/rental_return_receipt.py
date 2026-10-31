# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RentalReturnReceipt(models.Model):
    _name = 'rental.return.receipt'
    _description = 'Biên Lai Thu Hồi Xe & Trang Thiết Bị'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Mã Biên Lai', required=True, copy=False, readonly=True, default='Mới')
    
    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', required=True, ondelete='cascade')
    contract_id = fields.Many2one('rental.contract', string='Hợp đồng thuê', related='ticket_id.contract_id', store=True, readonly=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng', required=True)
    customer_phone = fields.Char(string='Số điện thoại')

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.customer_phone = self.customer_id.phone or self.customer_id.mobile or ''
    
    return_date = fields.Date(string='Ngày thu hồi xe')
    return_time = fields.Char(string='Giờ thu hồi xe', help='Thời gian thu hồi xe (VD: 18:00)')
    return_location = fields.Char(string='Địa điểm thu hồi xe', default='Tại cửa hàng')

    vehicle_ids = fields.Many2many(
        'rental.operation.ticket.vehicle',
        'rental_return_receipt_vehicle_rel',
        'receipt_id',
        'vehicle_detail_id',
        string='Danh sách xe thu hồi',
        required=True
    )

    # 4 món phụ kiện thu hồi thực tế
    qty_helmet = fields.Integer(string='Mũ bảo hiểm nhận lại', default=2, required=True)
    qty_raincoat = fields.Integer(string='Áo mưa nhận lại', default=2, required=True)
    qty_phone_holder = fields.Integer(string='Giá đỡ điện thoại nhận lại', default=1, required=True)
    qty_charger = fields.Integer(string='Bộ sạc xe nhận lại', default=1, required=True)

    return_visual_note = fields.Text(
        string='Tình trạng ngoại quan khi thu hồi',
        default='Ngoại quan bình thường, không trầy xước phát sinh.'
    )

    user_id = fields.Many2one(
        'res.users', 
        string='Nhân viên thu hồi xe', 
        default=lambda self: self.env.user if self.env.user.name not in ('Administrator', 'admin', 'Admin') else False
    )
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)

    is_selected = fields.Boolean(string='Chọn', default=False)
    vehicle_count = fields.Integer(string='Số lượng xe', compute='_compute_vehicle_count')

    @api.depends('vehicle_ids')
    def _compute_vehicle_count(self):
        for rec in self:
            rec.vehicle_count = len(rec.vehicle_ids)

    state = fields.Selection([
        ('pending', 'Chưa thực hiện'),
        ('returned', 'Đã thu hồi'),
    ], string='Trạng thái', default='pending', compute='_compute_state', store=True, readonly=False)

    @api.depends('vehicle_ids.status')
    def _compute_state(self):
        for rec in self:
            if not rec.vehicle_ids:
                rec.state = 'pending'
                continue
            statuses = rec.vehicle_ids.mapped('status')
            if all(s == 'returned' for s in statuses):
                rec.state = 'returned'
            else:
                rec.state = 'pending'

    def action_confirm_return(self):
        """Xác nhận đã thu hồi xe: chuyển biên lai sang Đã thu hồi và cập nhật các xe"""
        now = fields.Datetime.now()
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))
            if rec.state == 'returned':
                if len(self) == 1:
                    raise UserError(_('Biên lai "%s" đã ở trạng thái Đã thu hồi hoàn tất!') % (rec.name or ''))
                continue
            if not rec.vehicle_ids:
                raise UserError(_('Biên lai "%s" chưa có danh sách xe thu hồi!') % (rec.name or ''))

            # Rule: Chỉ những xe đang ở trạng thái đã bàn giao ('renting') mới có thể thu hồi
            not_delivered = rec.vehicle_ids.filtered(lambda v: v.status != 'renting')
            if not_delivered:
                names = ', '.join(not_delivered.mapped(lambda v: v._get_vehicle_label()))
                raise UserError(_(
                    'Biên lai "%(receipt)s" không thể chuyển sang trạng thái "Đã thu hồi" vì các xe sau chưa ở trạng thái đã bàn giao:\n%(names)s\n'
                    'Vui lòng chỉ thu hồi những xe đã được bàn giao cho khách hàng!'
                ) % {
                    'receipt': rec.name or '',
                    'names': names,
                })

            # 1. Cập nhật các xe con trong biên lai
            for vline in rec.vehicle_ids:
                v_vals = {
                    'status': 'returned',
                    'is_selected': False,
                }
                if not vline.actual_return_date:
                    v_vals['actual_return_date'] = now
                if rec.return_visual_note:
                    v_vals['return_visual_note'] = rec.return_visual_note
                vline.write(v_vals)

                # Chuyển Fleet xe sang pending_inspection & technical_ready = False
                if vline.vehicle_id:
                    vline.vehicle_id.write({
                        'operational_status': 'pending_inspection',
                        'technical_ready': False,
                    })

            # Kiểm tra nếu tất cả xe trong phiếu đã được thu hồi
            if rec.ticket_id:
                all_returned = all(v.status == 'returned' for v in rec.ticket_id.vehicle_detail_ids)
                if all_returned and not rec.ticket_id.actual_return_date:
                    rec.ticket_id.actual_return_date = now

            # 2. Cập nhật biên lai
            rec.write({
                'state': 'returned',
                'is_selected': False,
            })
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.return.receipt') or 'BLTH'
            if vals.get('ticket_id'):
                ticket = self.env['rental.operation.ticket'].browse(vals['ticket_id'])
                if ticket.state == 'contract_cancelled':
                    raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể tạo biên lai thu hồi xe!'))
                if not vals.get('customer_id') and ticket.customer_id:
                    vals['customer_id'] = ticket.customer_id.id
            if not vals.get('customer_phone') and vals.get('customer_id'):
                partner = self.env['res.partner'].browse(vals['customer_id'])
                vals['customer_phone'] = partner.phone or partner.mobile or ''
        receipts = super(RentalReturnReceipt, self).create(vals_list)
        return receipts

    def write(self, vals):
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể chỉnh sửa biên lai!'))

        # Rule: Không cho phép chuyển trực tiếp state sang returned nếu có xe chưa bàn giao
        if vals.get('state') == 'returned':
            for rec in self:
                not_delivered = rec.vehicle_ids.filtered(lambda v: v.status not in ('renting', 'returned'))
                if not_delivered:
                    names = ', '.join(not_delivered.mapped(lambda v: v._get_vehicle_label()))
                    raise UserError(_(
                        'Biên lai "%(receipt)s" không thể chuyển sang trạng thái "Đã thu hồi" vì các xe sau chưa ở trạng thái đã bàn giao:\n%(names)s'
                    ) % {
                        'receipt': rec.name or '',
                        'names': names,
                    })

        # Nếu có cập nhật các trường thông tin biên lai (ngoài is_selected và state)
        if any(k not in ('is_selected', 'state') for k in vals.keys()):
            returned_recs = self.filtered(lambda r: r.state == 'returned')
            if returned_recs:
                # Nếu chỉ có duy nhất biên lai đã thu hồi hoàn tất được sửa
                if len(self) == 1:
                    raise UserError(_('Biên lai "%s" đã thu hồi hoàn tất, không được phép chỉnh sửa!') % (returned_recs[0].name or ''))
                # Nếu sửa nhiều biên lai cùng lúc, chỉ cập nhật cho các biên lai chưa thu hồi hoàn tất
                updatable_recs = self - returned_recs
                if updatable_recs:
                    return super(RentalReturnReceipt, updatable_recs).write(vals)
                return True

        return super(RentalReturnReceipt, self).write(vals)

    def action_open_receipt_detail(self):
        """Mở chi tiết biên lai thu hồi xe dạng modal popup (chỉ xem)"""
        self.ensure_one()
        view_id = self.env.ref('motorbike_rental_operation.view_rental_return_receipt_form', raise_if_not_found=False)
        return {
            'name': _('Chi Tiết Biên Lai Thu Hồi: %s') % (self.name or ''),
            'type': 'ir.actions.act_window',
            'res_model': 'rental.return.receipt',
            'res_id': self.id,
            'views': [(view_id.id, 'form')] if view_id else [(False, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'flags': {'mode': 'readonly'},
            'context': {
                'default_ticket_id': self.ticket_id.id,
                'create': False,
                'edit': False,
                'delete': False,
            },
        }

    def action_save_changes(self):
        """Lưu thay đổi trên biên lai thu hồi xe và đồng bộ thông tin nếu có"""
        self.ensure_one()
        if self.ticket_id and self.ticket_id.state == 'contract_cancelled':
            raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))
        if self.state == 'returned':
            raise UserError(_('Biên lai đã thu hồi hoàn tất, không thể chỉnh sửa!'))

        for veh in self.vehicle_ids:
            if veh.status != 'returned':
                v_vals = {}
                if self.return_date and hasattr(veh, 'return_date') and veh.return_date != self.return_date:
                    v_vals['return_date'] = self.return_date
                    v_vals['is_custom_return_date'] = True
                if self.return_time and hasattr(veh, 'return_time') and veh.return_time != self.return_time:
                    v_vals['return_time'] = self.return_time
                    v_vals['is_custom_return_time'] = True
                if self.return_location and veh.return_location != self.return_location:
                    v_vals['return_location'] = self.return_location
                    v_vals['is_custom_return_location'] = True
                if v_vals:
                    veh.write(v_vals)

        return {'type': 'ir.actions.act_window_close'}

    def unlink(self):
        if not self.env.context.get('allow_wizard_cleanup'):
            raise UserError(_('Biên lai chỉ được phép xem, không được phép xóa!'))
        return super(RentalReturnReceipt, self).unlink()

    def action_print_receipt(self):
        """In lại biên lai thu hồi xe dạng PDF"""
        self.ensure_one()
        return self.env.ref('motorbike_rental_operation.action_report_return_receipt').report_action(self)
