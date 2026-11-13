import math
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


_VEHICLE_AVAILABILITY_LOCK_NAMESPACE = 0x52434F4E
_DEFAULT_RENTAL_DEPOSIT = 1_000_000


class RentalContract(models.Model):
    _name = 'rental.contract'
    _description = 'Hợp đồng thuê xe'
    _order = 'start_date desc, id desc'
    _sql_constraints = [
        (
            'valid_rental_date_range',
            'CHECK(end_date > start_date)',
            'Ngày kết thúc phải sau ngày bắt đầu.',
        ),
        (
            'nonnegative_rental_deposit',
            'CHECK(deposit_amount >= 0)',
            'Tiền đặt cọc không được âm.',
        ),
    ]

    name = fields.Char(string='Mã hợp đồng', required=True, copy=False, default='/')
    customer_id = fields.Many2one(
        'res.partner', string='Khách hàng', required=True, ondelete='restrict', index=True
    )
    customer_name = fields.Char(
        string='Họ tên khách hàng',
        related='customer_id.name',
        readonly=False,
    )
    customer_phone = fields.Char(
        string='Số điện thoại',
        related='customer_id.phone',
        readonly=False,
    )
    customer_email = fields.Char(
        string='Email',
        related='customer_id.email',
        readonly=False,
    )
    customer_id_number = fields.Char(
        string='Số CCCD/CMND',
        related='customer_id.rental_id_number',
        readonly=False,
    )
    start_date = fields.Datetime(
        string='Ngày giờ bắt đầu', required=True, default=fields.Datetime.now
    )
    end_date = fields.Datetime(
        string='Ngày giờ kết thúc',
        required=True,
        default=lambda self: fields.Datetime.add(fields.Datetime.now(), days=1),
    )
    calendar_title = fields.Char(
        string='Tiêu đề lịch thuê',
        compute='_compute_calendar_title',
    )
    rental_days = fields.Integer(
        string='Số ngày thuê',
        compute='_compute_rental_days',
        inverse='_inverse_rental_days',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ', required=True,
        default=lambda self: self.env.ref('base.VND'),
    )
    deposit_amount = fields.Monetary(
        string='Tiền đặt cọc',
        required=True,
        compute='_compute_deposit_amount',  # Tự tính cọc, nhân viên không nhập số tiền tùy ý.
        store=True,  # Lưu số tiền vào database để Finance và quyết toán đọc lại.
        precompute=True,  # Tính ngay khi tạo hợp đồng, trước khi Finance tạo phiếu cọc.
        currency_field='currency_id',
    )
    line_ids = fields.One2many(
        'rental.contract.line', 'contract_id', string='Xe thuê', copy=True
    )
    extension_ids = fields.One2many(
        'rental.extension', 'contract_id', string='Yêu cầu gia hạn', copy=False
    )
    vehicle_summary = fields.Char(
        string='Xe thuê',
        compute='_compute_vehicle_summary',
        store=True,
    )
    total_amount = fields.Monetary(
        string='Tổng tiền thuê',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id',
    )
    state = fields.Selection(
        [
            ('draft', 'Nháp'),
            ('confirmed', 'Đã xác nhận'),
            ('in_progress', 'Đang thuê'),
            ('done', 'Hoàn tất'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='draft',
        copy=False,
        index=True,
    )
    notes = fields.Text(string='Ghi chú')

    @api.depends('name', 'start_date', 'end_date')
    def _compute_calendar_title(self):
        for contract in self:
            if not contract.start_date or not contract.end_date:
                contract.calendar_title = contract.name
                continue
            start = fields.Datetime.context_timestamp(contract, contract.start_date)
            end = fields.Datetime.context_timestamp(contract, contract.end_date)
            contract.calendar_title = '%s | %s - %s' % (
                contract.name,
                start.strftime('%d/%m/%Y %H:%M'),
                end.strftime('%d/%m/%Y %H:%M'),
            )

    @api.depends('start_date', 'end_date')
    def _compute_rental_days(self):
        for contract in self:
            days = 0
            if contract.start_date and contract.end_date:
                seconds = (contract.end_date - contract.start_date).total_seconds()
                if seconds > 0:
                    days = max(1, math.ceil(seconds / 86400))
            contract.rental_days = max(days, 0)

    def _inverse_rental_days(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError(_('Chỉ hợp đồng nháp mới được chỉnh sửa số ngày thuê.'))
            if contract.rental_days < 1:
                raise ValidationError(_('Số ngày thuê phải từ 1 ngày trở lên.'))
            if contract.start_date:
                contract.end_date = fields.Datetime.add(
                    contract.start_date, days=contract.rental_days
                )

    @api.depends('line_ids', 'line_ids.subfleet')  # Tính lại khi thêm/bỏ xe hoặc đánh dấu xe thay thế.
    def _compute_deposit_amount(self):  # Tính cọc 1 triệu/xe gốc cho bản nháp; giữ cọc đã chốt sau khi ký.
        for contract in self:  # Xử lý riêng từng hợp đồng.
            if contract.state == 'draft':  # Chỉ hợp đồng nháp được cập nhật số tiền cọc.
                original_lines = contract.line_ids.filtered(lambda line: not line.subfleet)  # Bỏ xe thay thế để đổi A sang B không thu thêm cọc.
                contract.deposit_amount = len(original_lines) * _DEFAULT_RENTAL_DEPOSIT  # Mỗi dòng là một xe: 3 xe = 3 triệu; chưa có xe = 0.
            else:  # Đã ký, đang thuê, hoàn tất hoặc hủy: giữ nguyên tiền cọc lịch sử.
                contract.deposit_amount = contract.deposit_amount  # Không tính lại cọc khi thêm xe thay thế sau khi ký.

    @api.depends('line_ids.subtotal', 'currency_id')
    def _compute_total_amount(self):
        for contract in self:
            total = sum(contract.line_ids.mapped('subtotal'))
            contract.total_amount = (
                contract.currency_id.round(total) if contract.currency_id else total
            )

    @api.depends(
        'line_ids.vehicle_id',
        'line_ids.vehicle_id.name',
        'line_ids.vehicle_id.license_plate',
    )
    def _compute_vehicle_summary(self):
        for contract in self:
            contract.vehicle_summary = ', '.join(
                contract.line_ids.mapped('vehicle_id.display_name')
            )

    @api.model_create_multi
    def create(self, vals_list):
        default_state = self.default_get(['state']).get('state', 'draft')
        for vals in vals_list:
            if vals.get('deposit_amount', 0) < 0:
                raise ValidationError(_('Tiền đặt cọc không được âm.'))
            if vals.get('state', default_state) != 'draft':
                raise UserError(_('Hợp đồng mới phải ở trạng thái Nháp.'))
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.contract') or '/'
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('deposit_amount', 0) < 0:
            raise ValidationError(_('Tiền đặt cọc không được âm.'))
        # Ghi chú được sửa sau khi ký; Finance được cập nhật trạng thái quyết toán.
        # Cả hai trường hợp đều không cho sửa lại hợp đồng đã hủy.
        if self.filtered(lambda contract: contract.state == 'cancelled') and vals:
            raise UserError(_('Không thể chỉnh sửa hợp đồng đã hủy.'))
        allowed_after_confirmation = {'state', 'notes', 'settlement_status'}
        if self._is_approved_extension_update(vals):
            allowed_after_confirmation.add('end_date')
        if set(vals) - allowed_after_confirmation:
            locked_contract = self.filtered(lambda contract: contract.state != 'draft')
            if locked_contract:
                raise UserError(
                    _('Không thể chỉnh sửa hợp đồng sau khi đã xác nhận hoặc kết thúc.')
                )
        if 'state' in vals:
            if vals['state'] == 'cancelled' and self._contracts_with_started_delivery():
                raise UserError(
                    _(
                        'Không thể hủy hợp đồng sau khi đã bắt đầu giao xe. '
                        'Vui lòng thu hồi xe và hoàn tất hợp đồng theo quy trình hóa đơn.'
                    )
                )
            transitions = {
                'draft': {'confirmed', 'cancelled'},
                'confirmed': {'in_progress', 'cancelled'},
                'in_progress': {'done'},
                'done': set(),
                'cancelled': set(),
            }
            state_labels = dict(self._fields['state'].selection)
            for contract in self:
                target_state = vals['state']
                if (
                    target_state != contract.state
                    and target_state not in transitions.get(contract.state, set())
                ):
                    raise UserError(
                        _('Không thể chuyển hợp đồng từ "%(current)s" sang "%(target)s".')
                        % {
                            'current': state_labels.get(contract.state, contract.state),
                            'target': state_labels.get(target_state, target_state),
                        }
                    )
        return super().write(vals)

    def _is_approved_extension_update(self, vals):
        extension_id = self.env.context.get('rental_extension_id')
        if (
            set(vals) != {'end_date'}
            or not extension_id
            or len(self) != 1
        ):
            return False
        extension = self.env['rental.extension'].sudo().browse(extension_id).exists()
        return bool(
            extension
            and extension.state == 'approved'
            and extension.contract_id == self
            and extension.requested_end_date == vals['end_date']
            and (
                extension.requested_by == self.env.user
                or self.env.user.has_group(
                    'motorbike_rental_core.group_rental_manager'
                )
            )
        )

    def _contracts_with_started_delivery(self):
        started_contracts = self.filtered(
            lambda contract: contract.state == 'in_progress'
        )
        if self and 'rental.operation.ticket.vehicle' in self.env.registry:
            delivery_lines = self.env['rental.operation.ticket.vehicle'].sudo().search(
                [
                    ('ticket_id.contract_id', 'in', self.ids),
                    ('status', 'in', ['delivering', 'renting', 'returned']),
                ]
            )
            started_contracts |= delivery_lines.mapped('ticket_id.contract_id')
        return started_contracts

    def unlink(self):
        if self.filtered(lambda contract: contract.state != 'draft'):
            raise UserError(
                _('Không thể xóa hợp đồng sau khi đã xác nhận hoặc kết thúc.')
            )
        return super().unlink()

    @api.constrains(
        'start_date', 'end_date', 'deposit_amount', 'state', 'line_ids'
    )
    def _check_rental_period(self):
        for contract in self:
            if contract.deposit_amount < 0:
                raise ValidationError(_('Tiền đặt cọc không được âm.'))
            if not contract.start_date or not contract.end_date:
                continue
            if contract.end_date <= contract.start_date:
                raise ValidationError(_('Ngày kết thúc phải sau ngày bắt đầu.'))
            if contract.state in ('confirmed', 'in_progress'):
                if not contract.line_ids:
                    raise ValidationError(_('Hợp đồng phải có ít nhất một xe để xác nhận.'))
                contract._check_vehicle_availability()

    def _check_vehicle_availability(self, end_date=None, lines=None):  # Kiểm tra lịch riêng của từng xe; gia hạn chỉ truyền các xe được chọn.
        self.ensure_one()  # Mỗi lần xử lý một hợp đồng.
        lines = self.line_ids if lines is None else lines  # Không chọn riêng thì kiểm tra toàn bộ xe như lúc ký.
        for vehicle_id in sorted(set(lines.vehicle_id.ids)):  # Khóa theo thứ tự ID để hai nhân viên không giữ cùng xe đồng thời.
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', (_VEHICLE_AVAILABILITY_LOCK_NAMESPACE, vehicle_id))  # Dùng lại khóa lịch xe hiện có.
        for line in lines:  # Mỗi xe có thể kết thúc ở một ngày khác nhau.
            deadline = end_date or line.return_deadline or self.end_date  # Khi kiểm tra gia hạn dùng hạn đề nghị; bình thường dùng hạn riêng.
            conflict = self.env['rental.contract.line'].search([  # Kiểm tra cả các dữ liệu vừa thay đổi trong transaction hiện tại.
                ('contract_id', '!=', self.id),  # Bỏ chính hợp đồng đang xử lý.
                ('contract_id.state', 'in', ['confirmed', 'in_progress']),  # Chỉ lịch đã giữ hoặc đang thuê.
                ('contract_id.start_date', '<', deadline),  # Hai khoảng thời gian phải thực sự giao nhau.
                ('return_deadline', '>', self.start_date),  # Dùng hạn riêng, không dùng hạn muộn nhất của hợp đồng khác.
                ('vehicle_id', '=', line.vehicle_id.id),  # Chỉ kiểm tra cùng chiếc xe.
            ], limit=1)
            if conflict:  # Báo đúng xe và hợp đồng đang giữ lịch.
                raise ValidationError(_('Xe %s đã được giữ trong hợp đồng %s ở thời gian này.') % (line.vehicle_id.display_name, conflict.contract_id.name))
            with self.env.registry.cursor() as cursor:  # Đọc lại dữ liệu đã commit sau lúc chờ khóa để tránh nhận lịch cũ trong bộ nhớ.
                cursor.execute("""
                    SELECT contract.name
                      FROM rental_contract AS contract
                      JOIN rental_contract_line AS line ON line.contract_id = contract.id
                     WHERE contract.id != %s
                       AND contract.state IN ('confirmed', 'in_progress')
                       AND contract.start_date < %s
                       AND COALESCE(line.return_deadline, contract.end_date) > %s
                       AND line.vehicle_id = %s
                     LIMIT 1
                """, (self.id, deadline, self.start_date, line.vehicle_id.id))  # COALESCE dùng ngày chung cho dữ liệu cũ chưa có hạn riêng.
                fresh_conflict = cursor.fetchone()  # Không ghi dữ liệu qua kết nối phụ.
            if fresh_conflict:  # Có lịch mới được nhân viên khác xác nhận trước đó.
                raise ValidationError(_('Xe %s đã được giữ trong hợp đồng %s ở thời gian này.') % (line.vehicle_id.display_name, fresh_conflict[0]))

    def action_create_extension(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Chỉ hợp đồng đang thuê mới có thể yêu cầu gia hạn.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tạo yêu cầu gia hạn'),
            'res_model': 'rental.extension',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                **self.env.context,
                'default_contract_id': self.id,
            },
        }

    def action_confirm(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError(_('Chỉ hợp đồng nháp mới có thể được xác nhận.'))
            missing_customer_info = []
            if not contract.customer_id.name:
                missing_customer_info.append(_('họ tên'))
            if not contract.customer_id.phone:
                missing_customer_info.append(_('số điện thoại'))
            # Email là thông tin tùy chọn; khách vẫn có thể ký hợp đồng khi chưa có email.
            if not contract.customer_id.rental_id_number:
                missing_customer_info.append(_('số CCCD/CMND'))
            # Khi ký chỉ bắt buộc họ tên, số điện thoại và CCCD/CMND; email và tệp scan có thể bổ sung sau.
            if missing_customer_info:
                raise UserError(
                    _('Vui lòng bổ sung thông tin khách hàng trước khi xác nhận: %s.')
                    % ', '.join(missing_customer_info)
                )
            # Kiểm tra lại từng xe ngay lúc ký vì tình trạng Fleet có thể đã đổi sau khi chọn xe.
            for vehicle in contract.line_ids.mapped('vehicle_id'):
                # Fleet kiểm tra kỹ thuật, khóa thuê và lịch bảo dưỡng trong thời gian hợp đồng.
                fleet_ok = vehicle.check_fleet_availability(contract.start_date, contract.end_date)[0]['fleet_ok']
                # Chỉ xe đang sẵn sàng và đạt mọi điều kiện Fleet mới được đưa vào hợp đồng đã ký.
                if vehicle.operational_status != 'available' or not fleet_ok:
                    raise UserError(_('Xe %s chưa đủ điều kiện để ký hợp đồng.') % vehicle.display_name)
            contract.state = 'confirmed'

    def action_upload_customer_document(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Chỉ hợp đồng nháp mới được tải hồ sơ khách hàng.'))
        if not self.customer_id:
            raise UserError(_('Vui lòng chọn khách hàng trước khi tải hồ sơ.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tải scan thông tin khách hàng'),
            'res_model': 'rental.customer.document',
            'views': [(
                self.env.ref(
                    'motorbike_rental_core.view_rental_customer_document_form'
                ).id,
                'form',
            )],
            'view_mode': 'form',
            'target': 'new',
            'context': {
                **self.env.context,
                'default_customer_id': self.customer_id.id,
                'default_name': _('Hồ sơ khách hàng - %s') % self.name,
                'default_notes': _('Tải từ hợp đồng nháp %s') % self.name,
            },
        }

    def action_start(self):
        for contract in self:
            if contract.state != 'confirmed':
                raise UserError(_('Chỉ hợp đồng đã xác nhận mới có thể bắt đầu.'))
            contract.state = 'in_progress'

    def action_done(self):
        for contract in self:
            if contract.state != 'in_progress':
                raise UserError(_('Chỉ hợp đồng đang thuê mới có thể hoàn tất.'))
            contract.state = 'done'

    def action_cancel(self):
        for contract in self:
            if contract.state in ('done', 'cancelled'):
                raise UserError(_('Không thể hủy hợp đồng đã hoàn tất hoặc đã hủy.'))
            contract.state = 'cancelled'

class RentalContractLine(models.Model):
    _name = 'rental.contract.line'
    _description = 'Xe trong hợp đồng thuê'
    _order = 'id'

    contract_id = fields.Many2one(
        'rental.contract', string='Hợp đồng', required=True, ondelete='cascade', index=True
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Xe thuê',
        required=True,
        ondelete='restrict',
        index=True,
    )
    _sql_constraints = [
        (
            'unique_contract_vehicle',
            'UNIQUE(contract_id, vehicle_id)',
            'Mỗi xe chỉ được xuất hiện một lần trong một hợp đồng!',
        ),
        (
            'nonnegative_daily_rate',
            'CHECK(daily_rate >= 0)',
            'Giá thuê mỗi ngày không được âm.',
        ),
    ]
    vehicle_type_id = fields.Many2one(
        'rental.vehicle.type',
        string='Dòng xe / bảng giá',
        required=True,
        ondelete='restrict',
        domain=[('active', '=', True)],
    )
    vehicle_model_id = fields.Many2one(
        related='vehicle_type_id.model_id', string='Dòng xe', readonly=True
    )
    available_vehicle_ids = fields.Many2many(  # Danh sách xe được phép xuất hiện trong ô chọn xe của dòng này.
        'fleet.vehicle', compute='_compute_available_vehicle_ids',  # Chỉ tính để lọc giao diện, không lưu danh sách vào database.
    )
    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id', store=True, readonly=True
    )
    daily_rate = fields.Monetary(
        string='Giá thuê mỗi ngày', required=True, default=0, currency_field='currency_id'
    )
    # Xe gốc mặc định False; quy trình Đổi xe tự đánh dấu True cho xe thay thế.
    subfleet = fields.Boolean(string='Xe thay thế', default=False, readonly=True)
    return_deadline = fields.Datetime(  # Hạn trả riêng; ngày kết thúc chung chỉ là hạn muộn nhất.
        string='Hạn trả xe', compute='_compute_return_deadline', store=True, precompute=True,
    )
    rental_days = fields.Integer(string='Số ngày thuê xe', compute='_compute_line_rental_days', store=True)  # Số ngày tính riêng từ lúc bắt đầu hợp đồng.
    billing_line_id = fields.Many2one('rental.contract.line', string='Dòng xe gốc tính tiền', compute='_compute_billing_line_id', store=True, precompute=True, readonly=True, copy=False, ondelete='restrict')  # Xe đổi B/C cùng quy về dòng A, kể cả lịch sử đổi xe cũ.
    replacement_line_ids = fields.One2many('rental.contract.line', 'billing_line_id')  # Các xe thay thế thuộc cùng một khoản tiền thuê gốc.
    subtotal = fields.Monetary(
        string='Thành tiền', compute='_compute_subtotal', store=True, currency_field='currency_id'
    )
    # Ghi chú riêng cho dòng xe, độc lập với ghi chú chung của hợp đồng.
    notes = fields.Text(string='Ghi chú từng xe')

    @api.depends('contract_id.end_date')  # Bản nháp dùng ngày chung; sau ký giữ từng hạn riêng.
    def _compute_return_deadline(self):  # Khởi tạo hạn trả và không kéo dài xe khác khi chỉ một xe gia hạn.
        for line in self:  # Tính riêng mỗi xe.
            line.return_deadline = line.contract_id.end_date if line.contract_id.state == 'draft' or not line.return_deadline else line.return_deadline  # Hợp đồng cũ chưa có hạn riêng lấy ngày chung hiện tại.

    @api.depends('contract_id.start_date', 'return_deadline')  # Ngày trả của xe quyết định số ngày thuê riêng.
    def _compute_line_rental_days(self):  # Tính số ngày thuê xe, làm tròn lên theo quy tắc 24 giờ hiện có.
        for line in self:  # Không dùng số ngày của cả hợp đồng để tính từng xe.
            seconds = (line.return_deadline - line.contract_id.start_date).total_seconds() if line.return_deadline and line.contract_id.start_date else 0  # Chưa đủ ngày thì bằng 0.
            line.rental_days = max(1, math.ceil(seconds / 86400)) if seconds > 0 else 0  # Thuê một phần ngày vẫn tính một ngày.

    @api.depends('subfleet', 'vehicle_id', 'contract_id')  # Khôi phục liên kết tính tiền từ lịch sử đổi xe khi nâng cấp dữ liệu cũ.
    def _compute_billing_line_id(self):  # Tìm xe gốc của chuỗi A→B→C để gia hạn B/C không bỏ sót hoặc tính trùng tiền.
        for line in self:  # Xe gốc không cần liên kết tới chính nó.
            original = line  # Bắt đầu lần ngược từ chiếc xe hiện tại.
            visited = set()  # Chặn vòng lặp nếu dữ liệu lịch sử có vấn đề.
            while original.subfleet and original.id not in visited and 'rental.vehicle.exchange' in self.env.registry:  # Core vẫn chạy khi chưa cài Operation.
                visited.add(original.id)  # Mỗi dòng chỉ được duyệt một lần.
                exchange = self.env['rental.vehicle.exchange'].sudo().search([('ticket_id.contract_id', '=', line.contract_id.id), ('vehicle_b_id', '=', original.vehicle_id.id), ('status', 'in', ['confirmed', 'done'])], limit=1)  # Đọc lại lượt đổi đã đưa chiếc xe này vào hợp đồng.
                previous = line.contract_id.line_ids.filtered(lambda item: item.vehicle_id == exchange.vehicle_a_id)[:1]  # Xe A ngay trước đó trong chuỗi.
                if not previous:  # Không suy đoán dòng gốc nếu lịch sử không đủ dữ liệu.
                    break
                original = previous  # Tiếp tục lần ngược nếu A cũng từng là xe thay thế.
            line.billing_line_id = original if original != line and not original.subfleet else False  # Chỉ chốt khi tìm được dòng gốc thực sự.

    @api.depends('vehicle_id', 'vehicle_id.license_plate')  # Đổi xe thì cập nhật tên trong ô chọn gia hạn.
    def _compute_display_name(self):  # Hiển thị tên và biển số xe thay vì mã kỹ thuật của dòng hợp đồng.
        for line in self:  # Dùng cách đặt tên có sẵn của Fleet.
            line.display_name = line.vehicle_id.display_name or _('Chưa chọn xe')  # Cho phép form mới chưa chọn xe.

    @api.depends('rental_days', 'replacement_line_ids.rental_days', 'daily_rate', 'currency_id', 'subfleet')
    def _compute_subtotal(self):  # Tính tiền riêng từng xe; xe thay thế cộng thời gian vào dòng gốc, không tạo tiền thuê thứ hai.
        for line in self:
            # Xe thay thế vẫn hiện giá mỗi ngày, nhưng không tính thêm tiền thuê.
            days = max([line.rental_days] + line.replacement_line_ids.mapped('rental_days'))  # Gia hạn xe B sau đổi A→B được tính một lần vào A.
            amount = 0.0 if line.subfleet else days * line.daily_rate  # Xe không được gia hạn giữ tiền thuê cũ.
            line.subtotal = line.currency_id.round(amount) if line.currency_id else amount

    @api.depends('vehicle_type_id', 'contract_id.start_date', 'contract_id.end_date', 'contract_id.line_ids.vehicle_id')  # Đổi dòng xe, ngày thuê hoặc xe đã chọn thì tính lại danh sách.
    def _compute_available_vehicle_ids(self):  # Lọc xe sẵn sàng, đạt kỹ thuật và không bận trong khoảng thuê của hợp đồng.
        for line in self:  # Mỗi dòng xe có bảng giá và danh sách lựa chọn riêng.
            contract = line.contract_id  # Đọc thời gian thuê từ hợp đồng đang nhập.
            available = self.env['fleet.vehicle']  # Mặc định danh sách rỗng khi chưa nhập đủ điều kiện.
            if line.vehicle_type_id and contract.start_date and contract.end_date and contract.end_date > contract.start_date:  # Chỉ tìm khi có dòng xe và khoảng thuê hợp lệ.
                candidates = self.env['fleet.vehicle'].search([  # Lọc trước theo trạng thái hiện tại để không đưa xe hỏng/đang thuê vào danh sách.
                    ('active', '=', True),  # Không lấy xe đã lưu trữ.
                    ('model_id', '=', line.vehicle_type_id.model_id.id),  # Đúng dòng xe của bảng giá đã chọn.
                    ('operational_status', '=', 'available'),  # Chỉ xe đang sẵn sàng.
                    ('technical_ready', '=', True),  # Đã đạt điều kiện kỹ thuật.
                    ('rental_blocked', '=', False),  # Không bị Fleet khóa thuê.
                ])
                checks = candidates.check_fleet_availability(contract.start_date, contract.end_date)  # Dùng lại kiểm tra Fleet, gồm cả lịch bảo dưỡng và danh mục xe.
                ready_ids = [check['vehicle_id'] for check in checks if check['fleet_ok']]  # Chỉ giữ xe vượt qua toàn bộ kiểm tra Fleet.
                busy_lines = self.env['rental.contract.line'].search([  # Tìm hợp đồng đã giữ xe hoặc đang thuê bị giao thời gian.
                    ('contract_id', '!=', contract._origin.id or 0),  # Không coi chính hợp đồng đang chỉnh sửa là lịch bận khác.
                    ('contract_id.state', 'in', ['confirmed', 'in_progress']),  # Hợp đồng nháp/hủy/hoàn tất không giữ lịch thuê.
                    ('contract_id.start_date', '<', contract.end_date),  # Hợp đồng khác bắt đầu trước lúc chuyến này kết thúc.
                    ('return_deadline', '>', contract.start_date),  # Chỉ giữ xe tới hạn trả riêng của xe đó.
                    ('vehicle_id', 'in', ready_ids),  # Chỉ xét xe trong nhóm ứng viên đạt Fleet.
                ])
                other_lines = contract.line_ids.filtered(lambda other: other != line)  # Các dòng khác trong cùng hợp đồng.
                excluded = busy_lines.vehicle_id | other_lines.vehicle_id._origin  # _origin lấy xe thật từ dữ liệu form chưa lưu để loại đúng xe đã chọn.
                available = candidates.browse(ready_ids) - excluded  # Danh sách cuối cùng cho ô chọn xe.
            line.available_vehicle_ids = available  # Trả danh sách cho bộ lọc domain của giao diện.

    @api.onchange('vehicle_type_id')
    def _onchange_vehicle_type_id(self):
        if self.vehicle_type_id:
            self.daily_rate = self.vehicle_type_id.daily_rate
            if (
                self.vehicle_id
                and self.vehicle_id.model_id != self.vehicle_type_id.model_id
            ):
                self.vehicle_id = False
        # Không trả bộ lọc cũ chỉ theo dòng xe; giao diện dùng available_vehicle_ids ở trên.

    @api.model_create_multi
    def create(self, vals_list):
        default_contract_id = self.default_get(['contract_id']).get('contract_id')
        for vals in vals_list:
            contract_id = vals.get('contract_id', default_contract_id)
            contract = self.env['rental.contract'].browse(contract_id)
            if contract and contract.state != 'draft':
                raise UserError(
                    _('Không thể thêm xe vào hợp đồng sau khi đã xác nhận.')
                )
            if vals.get('vehicle_type_id') and 'daily_rate' not in vals:
                vehicle_type = self.env['rental.vehicle.type'].browse(vals['vehicle_type_id'])
                vals['daily_rate'] = vehicle_type.daily_rate
        return super().create(vals_list)

    def write(self, vals):
        extension = self.env['rental.extension'].browse(self.env.context.get('rental_extension_id')).exists()  # Chỉ yêu cầu gia hạn đã được xử lý mới được sửa hạn trả sau ký.
        if extension and set(vals) == {'return_deadline'} and extension.state == 'approved' and not (self - extension.line_ids) and vals['return_deadline'] == extension.requested_end_date:  # Không cho dùng gia hạn để sửa xe khác hoặc trường khác.
            if extension.requested_by == self.env.user or self.env.user.has_group('motorbike_rental_core.group_rental_manager'):  # Giữ quyền của người tạo và quản lý như luồng cũ.
                return super().write(vals)  # Lưu đúng hạn trả được duyệt; những trường hợp khác vẫn qua chốt khóa cũ bên dưới.
        contracts = self.mapped('contract_id')
        if vals.get('contract_id'):
            contracts |= self.env['rental.contract'].browse(vals['contract_id'])
        if contracts.filtered(lambda contract: contract.state != 'draft'):
            raise UserError(
                _('Không thể chỉnh sửa xe trong hợp đồng sau khi đã xác nhận.')
            )
        return super().write(vals)

    def unlink(self):
        if self.mapped('contract_id').filtered(
            lambda contract: contract.state != 'draft'
        ):
            raise UserError(
                _('Không thể xóa xe khỏi hợp đồng sau khi đã xác nhận.')
            )
        return super().unlink()

    @api.constrains('vehicle_id', 'vehicle_type_id', 'contract_id', 'daily_rate')
    def _check_vehicle_line(self):
        for line in self:
            if line.daily_rate < 0:
                raise ValidationError(_('Giá thuê mỗi ngày không được âm.'))
            if not line.vehicle_type_id or not line.contract_id:
                continue
            if not line.vehicle_id.active:
                raise ValidationError(_('Không thể cho thuê xe đã lưu trữ.'))
            if not line.vehicle_type_id.active:
                raise ValidationError(_('Không thể sử dụng bảng giá đã lưu trữ.'))
            if line.vehicle_id.model_id != line.vehicle_type_id.model_id:
                raise ValidationError(
                    _('Dòng xe của bảng giá phải trùng với dòng xe thực tế.')
                )
            if line.vehicle_type_id.currency_id != line.contract_id.currency_id:
                raise ValidationError(
                    _('Tiền tệ của dòng giá phải trùng với tiền tệ trên hợp đồng.')
                )
            duplicate = self.search(
                [
                    ('id', '!=', line.id),
                    ('contract_id', '=', line.contract_id.id),
                    ('vehicle_id', '=', line.vehicle_id.id),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(_('Không thể thêm cùng một xe hai lần vào hợp đồng.'))
            if line.contract_id.state in ('confirmed', 'in_progress'):
                line.contract_id._check_vehicle_availability()
