from datetime import datetime

from odoo import _, fields, http
from odoo.exceptions import ValidationError
from odoo.http import request


class RentalWebsite(http.Controller):

    @http.route(
        '/thue-xe',
        type='http',
        auth='public',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def rental_booking(self, **post):
        now = fields.Datetime.now()
        start_default_datetime = fields.Datetime.add(now, hours=1)
        end_default_datetime = fields.Datetime.add(start_default_datetime, days=1)
        start_default = fields.Datetime.to_string(start_default_datetime)
        end_default = fields.Datetime.to_string(end_default_datetime)
        form_values = {
            'customer_name': post.get('customer_name', '').strip(),
            'phone': post.get('phone', '').strip(),
            'email': post.get('email', '').strip(),
            'notes': post.get('notes', '').strip(),
            'start_local': post.get('start_local', ''),
            'end_local': post.get('end_local', ''),
            'start_utc': post.get('start_utc', ''),
            'end_utc': post.get('end_utc', ''),
        }
        errors = []
        is_check_request = 'check_availability' in post
        start_date = self._parse_datetime(form_values['start_utc'])
        end_date = self._parse_datetime(form_values['end_utc'])
        if request.httprequest.method == 'GET':
            start_date = start_default_datetime
            end_date = end_default_datetime

        if request.httprequest.method == 'POST':
            if not is_check_request:
                if not form_values['customer_name']:
                    errors.append(_('Vui lòng nhập họ tên.'))
                elif len(form_values['customer_name']) > 255:
                    errors.append(_('Họ tên không được dài quá 255 ký tự.'))
                if not form_values['phone']:
                    errors.append(_('Vui lòng nhập số điện thoại.'))
                elif len(form_values['phone']) > 32:
                    errors.append(_('Số điện thoại không được dài quá 32 ký tự.'))
                if len(form_values['email']) > 254:
                    errors.append(_('Email không được dài quá 254 ký tự.'))
                if len(form_values['notes']) > 2000:
                    errors.append(_('Ghi chú không được dài quá 2000 ký tự.'))
            if start_date is None or end_date is None:
                errors.append(_('Vui lòng chọn thời gian thuê hợp lệ.'))
            elif start_date < now:
                errors.append(_('Thời gian bắt đầu thuê không được ở trong quá khứ.'))
            elif end_date <= start_date:
                errors.append(_('Thời gian kết thúc phải sau thời gian bắt đầu.'))

        availability_start = start_date
        availability_end = end_date
        if (
            not availability_start
            or not availability_end
            or availability_end <= availability_start
        ):
            availability_start = start_default_datetime
            availability_end = end_default_datetime
        options = self._get_available_vehicles(availability_start, availability_end)
        try:
            current_vehicle_page = max(0, int(post.get('vehicle_page', 0)))
        except (TypeError, ValueError):
            current_vehicle_page = 0
        vehicles_per_page = 6
        vehicle_page_count = (
            (len(options) + vehicles_per_page - 1) // vehicles_per_page
        )
        if vehicle_page_count:
            current_vehicle_page = min(
                current_vehicle_page, vehicle_page_count - 1
            )
        else:
            current_vehicle_page = 0

        selected_vehicles = []
        allocated_vehicle_ids = set()
        quantities = {}
        for option in options:
            field_name = f"quantity_{option['vehicle_type'].id}"
            raw_quantity = post.get(field_name, '0')
            quantities[option['vehicle_type'].id] = raw_quantity
            try:
                quantity = int(raw_quantity)
            except (TypeError, ValueError):
                quantity = 0
                if request.httprequest.method == 'POST' and not is_check_request:
                    errors.append(_('Vui lòng nhập số lượng xe hợp lệ.'))
            if request.httprequest.method == 'POST' and not is_check_request:
                remaining_vehicles = option['vehicles'].filtered(
                    lambda vehicle: vehicle.id not in allocated_vehicle_ids
                )
                if quantity < 0:
                    errors.append(_('Số lượng xe không được âm.'))
                elif quantity > len(remaining_vehicles):
                    errors.append(
                        _(
                            'Dòng xe %(model)s chỉ còn %(count)s xe trong thời gian này.'
                        )
                        % {
                            'model': option['vehicle_type'].model_id.display_name,
                            'count': len(remaining_vehicles),
                        }
                    )
                elif quantity:
                    selected_vehicles.extend(
                        (vehicle, option['vehicle_type'])
                        for vehicle in remaining_vehicles[:quantity]
                    )
                    allocated_vehicle_ids.update(
                        remaining_vehicles[:quantity].ids
                    )

        if request.httprequest.method == 'POST' and not is_check_request:
            if not selected_vehicles:
                errors.append(_('Vui lòng chọn ít nhất một xe.'))

            rental_users = request.env.ref(
                'motorbike_rental_core.group_rental_user'
            ).sudo().users.filtered('active')
            if not rental_users:
                errors.append(
                    _(
                        'Chưa có nhân viên được cấp quyền Nhân viên thuê xe để nhận thông báo đặt xe.'
                    )
                )

            if not errors and selected_vehicles:
                try:
                    with request.env.cr.savepoint():
                        customer = request.env['res.partner'].sudo().create({
                            'name': form_values['customer_name'],
                            'phone': form_values['phone'],
                            'email': form_values['email'],
                            'is_rental_customer': True,
                        })
                        contract = request.env['rental.contract'].sudo().create({
                            'customer_id': customer.id,
                            'currency_id': request.website.company_id.currency_id.id,
                            'start_date': start_date,
                            'end_date': end_date,
                            'notes': form_values['notes'],
                            'line_ids': [
                                (0, 0, {
                                    'vehicle_id': vehicle.id,
                                    'vehicle_type_id': vehicle_type.id,
                                    'daily_rate': vehicle_type.daily_rate,
                                })
                                for vehicle, vehicle_type in selected_vehicles
                            ],
                        })
                        for rental_user in rental_users:
                            customer.sudo().activity_schedule(
                                'mail.mail_activity_data_todo',
                                summary=_('Yêu cầu thuê xe mới'),
                                note=_(
                                    'Khách đã gửi yêu cầu thuê xe trên website. '
                                    'Vui lòng kiểm tra hợp đồng %(contract)s '
                                    'và xác nhận nếu thông tin hợp lệ.'
                                ) % {'contract': contract.name},
                                user_id=rental_user.id,
                            )
                except ValidationError as error:
                    errors.append(str(error))
                else:
                    return request.redirect('/thue-xe?sent=1')

        return request.render('motorbike_rental_core.website_rental_booking', {
            'vehicles': options,
            'total_available': len({
                vehicle.id
                for option in options
                for vehicle in option['vehicles']
            }),
            'errors': errors,
            'form_values': form_values,
            'quantities': quantities,
            'start_default': start_default,
            'end_default': end_default,
            'vehicles_per_page': vehicles_per_page,
            'vehicle_count': len(options),
            'vehicle_page_count': vehicle_page_count,
            'current_vehicle_page': current_vehicle_page,
            'vehicle_page_start': (
                current_vehicle_page * vehicles_per_page + 1
                if options else 0
            ),
            'vehicle_page_end': min(
                (current_vehicle_page + 1) * vehicles_per_page,
                len(options),
            ),
            'success': request.params.get('sent') == '1',
        })

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

    @staticmethod
    def _get_available_vehicles(start_date, end_date):
        company_currency = request.website.company_id.currency_id
        rental_types = request.env['rental.vehicle.type'].sudo().search(
            [
                ('active', '=', True),
                ('currency_id', '=', company_currency.id),
                ('model_id.vehicle_type', '=', 'bike'),
            ],
            order='name, id',
        )
        if not rental_types:
            return []

        all_vehicles = request.env['fleet.vehicle'].sudo().search(
            [
                ('active', '=', True),
                ('model_id', 'in', rental_types.mapped('model_id').ids),
            ],
            order='license_plate, id',
        )
        fleet_availability = all_vehicles.check_fleet_availability(
            start_date, end_date
        )
        fleet_ready_ids = {
            item['vehicle_id']
            for item in fleet_availability
            if item['fleet_ok']
        }
        fleet_ready_vehicles = all_vehicles.filtered(
            lambda vehicle: vehicle.id in fleet_ready_ids
        )

        busy_lines = request.env['rental.contract.line'].sudo().search([
            ('contract_id.state', 'in', ['confirmed', 'in_progress']),
            ('contract_id.start_date', '<', end_date),
            ('contract_id.end_date', '>', start_date),
        ])
        busy_vehicle_ids = set(busy_lines.mapped('vehicle_id').ids)
        available_vehicles = fleet_ready_vehicles.filtered(
            lambda vehicle: vehicle.id not in busy_vehicle_ids
        )

        options = []
        for rental_type in rental_types:
            model_vehicles = all_vehicles.filtered(
                lambda vehicle: vehicle.model_id == rental_type.model_id
            )
            model_available_vehicles = available_vehicles.filtered(
                lambda vehicle: vehicle.model_id == rental_type.model_id
            )
            model_name = rental_type.model_id.name.casefold()
            illustration = (
                'evo-grand.svg' if 'evo grand' in model_name
                else 'evo.svg' if 'evo' in model_name
                else 'feliz.svg' if 'feliz' in model_name
                else 'electric-scooter.svg'
            )
            image = (
                'evo-grand.webp' if 'evo grand' in model_name
                else 'evo.jpg' if 'evo' in model_name
                else 'feliz.webp' if 'feliz' in model_name
                else None
            )
            options.append({
                'vehicle_type': rental_type,
                'image_url': (
                    f'/motorbike_rental_core/static/src/img/{image}'
                    if image
                    else (
                        f'/web/image/fleet.vehicle.model/'
                        f'{rental_type.model_id.id}/image_512'
                        if rental_type.model_id.image_128
                        else f'/motorbike_rental_core/static/src/img/{illustration}'
                    )
                ),
                'total_count': len(model_vehicles),
                'available_count': len(model_available_vehicles),
                'vehicles': model_available_vehicles,
            })
        return options
