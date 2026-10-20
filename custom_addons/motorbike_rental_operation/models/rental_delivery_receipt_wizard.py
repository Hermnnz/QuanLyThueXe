# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class RentalDeliveryReceiptWizard(models.TransientModel):
    _name = 'rental.delivery.receipt.wizard'
    _description = 'Xác Nhận & Xuất Biên Lai Giao Xe'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', required=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng', related='ticket_id.customer_id', readonly=True)
    customer_phone = fields.Char(string='Số điện thoại', related='ticket_id.customer_phone', readonly=True)

    # Thống kê số lượng biên lai
    receipt_count = fields.Integer(string='Số lượng biên lai', compute='_compute_receipt_summary')
    receipt_count_display = fields.Char(string='Thông tin biên lai', compute='_compute_receipt_summary')

    # Tab Biên lai 1
    receipt_1_visible = fields.Boolean(default=False)
    receipt_1_name = fields.Char(string='Tên biên lai 1', default='Biên lai 1')
    receipt_1_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_1_customer_phone = fields.Char(string='Số điện thoại')
    receipt_1_delivery_time = fields.Char(string='Giờ giao xe', default='08:00')
    receipt_1_delivery_date = fields.Date(string='Ngày giao xe', default=fields.Date.context_today)
    receipt_1_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_1_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_1_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_1_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_1_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_1_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_1_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_1_id',
        string='Xe biên lai 1'
    )

    # Tab Biên lai 2
    receipt_2_visible = fields.Boolean(default=False)
    receipt_2_name = fields.Char(string='Tên biên lai 2', default='Biên lai 2')
    receipt_2_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_2_customer_phone = fields.Char(string='Số điện thoại')
    receipt_2_delivery_time = fields.Char(string='Giờ giao xe', default='14:00')
    receipt_2_delivery_date = fields.Date(string='Ngày giao xe', default=fields.Date.context_today)
    receipt_2_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_2_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_2_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_2_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_2_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_2_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_2_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_2_id',
        string='Xe biên lai 2'
    )

    # Tab Biên lai 3
    receipt_3_visible = fields.Boolean(default=False)
    receipt_3_name = fields.Char(string='Tên biên lai 3', default='Biên lai 3')
    receipt_3_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_3_customer_phone = fields.Char(string='Số điện thoại')
    receipt_3_delivery_time = fields.Char(string='Giờ giao xe', default='08:00')
    receipt_3_delivery_date = fields.Date(string='Ngày giao xe', default=fields.Date.context_today)
    receipt_3_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_3_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_3_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_3_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_3_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_3_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_3_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_3_id',
        string='Xe biên lai 3'
    )

    # Tab Biên lai 4
    receipt_4_visible = fields.Boolean(default=False)
    receipt_4_name = fields.Char(string='Tên biên lai 4', default='Biên lai 4')
    receipt_4_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_4_customer_phone = fields.Char(string='Số điện thoại')
    receipt_4_delivery_time = fields.Char(string='Giờ giao xe', default='08:00')
    receipt_4_delivery_date = fields.Date(string='Ngày giao xe', default=fields.Date.context_today)
    receipt_4_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_4_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_4_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_4_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_4_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_4_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_4_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_4_id',
        string='Xe biên lai 4'
    )

    # Tab Biên lai 5
    receipt_5_visible = fields.Boolean(default=False)
    receipt_5_name = fields.Char(string='Tên biên lai 5', default='Biên lai 5')
    receipt_5_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_5_customer_phone = fields.Char(string='Số điện thoại')
    receipt_5_delivery_time = fields.Char(string='Giờ giao xe', default='08:00')
    receipt_5_delivery_date = fields.Date(string='Ngày giao xe', default=fields.Date.context_today)
    receipt_5_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_5_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_5_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_5_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_5_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_5_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_5_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_5_id',
        string='Xe biên lai 5'
    )

    # Tab Biên lai 6
    receipt_6_visible = fields.Boolean(default=False)
    receipt_6_name = fields.Char(string='Tên biên lai 6', default='Biên lai 6')
    receipt_6_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_6_customer_phone = fields.Char(string='Số điện thoại')
    receipt_6_delivery_time = fields.Char(string='Giờ giao xe', default='08:00')
    receipt_6_delivery_date = fields.Date(string='Ngày giao xe', default=fields.Date.context_today)
    receipt_6_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_6_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_6_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_6_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_6_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_6_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_6_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_6_id',
        string='Xe biên lai 6'
    )

    # Tương thích ngược với các trường cũ nếu có
    group_ids = fields.One2many(
        'rental.delivery.receipt.wizard.group',
        'wizard_id',
        string='Danh mục Biên lai giao xe cần xuất'
    )
    vehicle_line_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_id',
        string='Danh sách xe & Tình trạng ngoại quan ban đầu'
    )

    @api.depends(
        'receipt_1_visible', 'receipt_2_visible', 'receipt_3_visible',
        'receipt_4_visible', 'receipt_5_visible', 'receipt_6_visible'
    )
    def _compute_receipt_summary(self):
        for rec in self:
            count = sum(1 for i in range(1, 7) if getattr(rec, f'receipt_{i}_visible'))
            rec.receipt_count = count
            if count == 1:
                rec.receipt_count_display = 'Phiếu có 1 biên lai giao xe cần xuất.'
            elif count > 1:
                rec.receipt_count_display = f'Phiếu có {count} biên lai giao xe cần xuất. Vui lòng kiểm tra và tùy chỉnh thông tin ở từng tab bên dưới.'
            else:
                rec.receipt_count_display = 'Không có biên lai nào cần xuất.'

    @api.onchange('receipt_1_customer_id')
    def _onchange_receipt_1_customer_id(self):
        if self.receipt_1_customer_id:
            self.receipt_1_customer_phone = self.receipt_1_customer_id.phone or self.receipt_1_customer_id.mobile or ''

    @api.onchange('receipt_2_customer_id')
    def _onchange_receipt_2_customer_id(self):
        if self.receipt_2_customer_id:
            self.receipt_2_customer_phone = self.receipt_2_customer_id.phone or self.receipt_2_customer_id.mobile or ''

    @api.onchange('receipt_3_customer_id')
    def _onchange_receipt_3_customer_id(self):
        if self.receipt_3_customer_id:
            self.receipt_3_customer_phone = self.receipt_3_customer_id.phone or self.receipt_3_customer_id.mobile or ''

    @api.onchange('receipt_4_customer_id')
    def _onchange_receipt_4_customer_id(self):
        if self.receipt_4_customer_id:
            self.receipt_4_customer_phone = self.receipt_4_customer_id.phone or self.receipt_4_customer_id.mobile or ''

    @api.onchange('receipt_5_customer_id')
    def _onchange_receipt_5_customer_id(self):
        if self.receipt_5_customer_id:
            self.receipt_5_customer_phone = self.receipt_5_customer_id.phone or self.receipt_5_customer_id.mobile or ''

    @api.onchange('receipt_6_customer_id')
    def _onchange_receipt_6_customer_id(self):
        if self.receipt_6_customer_id:
            self.receipt_6_customer_phone = self.receipt_6_customer_id.phone or self.receipt_6_customer_id.mobile or ''

    def action_confirm_and_print(self):
        """Xác nhận thông tin, tạo các biên lai giao xe tương ứng từng tab và xuất file PDF"""
        self.ensure_one()

        active_indices = [i for i in range(1, 7) if getattr(self, f'receipt_{i}_visible')]
        
        # Nếu dùng cấu trúc cũ
        if not active_indices and self.group_ids:
            return self._action_confirm_and_print_legacy()

        if not active_indices:
            raise UserError('Không có biên lai nào để xuất!')

        all_vehicle_details = self.env['rental.operation.ticket.vehicle']
        for i in active_indices:
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            all_vehicle_details |= vlines.mapped('vehicle_detail_id')

        if not all_vehicle_details:
            raise UserError('Danh sách xe giao không được để trống!')

        # Kiểm tra xem có xe nào đã giao hoặc đã thu hồi không
        already_renting = all_vehicle_details.filtered(lambda v: v.status in ('renting', 'returned'))
        if already_renting:
            names = ', '.join(already_renting.mapped(lambda v: v._get_vehicle_label()))
            raise UserError(f'Xe {names} đã được giao xe thành công!')

        # 1. Cập nhật tình trạng ngoại quan ban đầu riêng cho từng chiếc xe
        for i in active_indices:
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            for vline in vlines:
                if vline.vehicle_detail_id:
                    note = (vline.delivery_visual_note or '').strip()
                    if not note or note in (
                        'Ngoại quan của xe không có vấn đề',
                        'Xe vận hành tốt, ngoại quan bình thường, không trầy xước phát sinh.'
                    ):
                        veh_cond = vline.vehicle_detail_id._get_vehicle_exterior_condition(vline.vehicle_id)
                        if veh_cond and veh_cond != 'Ngoại quan của xe không có vấn đề':
                            note = veh_cond
                    note = note or 'Ngoại quan của xe không có vấn đề'
                    vline.vehicle_detail_id.write({'delivery_visual_note': note})

        created_receipts = self.env['rental.delivery.receipt']

        # 2. Tạo biên lai cho từng tab
        for i in active_indices:
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            grp_vehicles = vlines.mapped('vehicle_detail_id')
            if not grp_vehicles:
                continue

            cust = getattr(self, f'receipt_{i}_customer_id') or self.ticket_id.customer_id
            cust_phone = getattr(self, f'receipt_{i}_customer_phone') or (cust.phone or cust.mobile or '')
            deliv_time = getattr(self, f'receipt_{i}_delivery_time') or '08:00'
            deliv_date = getattr(self, f'receipt_{i}_delivery_date') or fields.Date.context_today(self)
            deliv_loc = getattr(self, f'receipt_{i}_delivery_location') or 'Tại cửa hàng'
            q_helmet = max(0, getattr(self, f'receipt_{i}_qty_helmet'))
            q_raincoat = max(0, getattr(self, f'receipt_{i}_qty_raincoat'))
            q_phone_holder = max(0, getattr(self, f'receipt_{i}_qty_phone_holder'))
            q_charger = max(0, getattr(self, f'receipt_{i}_qty_charger'))

            receipt_vals = {
                'ticket_id': self.ticket_id.id,
                'customer_id': cust.id,
                'customer_phone': cust_phone,
                'delivery_time': deliv_time,
                'delivery_date': deliv_date,
                'delivery_location': deliv_loc,
                'vehicle_ids': [(6, 0, grp_vehicles.ids)],
                'qty_helmet': q_helmet,
                'qty_raincoat': q_raincoat,
                'qty_phone_holder': q_phone_holder,
                'qty_charger': q_charger,
                'state': 'confirmed',
            }
            receipt = self.env['rental.delivery.receipt'].create(receipt_vals)
            created_receipts |= receipt

            veh_vals = {
                'delivery_receipt_id': receipt.id,
                'delivery_receipt_issued': True,
                'receipt_printed_at': fields.Datetime.now(),
                'qty_helmet': q_helmet,
                'qty_raincoat': q_raincoat,
                'qty_phone_holder': q_phone_holder,
                'qty_charger': q_charger,
                'is_selected': False,
                'status': 'renting',
            }
            if any(not v.actual_delivery_date for v in grp_vehicles):
                veh_vals['actual_delivery_date'] = fields.Datetime.now()
            grp_vehicles.write(veh_vals)
            if self.ticket_id and not self.ticket_id.actual_delivery_date:
                self.ticket_id.actual_delivery_date = fields.Datetime.now()
            grp_vehicles._sync_contract_in_progress()

        if not created_receipts:
            raise UserError('Không có biên lai nào được tạo!')

        return self.env.ref('motorbike_rental_operation.action_report_delivery_receipt').report_action(created_receipts)

    def _action_confirm_and_print_legacy(self):
        """Hỗ trợ dự phòng nếu dùng danh sách nhóm cũ"""
        target_lines = self.vehicle_line_ids.mapped('vehicle_detail_id')
        already_renting = target_lines.filtered(lambda v: v.status in ('renting', 'returned'))
        if already_renting:
            names = ', '.join(already_renting.mapped(lambda v: v._get_vehicle_label()))
            raise UserError(f'Xe {names} đã được giao xe thành công!')

        for vline in self.vehicle_line_ids:
            if vline.vehicle_detail_id:
                note = (vline.delivery_visual_note or '').strip()
                if not note or note in (
                    'Ngoại quan của xe không có vấn đề',
                    'Xe vận hành tốt, ngoại quan bình thường, không trầy xước phát sinh.'
                ):
                    veh_cond = vline.vehicle_detail_id._get_vehicle_exterior_condition(vline.vehicle_id)
                    if veh_cond and veh_cond != 'Ngoại quan của xe không có vấn đề':
                        note = veh_cond
                note = note or 'Ngoại quan của xe không có vấn đề'
                vline.vehicle_detail_id.write({'delivery_visual_note': note})

        created_receipts = self.env['rental.delivery.receipt']
        for grp in self.group_ids:
            grp_vehicles = self.vehicle_line_ids.filtered(lambda v: v.group_key == grp.group_key).mapped('vehicle_detail_id')
            if not grp_vehicles:
                continue

            receipt_vals = {
                'ticket_id': self.ticket_id.id,
                'customer_id': grp.customer_id.id if grp.customer_id else self.customer_id.id,
                'delivery_time': grp.delivery_time or '08:00',
                'delivery_date': grp.delivery_date or fields.Date.context_today(self),
                'vehicle_ids': [(6, 0, grp_vehicles.ids)],
                'qty_helmet': max(0, grp.qty_helmet),
                'qty_raincoat': max(0, grp.qty_raincoat),
                'qty_phone_holder': max(0, grp.qty_phone_holder),
                'qty_charger': max(0, grp.qty_charger),
                'state': 'confirmed',
            }
            receipt = self.env['rental.delivery.receipt'].create(receipt_vals)
            created_receipts |= receipt

            veh_vals = {
                'delivery_receipt_id': receipt.id,
                'delivery_receipt_issued': True,
                'receipt_printed_at': fields.Datetime.now(),
                'qty_helmet': max(0, grp.qty_helmet),
                'qty_raincoat': max(0, grp.qty_raincoat),
                'qty_phone_holder': max(0, grp.qty_phone_holder),
                'qty_charger': max(0, grp.qty_charger),
                'is_selected': False,
                'status': 'renting',
            }
            if any(not v.actual_delivery_date for v in grp_vehicles):
                veh_vals['actual_delivery_date'] = fields.Datetime.now()
            grp_vehicles.write(veh_vals)
            if self.ticket_id and not self.ticket_id.actual_delivery_date:
                self.ticket_id.actual_delivery_date = fields.Datetime.now()
            grp_vehicles._sync_contract_in_progress()

        if not created_receipts:
            raise UserError('Không có biên lai nào được tạo!')

        return self.env.ref('motorbike_rental_operation.action_report_delivery_receipt').report_action(created_receipts)


class RentalDeliveryReceiptWizardGroup(models.TransientModel):
    _name = 'rental.delivery.receipt.wizard.group'
    _description = 'Nhóm Biên Lai Giao Xe'

    wizard_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    group_key = fields.Char(string='Khóa phân nhóm', required=True)
    name = fields.Char(string='Tên biên lai', required=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng')
    delivery_time = fields.Char(string='Giờ giao xe', default='08:00')
    delivery_date = fields.Date(string='Ngày giao xe', default=fields.Date.context_today)
    vehicle_count = fields.Integer(string='Số lượng xe', default=1)

    qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)


class RentalDeliveryReceiptWizardVehicle(models.TransientModel):
    _name = 'rental.delivery.receipt.wizard.vehicle'
    _description = 'Chi Tiết Xe Bàn Giao Trong Wizard'

    # Khóa liên kết từng tab biên lai
    wizard_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_1_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_2_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_3_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_4_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_5_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_6_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')

    vehicle_detail_id = fields.Many2one('rental.operation.ticket.vehicle', string='Dòng xe gốc', required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Xe', related='vehicle_detail_id.vehicle_id', readonly=True)
    license_plate = fields.Char(string='Biển số xe', related='vehicle_id.license_plate', readonly=True)
    group_key = fields.Char(string='Khóa nhóm')
    group_name = fields.Char(string='Thuộc biên lai')
    delivery_time = fields.Char(string='Giờ giao', related='vehicle_detail_id.delivery_time', readonly=True)
    delivery_location = fields.Char(string='Địa điểm giao', related='vehicle_detail_id.delivery_location', readonly=True)
    delivery_visual_note = fields.Text(
        string='Tình trạng ngoại quan ban đầu',
        required=True,
        default='Ngoại quan của xe không có vấn đề'
    )
