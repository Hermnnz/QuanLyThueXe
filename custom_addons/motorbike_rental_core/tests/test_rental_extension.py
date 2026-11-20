import uuid

from odoo import fields, Command  # Command dùng để chọn các dòng xe cần gia hạn.
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged, Form  # Form chạy cả default_get/onchange như lúc nhập trên giao diện.


@tagged('post_install', '-at_install')
class TestRentalExtension(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        suffix = uuid.uuid4().hex[:8]
        cls.customer = cls.env['res.partner'].create({
            'name': 'Extension customer %s' % suffix,
            'phone': '0901%s' % suffix[:6],
            'email': 'extension-%s@example.com' % suffix,
            'rental_id_number': 'ID-%s' % suffix,
            'is_rental_customer': True,
        })
        cls.customer.rental_document_ids.create({
            'name': 'Identity document',
            'customer_id': cls.customer.id,
            'file': 'dGVzdA==',
            'filename': 'identity.txt',
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Extension brand %s' % suffix,
        })
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'Extension bike %s' % suffix,
            'brand_id': brand.id,
            'vehicle_type': 'bike',
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'is_electric_motorbike': True,
            'odometer': 100,
            'technical_ready': True,
            'operational_status': 'available',
        })
        cls.vehicle_type = cls.env['rental.vehicle.type'].create({
            'name': 'Extension rate %s' % suffix,
            'model_id': model.id,
            'daily_rate': 100000,
        })
        cls.employee = cls.env['res.users'].create({
            'name': 'Extension employee %s' % suffix,
            'login': 'extension-employee-%s' % suffix,
            'groups_id': [(6, 0, [
                cls.env.ref('motorbike_rental_core.group_rental_user').id,
            ])],
        })
        cls.manager = cls.env['res.users'].create({
            'name': 'Extension manager %s' % suffix,
            'login': 'extension-manager-%s' % suffix,
            'groups_id': [(6, 0, [
                cls.env.ref('motorbike_rental_core.group_rental_manager').id,
            ])],
        })

    def _create_active_contract(
        self,
        start_date='2026-12-01 08:00:00',
        end_date='2026-12-03 08:00:00',
        vehicles=None,  # Cho phép thử hợp đồng nhiều xe; mặc định vẫn dùng một xe như các ca cũ.
    ):
        contract = self.env['rental.contract'].create({
            'customer_id': self.customer.id,
            'start_date': start_date,
            'end_date': end_date,
            'line_ids': [(0, 0, {
                'vehicle_id': vehicle.id,  # Mỗi dòng là một xe riêng trong nhóm thử.
                'vehicle_type_id': self.vehicle_type.id,
            }) for vehicle in (vehicles or self.vehicle)],
        })
        if (
            'motorbike.rental.payment' in self.env.registry
            and 'upfront_received_check' in contract._fields
        ):
            contract.write({
                'upfront_received_check': True,
                'upfront_payment_method': 'cash',
            })
        contract.action_confirm()
        contract.action_start()
        return contract

    def _create_extension(self, contract, requested_end_date):
        self._deliver(contract)  # Gia hạn chỉ dành cho xe thực sự đã bàn giao, không phải xe chờ giao.
        return self.env['rental.extension'].with_user(self.employee).create({
            'contract_id': contract.id,
            'requested_end_date': requested_end_date,
            'reason': 'Khách cần thêm thời gian thuê.',
        })

    def _deliver(self, contract):  # Bàn giao các xe còn chờ bằng các nút nghiệp vụ thật của Operation.
        if 'rental.operation.ticket.vehicle' in self.env.registry:  # Core có thể được chạy riêng khi không cài Operation.
            lines = self.env['rental.operation.ticket.vehicle'].search([('ticket_id.contract_id', '=', contract.id), ('status', '=', 'waiting')])  # Không giao lại xe đã giao.
            if lines:  # Dùng đúng luồng bắt đầu giao rồi xác nhận đã giao.
                lines.action_start_delivery()  # Fleet chuyển trạng thái xe sang đang thuê.
                lines.action_confirm_delivery()  # Operation xác nhận xe đã ở khách.

    def test_extension_form_defaults_show_current_and_next_return_time(self):
        contract = self._create_active_contract()
        self._deliver(contract)  # Form chỉ được chọn xe còn đang thuê.

        defaults = self.env['rental.extension'].with_context(
            default_contract_id=contract.id,
        ).default_get([
            'state',
            'contract_id',
            'original_end_date',
            'original_rental_days',
            'requested_end_date',
            'line_ids',  # Phép tính tiền giờ dựa trên những xe thực sự được chọn.
        ])

        self.assertEqual(defaults['state'], 'pending')
        self.assertEqual(defaults['contract_id'], contract.id)
        self.assertEqual(defaults['original_end_date'], contract.end_date)
        self.assertEqual(defaults['original_rental_days'], contract.rental_days)
        self.assertEqual(
            defaults['requested_end_date'],
            fields.Datetime.add(contract.end_date, days=1),
        )
        extension_form = self.env['rental.extension'].new(defaults)
        self.assertEqual(extension_form.additional_days, 1)
        self.assertEqual(extension_form.additional_amount, 100000)

    def test_create_uses_contract_from_action_context(self):
        contract = self._create_active_contract()
        self._deliver(contract)  # Dữ liệu thử phải phù hợp điều kiện xe đã bàn giao.

        extension = self.env['rental.extension'].with_user(
            self.employee
        ).with_context(default_contract_id=contract.id).create({
            'requested_end_date': '2026-12-04 08:00:00',
            'reason': 'Khách cần thêm thời gian thuê.',
        })

        self.assertEqual(extension.contract_id, contract)
        self.assertEqual(extension.original_end_date, contract.end_date)

    def test_rental_user_can_check_and_extend_contract(self):
        contract = self._create_active_contract()
        extension = self._create_extension(
            contract, '2026-12-05 08:00:00'
        )

        self.assertEqual(extension.additional_days, 2)
        self.assertEqual(extension.additional_amount, 200000)

        extension.with_user(self.employee).action_check_and_extend()

        self.assertEqual(extension.state, 'approved')
        self.assertEqual(extension.reviewed_by, self.employee)
        self.assertEqual(contract.end_date, fields.Datetime.to_datetime(
            '2026-12-05 08:00:00'
        ))
        self.assertEqual(contract.rental_days, 4)
        self.assertEqual(contract.total_amount, 400000)

    def test_check_does_not_extend_when_next_booking_conflicts(self):
        contract = self._create_active_contract()
        self._create_active_contract(
            start_date='2026-12-03 08:00:00',
            end_date='2026-12-05 08:00:00'
        )
        extension = self._create_extension(
            contract, '2026-12-04 08:00:00'
        )

        with self.assertRaises(ValidationError), self.cr.savepoint():
            extension.with_user(self.employee).action_check_and_extend()

        self.assertEqual(extension.state, 'pending')
        self.assertEqual(contract.end_date, fields.Datetime.to_datetime(
            '2026-12-03 08:00:00'
        ))

    def test_rejection_requires_a_reason(self):
        contract = self._create_active_contract()
        extension = self._create_extension(
            contract, '2026-12-04 08:00:00'
        )

        with self.assertRaises(UserError), self.cr.savepoint():
            extension.with_user(self.manager).action_reject()

        extension.with_user(self.manager).write({
            'rejection_reason': 'Xe đã có lịch thuê tiếp theo.',
        })
        extension.with_user(self.manager).action_reject()

        self.assertEqual(extension.state, 'rejected')
        self.assertEqual(extension.reviewed_by, self.manager)

    def test_requester_can_cancel_pending_extension(self):
        contract = self._create_active_contract()
        extension = self._create_extension(
            contract, '2026-12-04 08:00:00'
        )

        extension.with_user(self.employee).action_cancel()

        self.assertEqual(extension.state, 'cancelled')

    def test_only_one_pending_extension_per_contract(self):
        contract = self._create_active_contract()
        self._create_extension(contract, '2026-12-04 08:00:00')

        with self.assertRaises(UserError), self.cr.savepoint():
            self._create_extension(contract, '2026-12-05 08:00:00')

    def _three_vehicle_contract(self):  # Tạo và bàn giao 3 xe cùng giá 100 nghìn/ngày trong 2 ngày.
        if 'rental.operation.ticket' not in self.env.registry:  # Ca tích hợp cần Operation; không ép Core phụ thuộc ngược vào Operation.
            self.skipTest('Ca tích hợp này cần cài module Operation.')  # Khi Core chạy riêng vẫn giữ các ca kiểm thử Core cũ.
        extra = self.env['fleet.vehicle'].create([{'model_id': self.vehicle.model_id.id, 'is_electric_motorbike': True, 'technical_ready': True, 'operational_status': 'available'} for _ in range(2)])  # Hai xe riêng, không dùng dữ liệu thật.
        contract = self._create_active_contract(vehicles=self.vehicle | extra)  # Hợp đồng ban đầu 600 nghìn và cọc 3 triệu.
        self._deliver(contract)  # Cả ba xe phải đang ở khách trước khi gia hạn.
        return contract  # Trả về hợp đồng để từng ca chọn A/B/C.

    def _extend_lines(self, contract, lines, deadline):  # Tạo và duyệt yêu cầu cho đúng các dòng xe được truyền vào.
        extension = self.env['rental.extension'].create({'contract_id': contract.id, 'select_all': False, 'line_ids': [Command.set(lines.ids)], 'requested_end_date': deadline, 'reason': 'Thử gia hạn riêng từng xe'})  # Không dùng Chọn tất cả.
        extension.action_check_and_extend()  # Dùng nút nghiệp vụ để cập nhật Core và Operation.
        return extension  # Giữ yêu cầu để đối chiếu tiền và lịch sử.

    def test_partial_extension_updates_only_selected_vehicle(self):  # Gia hạn B hai ngày, giữ lịch và tiền thuê A/C.
        contract = self._three_vehicle_contract()  # Ba xe đều trả ngày 3/12 ban đầu.
        a, b, c = contract.line_ids  # Đặt tên rõ cho ví dụ A/B/C.
        extension = self._extend_lines(contract, b, '2026-12-05 08:00:00')  # Chỉ B thêm hai ngày.
        self.assertEqual(a.return_deadline, fields.Datetime.to_datetime('2026-12-03 08:00:00'))  # A không gia hạn.
        self.assertEqual(c.return_deadline, a.return_deadline)  # C giữ hạn cũ như A.
        self.assertEqual(b.return_deadline, contract.end_date)  # B là xe trả muộn nhất nên quyết định ngày kết thúc chung.
        self.assertEqual(extension.additional_amount, 200000)  # Chỉ tính 2 ngày của B.
        self.assertEqual(contract.total_amount, 800000)  # A 200k + B 400k + C 200k.
        self.assertEqual(contract.deposit_amount, 3000000)  # Gia hạn không tăng tiền cọc.
        if 'motorbike.rental.payment' in self.env.registry:  # Tiền đã thu đầu vào phải giữ nguyên.
            rent = contract.payment_ids.filtered(lambda payment: payment.transaction_type == 'rental_payment')  # Đọc phiếu thu tiền thuê ban đầu.
            self.assertEqual(rent.amount, 600000)  # Phần gia hạn chỉ quyết toán sau, không tự báo đã thu thêm.
        operations = self.env['rental.operation.ticket.vehicle'].search([('ticket_id.contract_id', '=', contract.id)])  # Đối chiếu lịch Operation.
        self.assertEqual(operations.filtered(lambda line: line.vehicle_id == b.vehicle_id).date_checkin, b.return_deadline)  # B được cập nhật lịch thu hồi.
        self.assertEqual(operations.filtered(lambda line: line.vehicle_id == a.vehicle_id).date_checkin, a.return_deadline)  # A giữ lịch cũ.

    def test_select_all_extends_each_current_vehicle(self):  # Chọn tất cả vẫn hỗ trợ luồng gia hạn cả hợp đồng như trước.
        contract = self._three_vehicle_contract()  # Ba xe đang thuê.
        extension = self.env['rental.extension'].create({'contract_id': contract.id, 'select_all': True, 'requested_end_date': '2026-12-04 08:00:00', 'reason': 'Gia hạn tất cả'})  # Hệ thống tự lấy đủ ba xe hợp lệ.
        self.assertEqual(extension.line_ids, contract.line_ids)  # Không sót xe nào trong nhóm đang thuê.
        self.assertEqual(extension.additional_amount, 300000)  # Mỗi xe thêm một ngày, tổng 300k.
        extension.action_check_and_extend()  # Duyệt yêu cầu chung.
        self.assertTrue(all(line.return_deadline == contract.end_date for line in contract.line_ids))  # Cả ba cùng ngày trả mới.
        self.assertEqual(contract.total_amount, 900000)  # Ba xe, mỗi xe 3 ngày.

    def test_different_deadlines_preserve_previous_extension_amount(self):  # Gia hạn A sau B nhưng chưa vượt ngày B không được kéo dài các xe khác.
        contract = self._three_vehicle_contract()  # A/B/C cùng hạn ban đầu.
        a, b, c = contract.line_ids  # Tách từng dòng xe.
        first = self._extend_lines(contract, b, '2026-12-05 08:00:00')  # B thêm hai ngày.
        second = self._extend_lines(contract, a, '2026-12-04 08:00:00')  # A chỉ thêm một ngày.
        self.assertEqual(contract.end_date, b.return_deadline)  # Hạn chung vẫn là ngày 5 của B.
        self.assertEqual(second.additional_amount, 100000)  # A chỉ phát sinh 100k.
        self.assertEqual(first.additional_amount, 200000)  # Lịch sử lần B giữ đúng số tiền đã duyệt.
        self.assertEqual(contract.total_amount, 900000)  # A 300k + B 400k + C 200k.
        self.assertLess(c.return_deadline, a.return_deadline)  # C vẫn chưa bị gia hạn.

    def test_return_receipts_split_and_invoice_waits_for_last_vehicle(self):  # Thu A/C trước không được thu hồi nhầm B hoặc cho xuất hóa đơn sớm.
        contract = self._three_vehicle_contract()  # Cả ba xe đã giao.
        ticket = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)], limit=1)  # Phiếu vận hành duy nhất của hợp đồng.
        operations = ticket.vehicle_detail_ids  # Ba dòng xe đang thuê.
        old = self.env['rental.return.receipt'].create({'ticket_id': ticket.id, 'customer_id': contract.customer_id.id, 'vehicle_ids': [Command.set(operations.ids)], 'return_date': '2026-12-03', 'return_time': '15:00'})  # Biên lai ban đầu chứa cả ba xe.
        operations.write({'return_receipt_id': old.id})  # Gắn liên kết như khi lập biên lai từ Operation.
        b = contract.line_ids[1]  # Chỉ gia hạn B.
        self._extend_lines(contract, b, '2026-12-05 08:00:00')  # B phải tách sang biên lai ngày 5.
        self.assertEqual(len(old.vehicle_ids), 2)  # Biên lai cũ chỉ còn A/C.
        self.assertNotIn(b.vehicle_id, old.vehicle_ids.vehicle_id)  # Không thu hồi B theo biên lai cũ.
        remaining = ticket.return_receipt_ids - old  # Biên lai mới dành cho B.
        self.assertEqual(remaining.vehicle_ids.vehicle_id, b.vehicle_id)  # Biên lai mới chỉ chứa B.
        self.assertEqual(remaining.qty_helmet, sum(remaining.vehicle_ids.mapped('qty_helmet')))  # Không sao chép mũ của A/C sang biên lai B.
        self.assertEqual(old.qty_charger, sum(old.vehicle_ids.mapped('qty_charger')))  # Nhóm A/C chỉ nhận lại các bộ sạc của chính nhóm đó.
        old.action_confirm_return()  # Thu hồi A/C bình thường.
        self.assertEqual(contract.state, 'in_progress')  # B còn thuê nên hợp đồng chưa kết thúc.
        if 'account.move' in self.env.registry and 'contract_id' in self.env['account.move']._fields:  # Finance vẫn chặn hóa đơn trước khi thu hồi đủ.
            with self.assertRaises(UserError), self.cr.savepoint():  # Không để ca thử lưu hóa đơn sai quy tắc.
                self.env['account.move'].create({'move_type': 'out_invoice', 'partner_id': contract.customer_id.id, 'contract_id': contract.id})  # B vẫn ở khách.
        remaining.action_confirm_return()  # Thu hồi B khi kết thúc lượt gia hạn.
        self.assertEqual(contract.state, 'in_progress')  # Chờ quyết toán hóa đơn; thu hồi không tự đóng hợp đồng.
        if 'account.move' in self.env.registry and 'contract_id' in self.env['account.move']._fields:  # Kiểm tra hóa đơn lấy đúng tiền thuê sau gia hạn.
            invoice = self.env['account.move'].new({'move_type': 'out_invoice', 'contract_id': contract.id})  # Dữ liệu nháp như trên form hóa đơn.
            invoice._onchange_contract_id()  # Dùng cùng hàm điền dòng tiền thuê của giao diện Finance.
            self.assertEqual(sum(invoice.invoice_line_ids.mapped('price_unit')), 800000)  # Không biến thành 1,2 triệu do kéo dài cả ba xe.

    def test_unselected_vehicle_is_free_after_own_deadline(self):  # Gia hạn B tới ngày 5 không được giữ lịch A tới ngày 5.
        contract = self._three_vehicle_contract()  # Hạn ban đầu ngày 3.
        a, b, c = contract.line_ids  # Ba xe riêng.
        self._extend_lines(contract, b, '2026-12-05 08:00:00')  # B mới là xe được gia hạn.
        next_contract = self.env['rental.contract'].create({'customer_id': self.customer.id, 'start_date': '2026-12-03 08:00:00', 'end_date': '2026-12-04 08:00:00', 'line_ids': [Command.create({'vehicle_id': a.vehicle_id.id, 'vehicle_type_id': self.vehicle_type.id})]})  # Lịch tiếp theo của A bắt đầu đúng hạn trả A.
        next_contract._check_vehicle_availability()  # Không được chặn vì ngày kết thúc chung của hợp đồng trước là ngày 5.
        with self.assertRaises(ValidationError), self.cr.savepoint():  # Nhưng thuê lại B trong khoảng gia hạn phải bị chặn.
            next_contract.line_ids.write({'vehicle_id': b.vehicle_id.id})  # Kiểm tra cùng khoảng thuê với B.
            next_contract._check_vehicle_availability()  # Bản nháp được sửa xe; chốt lịch được kiểm tra khi xác nhận.

    def test_returned_vehicle_cannot_be_extended(self):  # Xe đã trả không còn trong Chọn tất cả và không được chọn thủ công.
        contract = self._three_vehicle_contract()  # Ba xe đang thuê.
        a = contract.line_ids[0]  # Thu A trước.
        operation = self.env['rental.operation.ticket.vehicle'].search([('ticket_id.contract_id', '=', contract.id), ('vehicle_id', '=', a.vehicle_id.id)])  # Dòng vận hành của A.
        operation.action_confirm_return()  # Dùng thao tác thu hồi thật.
        with self.assertRaises(UserError), self.cr.savepoint():  # Chặn cả khi dữ liệu cũ trên form vẫn gửi A.
            self._extend_lines(contract, a, '2026-12-04 08:00:00')  # Không cho gia hạn xe không còn ở khách.
        extension = self.env['rental.extension'].create({'contract_id': contract.id, 'select_all': True, 'requested_end_date': '2026-12-04 08:00:00', 'reason': 'Chỉ các xe còn thuê'})  # Chọn tất cả phải bỏ A.
        self.assertNotIn(a, extension.line_ids)  # Chỉ còn B/C.

    def test_form_can_save_individual_vehicle_selection(self):  # Kiểm tra form lưu đúng nhóm xe sau khi widget chuyển sang chọn riêng.
        contract = self._three_vehicle_contract()  # Ba xe đã bàn giao.
        b = contract.line_ids[1]  # Xe muốn giữ lại lâu hơn.
        model = self.env['rental.extension'].with_context(default_contract_id=contract.id, default_select_all=False)  # Mô phỏng cờ nội bộ mà widget đặt khi chọn riêng xe.
        with Form(model, view='motorbike_rental_core.view_rental_extension_form') as form:  # Chạy các onchange thật của form.
            self.assertEqual(len(form.line_ids), 3)  # Danh sách xe ban đầu vẫn có đủ ba xe hợp lệ.
            form.line_ids.clear()  # Bỏ nhóm mặc định.
            form.line_ids.add(b)  # Chỉ chọn xe B.
            form.requested_end_date = '2026-12-05 08:00:00'  # B gia hạn hai ngày.
            form.reason = 'Khách giữ riêng xe B'  # Nhập lý do bắt buộc.
            self.assertEqual(form.additional_amount, 200000)  # Tiền trên form chỉ tính B.
        extension = form.record  # Form đã lưu yêu cầu, chưa duyệt.
        self.assertEqual(extension.line_ids, b)  # Phạm vi chọn trên form được giữ khi lưu.
        extension.action_check_and_extend()  # Duyệt bằng nút nghiệp vụ.
        self.assertEqual(contract.total_amount, 800000)  # Sau duyệt tiền thuê cả hợp đồng đúng 800k.

    def _swap_vehicle(self, contract, original):  # Đổi một xe đang thuê bằng luồng thật của Operation.
        if 'rental.vehicle.exchange' not in self.env.registry:  # Chỉ thử đổi xe khi chức năng đó được cài.
            self.skipTest('Ca tích hợp này cần chức năng đổi xe của Operation.')  # Không tạo phụ thuộc mới cho module Core.
        replacement = self.env['fleet.vehicle'].create({'model_id': original.vehicle_id.model_id.id, 'is_electric_motorbike': True, 'technical_ready': True, 'operational_status': 'available'})  # Xe thay thế cùng loại, cùng bảng giá.
        ticket = self.env['rental.operation.ticket'].search([('contract_id', '=', contract.id)], limit=1)  # Dùng lại phiếu vận hành gốc.
        exchange = self.env['rental.vehicle.exchange'].create({'ticket_id': ticket.id, 'vehicle_a_id': original.vehicle_id.id, 'vehicle_b_id': replacement.id, 'reason': 'Thử đổi xe trước gia hạn', 'error_by': 'company'})  # Giữ B và tạo dòng vận hành chờ giao.
        old_operation = ticket.vehicle_detail_ids.filtered(lambda item: item.vehicle_id == original.vehicle_id)  # Dòng vận hành của xe A.
        old_operation.action_confirm_return()  # Thu hồi A trước khi được bàn giao B.
        exchange.ticket_line_b_id.action_start_delivery()  # Bắt đầu giao xe thay thế.
        exchange.ticket_line_b_id.action_confirm_delivery()  # Giao B thành công thì Operation ghi B vào hợp đồng.
        self.assertEqual(exchange.status, 'done')  # Lượt đổi phải kết thúc trước khi yêu cầu gia hạn B.
        return exchange.contract_line_b_id  # Trả dòng hợp đồng của xe thay thế.

    def test_replacement_chain_extension_is_billed_once(self):  # A→B→C vẫn chỉ có một khoản thuê và một khoản cọc.
        contract = self._create_active_contract()  # A thuê hai ngày giá 100k/ngày.
        self._deliver(contract)  # Xe A đã ở khách.
        a = contract.line_ids  # Dòng thuê gốc dùng để ghi doanh thu.
        b = self._swap_vehicle(contract, a)  # Thu A, giao B.
        self.assertEqual(b.billing_line_id, a)  # B quy về khoản thuê của A.
        first = self._extend_lines(contract, b, '2026-12-05 08:00:00')  # B gia hạn thêm hai ngày.
        self.assertEqual(first.additional_amount, 200000)  # Chỉ phát sinh hai ngày của một xe.
        self.assertEqual(contract.total_amount, 400000)  # Không thu đồng thời cả A lẫn B.
        c = self._swap_vehicle(contract, b)  # Sau đó B có vấn đề thì đổi tiếp sang C.
        self.assertEqual(c.return_deadline, b.return_deadline)  # C kế thừa hạn đã gia hạn của B.
        self.assertEqual(c.billing_line_id, a)  # C vẫn quy về A, không tạo thêm khoản thuê gốc.
        second = self._extend_lines(contract, c, '2026-12-06 08:00:00')  # C chỉ thêm một ngày nữa.
        self.assertEqual(second.additional_amount, 100000)  # Không thu lại hai ngày gia hạn trước.
        self.assertEqual(contract.total_amount, 500000)  # Tổng năm ngày cho đúng một xe thuê.
        self.assertEqual(contract.deposit_amount, 1000000)  # Đổi xe và gia hạn đều không tăng cọc.
        self.assertEqual(first.additional_amount, 200000)  # Lịch sử yêu cầu trước vẫn giữ nguyên.

    def test_select_all_after_partial_extension_calculates_each_balance(self):  # Chọn tất cả khi B đã gia hạn phải trừ đúng phần ngày đã tính của B.
        contract = self._three_vehicle_contract()  # A/B/C ban đầu cùng trả ngày 3.
        self._extend_lines(contract, contract.line_ids[1], '2026-12-05 08:00:00')  # B đã trả tiền thuê đến ngày 5.
        extension = self.env['rental.extension'].create({'contract_id': contract.id, 'select_all': True, 'requested_end_date': '2026-12-06 08:00:00', 'reason': 'Cả nhóm cùng kéo dài tới ngày 6'})  # A/C thêm ba ngày, B chỉ thêm một ngày.
        self.assertEqual(extension.additional_amount, 700000)  # 300k + 100k + 300k; không phải 900k.
        extension.action_check_and_extend()  # Duyệt nhóm xe có các hạn cũ khác nhau.
        self.assertEqual(contract.total_amount, 1500000)  # Ba xe, mỗi xe tổng năm ngày.
