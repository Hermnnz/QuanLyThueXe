import math

from odoo import _, api, fields, models, Command  # Command.set gán chính xác danh sách xe được chọn.
from odoo.exceptions import UserError, ValidationError


_RENTAL_EXTENSION_LOCK_NAMESPACE = 0x52455854


class RentalExtension(models.Model):
    _name = 'rental.extension'
    _description = 'Yêu cầu gia hạn thuê xe'
    _order = 'requested_at desc, id desc'

    name = fields.Char(
        string='Mã yêu cầu',
        required=True,
        readonly=True,
        copy=False,
        default='/',
    )
    contract_id = fields.Many2one(
        'rental.contract',
        string='Hợp đồng',
        required=True,
        ondelete='restrict',
        index=True,
    )
    customer_id = fields.Many2one(
        related='contract_id.customer_id',
        string='Khách hàng',
        readonly=True,
    )
    select_all = fields.Boolean(string='Chọn tất cả xe đang thuê', default=True)  # Bỏ tích để chọn một hoặc nhiều xe riêng.
    line_ids = fields.Many2many('rental.contract.line', 'rental_extension_line_rel', 'extension_id', 'line_id', string='Xe cần gia hạn', copy=False)  # Lưu đúng xe được gia hạn để giữ lịch sử.
    eligible_line_ids = fields.Many2many('rental.contract.line', compute='_compute_eligible_lines')  # Danh sách cho ô chọn; loại xe đã trả, chưa giao hoặc đang đổi dở.
    currency_id = fields.Many2one(
        related='contract_id.currency_id',
        string='Tiền tệ',
        readonly=True,
    )
    original_end_date = fields.Datetime(
        string='Thời gian trả hiện tại',
        required=True,
        readonly=True,
        copy=False,
    )
    original_rental_days = fields.Integer(
        string='Số ngày thuê hiện tại',
        required=True,
        readonly=True,
        copy=False,
    )
    requested_end_date = fields.Datetime(
        string='Thời gian trả đề nghị',
        required=True,
        copy=False,
    )
    additional_days = fields.Integer(
        string='Số ngày tăng thêm',
        compute='_compute_additional_amount',
        store=True,
    )
    additional_amount = fields.Monetary(
        string='Tiền thuê tăng thêm',
        compute='_compute_additional_amount',
        store=True,
        currency_field='currency_id',
    )
    reason = fields.Text(string='Lý do gia hạn', required=True)
    state = fields.Selection(
        [
            ('pending', 'Chờ kiểm tra'),
            ('approved', 'Đã gia hạn'),
            ('rejected', 'Từ chối'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='pending',
        readonly=True,
        copy=False,
        index=True,
    )
    requested_by = fields.Many2one(
        'res.users',
        string='Người tạo yêu cầu',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )
    requested_at = fields.Datetime(
        string='Thời điểm yêu cầu',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
    )
    reviewed_by = fields.Many2one(
        'res.users', string='Người kiểm tra/xử lý', readonly=True, copy=False
    )
    reviewed_at = fields.Datetime(
        string='Thời điểm xử lý', readonly=True, copy=False
    )
    rejection_reason = fields.Text(string='Lý do từ chối')

    def _lock_contract(self, contract):
        contract.flush_recordset(['state', 'end_date', 'rental_days'])
        self.env.cr.execute(
            'SELECT id FROM rental_contract WHERE id = %s FOR UPDATE',
            (contract.id,),
        )
        contract.invalidate_recordset(['state', 'end_date', 'rental_days'])
        contract.line_ids.invalidate_recordset(['return_deadline', 'rental_days'])  # Sau khi chờ khóa phải đọc lại hạn trả từng xe.

    def _get_eligible_lines(self, contract):  # Lấy những xe thực sự đang thuê thuộc đúng hợp đồng này.
        lines = contract.line_ids  # Bắt đầu từ lịch sử xe trong hợp đồng.
        if 'rental.operation.ticket.vehicle' in self.env.registry:  # Khi có Operation, trạng thái giao/thu hồi là nguồn xác định xe đang ở khách.
            operation_lines = self.env['rental.operation.ticket.vehicle'].sudo().search([('ticket_id.contract_id', '=', contract.id)])  # Đọc nội bộ để nhân viên Core không cần quyền ghi Operation.
            if operation_lines:  # Có phiếu vận hành thì chỉ xe đã giao và chưa trả mới được gia hạn.
                lines = lines.filtered(lambda line: line.vehicle_id.id in operation_lines.filtered(lambda item: item.status == 'renting').vehicle_id.ids)  # Bỏ xe đã thu hồi và xe chờ giao.
            if 'rental.vehicle.exchange' in self.env.registry:  # Không kéo dài xe A trong khi đang làm thủ tục A→B.
                exchanges = self.env['rental.vehicle.exchange'].sudo().search([('ticket_id.contract_id', '=', contract.id), ('status', '=', 'confirmed')])  # Sau khi đổi hoàn tất, B có thể gia hạn bình thường.
                lines = lines.filtered(lambda line: line.vehicle_id not in exchanges.vehicle_a_id)  # Chờ hoàn tất lượt đổi rồi gia hạn đúng xe đang sử dụng.
        return lines  # Không loại subfleet: xe thay thế B đang thuê cũng phải chọn được.

    @api.depends('contract_id')  # Chọn hợp đồng khác phải lấy lại danh sách xe.
    def _compute_eligible_lines(self):  # Cung cấp danh sách xe hợp lệ cho giao diện.
        for extension in self:  # Mỗi yêu cầu có một hợp đồng riêng.
            extension.eligible_line_ids = self._get_eligible_lines(extension.contract_id) if extension.contract_id else False  # Chưa chọn hợp đồng thì danh sách rỗng.

    @api.onchange('select_all', 'contract_id')  # Tích Chọn tất cả thì điền các xe đang thuê; bỏ tích giữ lựa chọn để người dùng bỏ bớt.
    def _onchange_selected_contract(self):  # Đồng bộ ô chọn xe trên form chưa lưu.
        if self.select_all:  # Chọn tất cả chỉ có hiệu lực trên các xe đủ điều kiện hiện tại.
            self.line_ids = self._get_eligible_lines(self.contract_id)  # Không chọn cả xe đã trả hoặc xe A cũ đã thay.
        else:  # Khi đổi hợp đồng phải bỏ các xe không còn thuộc danh sách hợp lệ.
            eligible = self._get_eligible_lines(self.contract_id)  # Lấy các dòng thật trong database.
            self.line_ids = self.line_ids.filtered(lambda line: line._origin in eligible)  # _origin đối chiếu đúng dòng xe từ dữ liệu tạm trên form.

    @api.onchange('line_ids')  # Chọn lại nhóm xe thì hiển thị mốc trả hiện tại của nhóm đó.
    def _onchange_line_dates(self):  # Cập nhật thông tin tham chiếu và gợi ý hạn mới khi chọn xe.
        if self.line_ids:  # Nhóm xe có thể đang có các hạn trả khác nhau.
            self.original_end_date = max(self.line_ids.mapped('return_deadline'))  # Hiển thị hạn muộn nhất trong nhóm được chọn.
            self.original_rental_days = max(self.line_ids.mapped('rental_days'))  # Số ngày hiện tại lớn nhất của nhóm.
            if not self.requested_end_date or self.requested_end_date <= self.original_end_date:  # Không tự thay ngày hợp lệ nhân viên đã nhập.
                self.requested_end_date = fields.Datetime.add(self.original_end_date, days=1)  # Gợi ý thêm một ngày sau hạn hiện tại.

    def _selection_values(self, contract, values):  # Chuẩn hóa và kiểm tra xe được chọn trước khi lưu yêu cầu.
        eligible = self._get_eligible_lines(contract)  # Đọc lại trạng thái thật, không tin danh sách cũ trên form.
        selected = eligible if values.get('select_all', True) else self.new({'contract_id': contract.id, 'line_ids': values.get('line_ids', [])}).line_ids._origin  # Dữ liệu giao diện dùng lệnh Many2many, new giúp Odoo giải mã đúng.
        if not selected or selected - eligible:  # Không chấp nhận xe sai hợp đồng, chưa giao hoặc đã trả.
            raise UserError(_('Vui lòng chọn ít nhất một xe còn đang thuê và không trong lượt đổi xe chưa hoàn tất.'))
        return {'line_ids': [Command.set(selected.ids)], 'original_end_date': max(selected.mapped('return_deadline')), 'original_rental_days': max(selected.mapped('rental_days'))}  # Lưu nhóm xe và mốc ban đầu cho lịch sử.

    def _lock_extension(self):
        self.ensure_one()
        self.flush_recordset(['state'])
        self.env.cr.execute(
            'SELECT id FROM rental_extension WHERE id = %s FOR UPDATE',
            (self.id,),
        )
        self.invalidate_recordset(['state'])

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        contract_id = (
            defaults.get('contract_id')
            or self.env.context.get('default_contract_id')
        )
        if not contract_id:
            return defaults

        contract = self.env['rental.contract'].browse(contract_id).exists()
        if not contract:
            return defaults
        if contract.state != 'in_progress':
            raise UserError(_('Chỉ hợp đồng đang thuê mới có thể yêu cầu gia hạn.'))

        if 'original_end_date' in fields_list:
            defaults['original_end_date'] = contract.end_date
        if 'original_rental_days' in fields_list:
            defaults['original_rental_days'] = contract.rental_days
        selected = self._get_eligible_lines(contract)  # Mặc định chọn tất cả xe còn đang thuê.
        if 'line_ids' in fields_list:
            defaults['line_ids'] = [Command.set(selected.ids)]  # Điền các xe để form hiển thị rõ phạm vi gia hạn.
        if (
            'requested_end_date' in fields_list
            and not defaults.get('requested_end_date')
        ):
            defaults['requested_end_date'] = fields.Datetime.add(
                contract.end_date, days=1
            )
        return defaults

    @api.model_create_multi
    def create(self, vals_list):
        seen_contract_ids = set()
        for vals in vals_list:
            contract_id = (
                vals.get('contract_id')
                or self.env.context.get('default_contract_id')
            )
            contract = self.env['rental.contract'].browse(contract_id).exists()
            if not contract:
                raise ValidationError(_('Vui lòng chọn hợp đồng cần gia hạn.'))
            vals['contract_id'] = contract.id
            self._lock_contract(contract)
            if contract.state != 'in_progress':
                raise UserError(_('Chỉ hợp đồng đang thuê mới có thể yêu cầu gia hạn.'))
            if vals.get('state', 'pending') != 'pending':
                raise UserError(_('Yêu cầu gia hạn mới phải ở trạng thái Chờ kiểm tra.'))
            if contract.id in seen_contract_ids:
                raise UserError(
                    _('Chỉ được tạo một yêu cầu gia hạn chờ xử lý cho mỗi hợp đồng.')
                )
            seen_contract_ids.add(contract.id)

            self.env.cr.execute(
                'SELECT pg_advisory_xact_lock(%s, %s)',
                (_RENTAL_EXTENSION_LOCK_NAMESPACE, contract.id),
            )
            pending_request = self.search(
                [('contract_id', '=', contract.id), ('state', '=', 'pending')],
                limit=1,
            )
            if pending_request:
                raise UserError(
                    _('Hợp đồng này đang có một yêu cầu gia hạn chờ xử lý.')
                )
            vals.update({
                'name': (
                    self.env['ir.sequence'].next_by_code('rental.extension')
                    or '/'
                ),
                'original_end_date': contract.end_date,
                'original_rental_days': contract.rental_days,
                'requested_by': self.env.user.id,
                'requested_at': fields.Datetime.now(),
            })
            vals.update(self._selection_values(contract, vals))  # Ghi đè mốc chung bằng hạn hiện tại của nhóm xe được chọn.
            for readonly_field in (
                'reviewed_by', 'reviewed_at', 'rejection_reason'
            ):
                vals.pop(readonly_field, None)
        return super().create(vals_list)

    @api.depends('requested_end_date', 'line_ids', 'line_ids.return_deadline', 'line_ids.daily_rate', 'line_ids.billing_line_id.replacement_line_ids.rental_days', 'currency_id')
    def _compute_additional_amount(self):  # Chỉ tính phần ngày tăng của các xe được chọn; lịch sử đã duyệt giữ nguyên số tiền.
        for extension in self:  # Một yêu cầu có thể chọn nhiều xe với hạn trả hiện tại khác nhau.
            if extension.state != 'pending':  # Không để lần gia hạn sau làm đổi báo cáo lịch sử của lần trước.
                extension.additional_days = extension.additional_days  # Giữ số ngày đã chốt.
                extension.additional_amount = extension.additional_amount  # Giữ số tiền đã chốt.
                continue
            deltas = []  # Lưu số ngày tăng riêng cho từng xe.
            amount = 0  # Tổng tiền gia hạn chỉ gồm nhóm xe được chọn.
            for line in extension.line_ids:  # Xe không được chọn không phát sinh tiền.
                seconds = (extension.requested_end_date - extension.contract_id.start_date).total_seconds() if extension.requested_end_date and extension.contract_id.start_date else 0  # Tính từ cùng mốc bắt đầu để không thu trùng phần ngày đã trả tiền.
                new_days = max(1, math.ceil(seconds / 86400)) if seconds > 0 else 0  # Dùng quy tắc làm tròn ngày hiện tại.
                billing = line.billing_line_id or line  # Xe thay thế phải tính trên tiền thuê đã trả của dòng gốc.
                old_days = max([billing.rental_days] + billing.replacement_line_ids.mapped('rental_days'))  # A→B→C vẫn chỉ là một khoản tiền thuê.
                days = max(0, new_days - old_days)  # Không thu lại những ngày đã tính ở lần trước.
                deltas.append(days)  # Dùng để hiển thị số ngày tăng lớn nhất của nhóm.
                amount += days * billing.daily_rate  # Chỉ cộng giá của xe đang gia hạn, không cộng tất cả xe trong hợp đồng.
            extension.additional_days = max(deltas, default=0)  # Khi nhóm xe khác hạn, đây là số ngày tăng lớn nhất; tiền vẫn tính riêng từng xe.
            extension.additional_amount = extension.currency_id.round(amount) if extension.currency_id else amount  # Làm tròn theo đồng tiền hợp đồng.

    @api.constrains('requested_end_date', 'original_end_date')
    def _check_requested_end_date(self):
        for extension in self:
            if (
                extension.requested_end_date
                and extension.original_end_date
                and extension.requested_end_date <= extension.original_end_date
            ):
                raise ValidationError(
                    _('Thời gian trả đề nghị phải sau thời gian trả hiện tại.')
                )

    def write(self, vals):
        editable_fields = {'requested_end_date', 'reason', 'rejection_reason', 'line_ids', 'select_all'}  # Cho phép đổi nhóm xe khi yêu cầu còn chờ.
        if not vals or set(vals) - editable_fields:
            raise UserError(
                _('Không được sửa trực tiếp yêu cầu gia hạn; hãy dùng các nút xử lý.')
            )
        if self.filtered(lambda extension: extension.state != 'pending'):
            raise UserError(_('Chỉ yêu cầu đang chờ kiểm tra mới được chỉnh sửa.'))
        if {'line_ids', 'select_all'} & vals.keys():  # Cập nhật nhóm xe phải tính lại mốc cũ từ dữ liệu thật.
            for extension in self:  # Mỗi yêu cầu giữ nhóm xe và mốc riêng.
                values = {'select_all': extension.select_all, 'line_ids': [Command.set(extension.line_ids.ids)], **vals}  # Ghép thông tin cũ với lựa chọn mới.
                values.update(self._selection_values(extension.contract_id, values))  # Kiểm tra và chuẩn hóa danh sách.
                if extension.requested_by != self.env.user and not self.env.user.has_group('motorbike_rental_core.group_rental_manager'):  # Giữ giới hạn quyền sửa.
                    raise UserError(_('Chỉ người tạo yêu cầu hoặc quản lý mới được cập nhật.'))
                super(RentalExtension, extension).write(values)  # Lưu một lần cả nhóm xe và mốc ban đầu.
            return True  # Đã xử lý toàn bộ yêu cầu.
        if self.env.user.has_group('motorbike_rental_core.group_rental_manager'):
            return super().write(vals)
        # Nhân viên hợp đồng được nhập lý do từ chối yêu cầu của đồng nghiệp.
        if set(vals) == {'rejection_reason'} and self.env.user.has_group('motorbike_rental_core.group_rental_user'):
            return super().write(vals)
        if set(vals) - {'requested_end_date', 'reason'} or self.filtered(
            lambda extension: extension.requested_by != self.env.user
        ):
            raise UserError(
                _('Chỉ người tạo yêu cầu mới được cập nhật đề nghị đang chờ kiểm tra.')
            )
        return super().write(vals)

    def action_check_and_extend(self):
        for extension in self:
            extension._lock_extension()
            if extension.state != 'pending':
                raise UserError(_('Chỉ yêu cầu đang chờ kiểm tra mới được xử lý.'))
            contract = extension.contract_id
            self._lock_contract(contract)
            if contract.state != 'in_progress':
                raise UserError(
                    _('Chỉ hợp đồng đang thuê mới có thể gia hạn.')
                )
            eligible = extension._get_eligible_lines(contract)  # Kiểm tra lại ngay lúc bấm nút vì có thể xe vừa được thu hồi.
            if not extension.line_ids or extension.line_ids - eligible:  # Không gia hạn xe đã trả, xe sai hợp đồng hoặc đang đổi dở.
                raise UserError(_('Danh sách xe đã thay đổi; vui lòng chọn lại các xe còn đang thuê.'))
            if max(extension.line_ids.mapped('return_deadline')) != extension.original_end_date:  # Không áp dụng yêu cầu dựa trên hạn trả cũ.
                raise UserError(_('Hạn trả của xe đã thay đổi; vui lòng tạo yêu cầu gia hạn mới.'))
            contract._check_vehicle_availability(end_date=extension.requested_end_date, lines=extension.line_ids)  # Chỉ xe được chọn cần kiểm tra lịch kéo dài.
            for line in extension.line_ids:  # Fleet kiểm tra kỹ thuật, khóa thuê và bảo dưỡng của từng xe đang gia hạn.
                if not line.vehicle_id.check_fleet_availability(line.return_deadline, extension.requested_end_date)[0]['fleet_ok']:
                    raise UserError(_('Xe %s không đủ điều kiện Fleet để gia hạn.') % line.vehicle_id.display_name)
            extension.flush_recordset(['additional_amount', 'additional_days'])  # Chốt phép tính khi còn chờ, trước khi cập nhật hạn trả từng xe.
            contract.line_ids.mapped('return_deadline')  # Nạp đủ các hạn hiện tại trước khi thay đổi ngày kết thúc chung.
            super(RentalExtension, extension).write({
                'state': 'approved',
                'reviewed_by': self.env.user.id,
                'reviewed_at': fields.Datetime.now(),
            })
            extension.line_ids.with_context(rental_extension_id=extension.id).write({'return_deadline': extension.requested_end_date})  # Chỉ sửa hạn trả của các xe đã chọn.
            latest = max(contract.line_ids.mapped('return_deadline'))  # Ngày kết thúc hợp đồng là hạn trả muộn nhất.
            if latest != contract.end_date:  # Gia hạn xe khác tới trước hạn muộn nhất không cần đổi ngày chung.
                contract.with_context(rental_extension_id=extension.id).write({'end_date': latest})  # Dùng chốt quyền gia hạn có sẵn.
            extension._sync_operation_schedule()
        return {'type': 'ir.actions.act_window_close'}

    def action_reject(self):
        # Nhân viên hợp đồng và quản lý đều được từ chối yêu cầu gia hạn.
        self.check_access("write")
        for extension in self:
            extension._lock_extension()
            if extension.state != 'pending':
                raise UserError(_('Chỉ yêu cầu đang chờ kiểm tra mới được xử lý.'))
            if not (extension.rejection_reason or '').strip():
                raise UserError(_('Vui lòng nhập lý do từ chối.'))
            super(RentalExtension, extension).write({
                'state': 'rejected',
                'reviewed_by': self.env.user.id,
                'reviewed_at': fields.Datetime.now(),
            })
        return True

    def action_cancel(self):
        for extension in self:
            extension._lock_extension()
            if extension.state != 'pending':
                raise UserError(_('Chỉ yêu cầu đang chờ kiểm tra mới có thể hủy.'))
            if (
                extension.requested_by != self.env.user
                and not self.env.user.has_group(
                    'motorbike_rental_core.group_rental_manager'
                )
            ):
                raise UserError(_('Chỉ người tạo yêu cầu hoặc quản lý mới được hủy.'))
            super(RentalExtension, extension).write({
                'state': 'cancelled',
                'reviewed_by': self.env.user.id,
                'reviewed_at': fields.Datetime.now(),
            })
        return True

    def _sync_operation_schedule(self):
        self.ensure_one()
        if 'rental.operation.ticket.vehicle' not in self.env.registry:
            return
        ticket_model = self.env['rental.operation.ticket']
        if 'contract_id' not in ticket_model._fields:
            return
        tickets = ticket_model.sudo().search(
            [('contract_id', '=', self.contract_id.id)]
        )
        vehicle_model = self.env['rental.operation.ticket.vehicle'].sudo()
        if not tickets or 'date_checkin' not in vehicle_model._fields:
            return
        vehicle_lines = vehicle_model.search([
            ('ticket_id', 'in', tickets.ids),
            ('status', '=', 'renting'),  # Chỉ đổi lịch xe thực sự còn ở khách.
            ('vehicle_id', 'in', self.line_ids.vehicle_id.ids),  # Không đổi lịch thu hồi các xe không gia hạn.
        ])
        local_end = fields.Datetime.context_timestamp(self, self.requested_end_date)  # Cùng cách đổi múi giờ hiện có của Operation.
        if 'rental.return.receipt' in self.env.registry:  # Nếu đã có biên lai dự kiến thì phải tách xe gia hạn khỏi nhóm trả cũ.
            receipts = self.env['rental.return.receipt'].sudo().search([('ticket_id', 'in', tickets.ids), ('state', '!=', 'returned'), ('vehicle_ids', 'in', vehicle_lines.ids)])  # Chỉ chỉnh biên lai chưa thu hồi.
            for receipt in receipts:  # Một biên lai có thể đang gộp A, B, C cùng ngày cũ.
                selected = receipt.vehicle_ids & vehicle_lines  # Các xe thực sự được gia hạn trong biên lai.
                schedule = {'return_date': local_end.date(), 'return_time': local_end.strftime('%H:%M')}  # Ngày giờ mới dùng cho nhóm gia hạn.
                if selected == receipt.vehicle_ids:  # Cả biên lai cùng gia hạn thì chỉ đổi lịch.
                    receipt.write(schedule)  # Không tạo thêm biên lai không cần thiết.
                else:  # Gia hạn riêng B thì A/C phải ở lại biên lai cũ.
                    remaining = receipt.vehicle_ids - selected  # Nhóm A/C vẫn trả theo ngày cũ.
                    quantities = ('qty_helmet', 'qty_raincoat', 'qty_phone_holder', 'qty_charger')  # Bốn loại phụ kiện Operation đang theo dõi trên từng xe.
                    old_quantities = {name: sum(remaining.mapped(name)) for name in quantities}  # Dự kiến thu hồi phụ kiện của A/C, không còn phần B.
                    new_quantities = {name: sum(selected.mapped(name)) for name in quantities}  # Biên lai B chỉ dự kiến thu phụ kiện đã giao cùng B.
                    receipt.write({'vehicle_ids': [Command.unlink(vehicle.id) for vehicle in selected], **old_quantities})  # Bỏ B khỏi nhóm cũ, không xóa dữ liệu xe.
                    new_receipt = receipt.copy({**schedule, **new_quantities, 'vehicle_ids': [Command.set(selected.ids)], 'is_selected': False})  # Tạo biên lai dự kiến riêng, không sao chép nhầm tổng phụ kiện cả nhóm.
                    if 'return_receipt_id' in vehicle_lines._fields:  # Operation dùng liên kết này để mở lại đúng biên lai của xe.
                        selected.write({'return_receipt_id': new_receipt.id})  # Trỏ B sang biên lai mới.


        vehicle_lines.write({'date_checkin': self.requested_end_date, 'return_date': local_end.date(), 'return_time': local_end.strftime('%H:%M')})  # Cập nhật đủ cả mốc đầy đủ và ngày/giờ hiển thị.

    def unlink(self):
        raise UserError(_('Không được xóa yêu cầu gia hạn để bảo toàn lịch sử.'))
