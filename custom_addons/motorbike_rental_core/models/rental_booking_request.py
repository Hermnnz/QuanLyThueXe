import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .rental_contract import _DEFAULT_RENTAL_DEPOSIT


class RentalBookingRequest(models.Model):
    _name = 'rental.booking.request'
    _description = 'Yêu cầu thuê xe'
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Mã yêu cầu',
        required=True,
        copy=False,
        default='/',
        readonly=True,
    )
    customer_name = fields.Char(string='Họ tên khách', required=True)
    phone = fields.Char(string='Số điện thoại', required=True)
    email = fields.Char(string='Email')
    customer_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        ondelete='restrict',
        domain=[('is_rental_customer', '=', True)],
    )
    start_date = fields.Datetime(string='Bắt đầu thuê', required=True)
    end_date = fields.Datetime(string='Kết thúc thuê', required=True)
    notes = fields.Text(string='Ghi chú của khách')
    line_ids = fields.One2many(
        'rental.booking.request.line',
        'request_id',
        string='Xe khách yêu cầu',
        copy=True,
    )
    state = fields.Selection(
        [
            ('new', 'Mới'),
            ('converted', 'Đã tạo hợp đồng nháp'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='new',
        copy=False,
        index=True,
    )
    contract_id = fields.Many2one(
        'rental.contract',
        string='Hợp đồng nháp',
        readonly=True,
        copy=False,
        ondelete='restrict',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('customer_id'):
                customer = self._find_existing_rental_customer(
                    vals.get('customer_name'),
                    vals.get('phone'),
                )
                if customer:
                    vals['customer_id'] = customer.id
                    vals['customer_name'] = customer.name
                    vals['phone'] = customer.phone
                    vals['email'] = customer.email or vals.get('email')
            if vals.get('name', '/') == '/':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('rental.booking.request')
                    or '/'
                )
        return super().create(vals_list)

    @api.model
    def _find_existing_rental_customer(self, name, phone):
        normalized_name = self._normalize_customer_name(name)
        normalized_phone = self._normalize_customer_phone(phone)
        if not normalized_name or not normalized_phone:
            return self.env['res.partner']

        candidates = self.env['res.partner'].sudo().search([
            ('is_rental_customer', '=', True),
            ('name', '!=', False),
            ('phone', '!=', False),
        ], order='id desc')
        matches = candidates.filtered(
            lambda customer: (
                self._normalize_customer_name(customer.name) == normalized_name
                and self._normalize_customer_phone(customer.phone) == normalized_phone
            )
        )
        if not matches:
            return self.env['res.partner']

        return max(
            matches,
            key=lambda customer: (
                bool(customer.email)
                + bool(customer.rental_id_number)
                + bool(customer.rental_document_ids.filtered('file')),
                bool(customer.email),
                bool(customer.rental_id_number),
                bool(customer.rental_document_ids.filtered('file')),
                customer.id,
            ),
        )

    @api.model
    def _normalize_customer_name(self, name):
        decomposed_name = unicodedata.normalize('NFKD', name or '')
        without_accents = ''.join(
            character
            for character in decomposed_name
            if not unicodedata.combining(character)
        )
        return ' '.join(without_accents.split()).casefold()

    @api.model
    def _normalize_customer_phone(self, phone):
        digits = ''.join(character for character in (phone or '') if character.isdigit())
        if digits.startswith('0084') and len(digits) == 13:
            return '0' + digits[4:]
        if digits.startswith('84') and len(digits) == 11:
            return '0' + digits[2:]
        return digits

    @api.constrains('start_date', 'end_date', 'line_ids')
    def _check_request(self):
        for request in self:
            if request.start_date and request.end_date and request.end_date <= request.start_date:
                raise ValidationError(_('Thời gian kết thúc phải sau thời gian bắt đầu.'))
            if request.state == 'new' and not request.line_ids:
                raise ValidationError(_('Yêu cầu phải có ít nhất một xe.'))

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.customer_name = self.customer_id.name
            self.phone = self.customer_id.phone
            self.email = self.customer_id.email

    def action_create_draft_contract(self):
        self.ensure_one()
        if self.state != 'new':
            raise UserError(_('Chỉ yêu cầu mới mới có thể tạo hợp đồng nháp.'))
        if not self.line_ids:
            raise UserError(_('Yêu cầu phải có ít nhất một xe trước khi tạo hợp đồng.'))
        if not self.customer_name or not self.phone:
            raise UserError(_('Vui lòng nhập họ tên và số điện thoại khách hàng.'))
        if self.end_date <= self.start_date:
            raise UserError(_('Thời gian kết thúc phải sau thời gian bắt đầu.'))

        vehicle_ids = self.line_ids.mapped('vehicle_id').ids
        if len(vehicle_ids) != len(set(vehicle_ids)):
            raise UserError(_('Không thể chọn cùng một xe nhiều lần trong một yêu cầu.'))

        for line in self.line_ids:
            vehicle = line.vehicle_id
            if not vehicle.active or vehicle.model_id != line.vehicle_type_id.model_id:
                raise UserError(
                    _('Xe %(vehicle)s không còn phù hợp với dòng xe đã yêu cầu.')
                    % {'vehicle': vehicle.display_name}
                )
            availability = vehicle.check_fleet_availability(
                self.start_date, self.end_date
            )
            if (
                vehicle.operational_status != 'available'
                or not availability
                or not availability[0]['fleet_ok']
            ):
                raise UserError(
                    _('Xe %(vehicle)s hiện không đủ điều kiện cho thời gian đã chọn.')
                    % {'vehicle': vehicle.display_name}
                )

        conflict = self.env['rental.contract.line'].search(
            [
                ('vehicle_id', 'in', vehicle_ids),
                ('contract_id.state', 'in', ('confirmed', 'in_progress')),
                ('contract_id.start_date', '<', self.end_date),
                ('contract_id.end_date', '>', self.start_date),
            ],
            limit=1,
        )
        if conflict:
            raise UserError(
                _('Xe %s đã được giữ trong một hợp đồng khác ở thời gian này.')
                % conflict.vehicle_id.display_name
            )

        customer = self.customer_id or self._find_existing_rental_customer(
            self.customer_name, self.phone
        )
        if not customer:
            customer = self.env['res.partner'].create({
                'name': self.customer_name,
                'phone': self.phone,
                'email': self.email,
                'is_rental_customer': True,
            })

        currency = self.line_ids[0].vehicle_type_id.currency_id
        contract = self.env['rental.contract'].create({
            'customer_id': customer.id,
            'currency_id': currency.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'deposit_amount': _DEFAULT_RENTAL_DEPOSIT,
            'notes': self.notes,
            'line_ids': [
                (0, 0, {
                    'vehicle_id': line.vehicle_id.id,
                    'vehicle_type_id': line.vehicle_type_id.id,
                    'daily_rate': line.vehicle_type_id.daily_rate,
                })
                for line in self.line_ids
            ],
        })
        self.write({
            'customer_id': customer.id,
            'state': 'converted',
            'contract_id': contract.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hợp đồng thuê xe'),
            'res_model': 'rental.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel_request(self):
        for booking_request in self:
            if booking_request.state != 'new':
                raise UserError(_('Chỉ yêu cầu chưa chuyển hợp đồng mới có thể hủy.'))
            booking_request.state = 'cancelled'
        return True


class RentalBookingRequestLine(models.Model):
    _name = 'rental.booking.request.line'
    _description = 'Xe trong yêu cầu thuê'
    _order = 'id'

    request_id = fields.Many2one(
        'rental.booking.request',
        string='Yêu cầu',
        required=True,
        ondelete='cascade',
        index=True,
    )
    vehicle_type_id = fields.Many2one(
        'rental.vehicle.type',
        string='Dòng xe / bảng giá',
        required=True,
        ondelete='restrict',
        domain=[('active', '=', True)],
    )
    vehicle_model_id = fields.Many2one(
        related='vehicle_type_id.model_id',
        string='Dòng xe',
        readonly=True,
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Xe khách yêu cầu',
        required=True,
        ondelete='restrict',
        domain="[('active', '=', True), ('model_id', '=', vehicle_model_id)]",
    )

    _sql_constraints = [
        (
            'unique_booking_request_vehicle',
            'UNIQUE(request_id, vehicle_id)',
            'Mỗi xe chỉ được xuất hiện một lần trong một yêu cầu.',
        ),
    ]

    @api.constrains('vehicle_id', 'vehicle_type_id')
    def _check_vehicle_matches_type(self):
        for line in self:
            if line.vehicle_id and line.vehicle_type_id:
                if line.vehicle_id.model_id != line.vehicle_type_id.model_id:
                    raise ValidationError(
                        _('Dòng xe phải khớp với dòng xe thực tế của phương tiện.')
                    )
