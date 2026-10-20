from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestInvoiceReturn(AccountTestInvoicingCommon):
    """Kiểm thử ràng buộc thu hồi bằng model Odoo và dữ liệu kế toán thử."""

    @classmethod
    def setUpClass(cls):  # Chuẩn bị khách, xe và bảng giá; lớp cha cung cấp tài khoản và sổ nhật ký thử.
        super().setUpClass()

        # AccountTestInvoicingCommon chuẩn bị tài khoản có quyền kế toán,
        # nhưng tài khoản đó chưa mặc nhiên có quyền Rental/Finance của nhóm.
        # Cần cấp thêm quyền nghiệp vụ để bộ test có thể tạo bảng giá, hợp
        # đồng, phiếu thu và phụ phí trước khi kiểm tra ràng buộc hóa đơn.
        #
        # sudo() chỉ dùng ở bước cấp nhóm cho tài khoản KIỂM THỬ trong
        # database test. Các thao tác nghiệp vụ bên dưới vẫn chạy bằng
        # cls.env của tài khoản đó để chịu ACL như người dùng bình thường.
        # Thay đổi này không sửa quyền người dùng của database đang sử dụng.
        cls.env.user.sudo().write({
            'groups_id': [
                # Rental Manager cho phép tạo bảng giá và hợp đồng thuê;
                # nhóm này cũng kế thừa Rental User và Fleet Officer.
                Command.link(cls.env.ref('motorbike_rental_core.group_rental_manager').id),
                # Finance User cho phép tạo/xác nhận phiếu thu và phụ phí,
                # phục vụ dữ liệu đầu vào của các tình huống lập hóa đơn.
                Command.link(cls.env.ref('motorbike_rental_finance.group_motorbike_finance_user').id),
            ],
        })

        cls.customer = cls.partner_a
        # Đường lập hóa đơn từ Charge không truyền account_id; cấu hình
        # tài khoản mặc định trên nhật ký thử để Odoo tự điền hợp lệ.
        cls.company_data['default_journal_sale'].default_account_id = (
            cls.company_data['default_account_revenue']
        )
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Invoice return brand'})
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'Invoice return bike', 'brand_id': brand.id, 'vehicle_type': 'bike',
        })
        cls.vehicles = cls.env['fleet.vehicle'].create([
            {'model_id': model.id, 'is_electric_motorbike': True,
             'operational_status': 'available', 'technical_ready': True},
            {'model_id': model.id, 'is_electric_motorbike': True,
             'operational_status': 'available', 'technical_ready': True},
        ])
        cls.price = cls.env['rental.vehicle.type'].create({
            'name': 'Invoice return price', 'model_id': model.id, 'daily_rate': 300000,
        })

    def contract(self, vehicles=None, **overrides):  # Tạo hợp đồng đã thu đủ tiền thuê và đã ký để tập trung kiểm thử bước thu hồi.
        vehicles = self.vehicles[:1] if vehicles is None else vehicles
        contract = self.env['rental.contract'].create({
            'customer_id': self.customer.id,
            'start_date': '2026-12-01 03:00:00',
            'end_date': '2026-12-03 03:00:00',
            'deposit_amount': 0,
            'line_ids': [Command.create({
                'vehicle_id': vehicle.id, 'vehicle_type_id': self.price.id,
            }) for vehicle in vehicles],
            **overrides,
        })
        self.env['motorbike.rental.payment'].create({
            'customer_id': contract.customer_id.id, 'contract_id': contract.id,
            'currency_id': contract.currency_id.id, 'transaction_type': 'rental_payment',
            'amount': contract.total_amount, 'payment_method': 'cash', 'state': 'confirmed',
        })
        contract.action_confirm()
        contract.action_start()
        return contract

    def ticket(self, contract, vehicles=None):  # Tạo phiếu vận hành, cho phép chỉ định danh sách xe để thử trường hợp thiếu xe.
        values = {'contract_id': contract.id}
        if vehicles is not None:
            values['vehicle_detail_ids'] = [Command.create({
                'vehicle_id': vehicle.id,
            }) for vehicle in vehicles] or [Command.clear()]
        return self.env['rental.operation.ticket'].create(values)

    def invoice_values(self, contract=None, charge=None):  # Chuẩn bị hóa đơn nháp với tài khoản doanh thu hợp lệ và các liên kết cần thử.
        return {
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'journal_id': self.company_data['default_journal_sale'].id,
            'invoice_date': fields.Date.today(),
            'contract_id': contract.id if contract else False,
            'invoice_line_ids': [Command.create({
                'name': 'Rental service', 'quantity': 1,
                'price_unit': charge.amount if charge else 600000,
                'account_id': self.company_data['default_account_revenue'].id,
                'charge_id': charge.id if charge else False,
                'tax_ids': [Command.clear()],
            })],
        }

    def charge(self, contract):  # Tạo phụ phí đã duyệt để kiểm thử đường lập hóa đơn không gắn contract_id trực tiếp.
        return self.env['motorbike.rental.charge'].create({
            'name': 'Return test surcharge', 'customer_id': contract.customer_id.id,
            'contract_id': contract.id, 'currency_id': contract.currency_id.id,
            'quantity': 1, 'unit_price': 150000, 'state': 'confirmed',
        })

    def assert_invoice_blocked(self, values):  # Kiểm tra lỗi thu hồi và rollback cả thao tác tạo hóa đơn bị từ chối.
        with self.assertRaisesRegex(UserError, 'thu hồi đầy đủ'), self.cr.savepoint():
            self.env['account.move'].create(values)

    def test_no_ticket_or_empty_ticket_blocks_invoice(self):  # Chặn hóa đơn khi chưa có phiếu hoặc phiếu không có dòng xe.
        contract = self.contract()
        self.assert_invoice_blocked(self.invoice_values(contract))
        self.ticket(contract, vehicles=self.env['fleet.vehicle'])
        self.assert_invoice_blocked(self.invoice_values(contract))

    def test_waiting_delivering_and_renting_block_invoice(self):  # Chặn hóa đơn ở cả ba bước trước khi xác nhận thu hồi.
        contract = self.contract()
        lines = self.ticket(contract).vehicle_detail_ids
        self.assert_invoice_blocked(self.invoice_values(contract))
        lines.action_start_delivery()
        self.assert_invoice_blocked(self.invoice_values(contract))
        lines.action_confirm_delivery()
        self.assert_invoice_blocked(self.invoice_values(contract))

    def test_partial_return_blocks_then_full_return_allows_invoice(self):  # Hai xe phải được thu hồi đủ; chờ Fleet kiểm tra kỹ thuật không cản lập hóa đơn.
        contract = self.contract(vehicles=self.vehicles)
        lines = self.ticket(contract).vehicle_detail_ids
        lines.action_confirm_delivery()
        lines[:1].action_confirm_return()
        self.assert_invoice_blocked(self.invoice_values(contract))
        lines[1:].action_confirm_return()
        self.assertEqual(set(self.vehicles.mapped('operational_status')), {'pending_inspection'})
        invoice = self.env['account.move'].create(self.invoice_values(contract))
        self.assertEqual(invoice.state, 'draft')
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_done_ticket_missing_contract_vehicle_still_blocks_invoice(self):  # Phiếu đã xong nhưng thiếu một xe của hợp đồng vẫn không đủ điều kiện.
        contract = self.contract(vehicles=self.vehicles)
        ticket = self.ticket(contract, vehicles=self.vehicles[:1])
        ticket.vehicle_detail_ids.action_confirm_delivery()
        ticket.vehicle_detail_ids.action_confirm_return()
        self.assertEqual(ticket.state, 'done')
        self.assert_invoice_blocked(self.invoice_values(contract))

    def test_all_tickets_are_checked(self):  # Không cho lấy phiếu đã hoàn tất để bỏ qua phiếu khác của cùng hợp đồng còn chờ giao.
        contract = self.contract()
        finished = self.ticket(contract)
        self.ticket(contract)
        finished.vehicle_detail_ids.action_confirm_delivery()
        finished.vehicle_detail_ids.action_confirm_return()
        self.assert_invoice_blocked(self.invoice_values(contract))

    def test_charge_invoice_without_direct_contract_is_checked(self):  # Charge trên dòng hóa đơn vẫn truy ra hợp đồng khi contract_id của hóa đơn trống.
        contract = self.contract()
        self.assert_invoice_blocked(self.invoice_values(charge=self.charge(contract)))

    def test_each_contract_on_grouped_charge_invoice_is_checked(self):  # Gộp phí nhiều hợp đồng phải chờ tất cả hợp đồng thu hồi, không chỉ hợp đồng đầu tiên.
        returned_contract = self.contract()
        pending_contract = self.contract(
            start_date='2026-12-04 03:00:00', end_date='2026-12-06 03:00:00',
        )
        lines = self.ticket(returned_contract).vehicle_detail_ids
        lines.action_confirm_delivery()
        lines.action_confirm_return()
        returned_charge = self.charge(returned_contract)
        pending_charge = self.charge(pending_contract)
        values = self.invoice_values(charge=returned_charge)
        values['invoice_line_ids'].append(Command.create({
            'name': 'Pending contract surcharge', 'quantity': 1,
            'price_unit': pending_charge.amount, 'charge_id': pending_charge.id,
            'account_id': self.company_data['default_account_revenue'].id,
            'tax_ids': [Command.clear()],
        }))
        self.assert_invoice_blocked(values)

    def test_charge_button_obeys_return_rule(self):  # Nút lập hóa đơn từ Charge phải bị chặn trước thu hồi và hoạt động sau thu hồi.
        contract = self.contract()
        charge = self.charge(contract)
        with self.assertRaisesRegex(UserError, 'thu hồi đầy đủ'), self.cr.savepoint():
            charge.action_create_invoice()
        self.assertFalse(charge.invoice_id)
        lines = self.ticket(contract).vehicle_detail_ids
        lines.action_confirm_delivery()
        lines.action_confirm_return()
        action = charge.action_create_invoice()
        self.assertEqual(action['res_id'], charge.invoice_id.id)
        self.assertFalse(charge.invoice_id.contract_id)

    def test_reverse_charge_link_is_checked(self):  # Liên kết Charge qua trường phụ phí của hóa đơn cũng phải chịu kiểm tra thu hồi.
        contract = self.contract()
        values = self.invoice_values()
        values['rental_charges_ids'] = [Command.set(self.charge(contract).ids)]
        self.assert_invoice_blocked(values)

    def test_attaching_contract_to_existing_invoice_is_checked(self):  # Không cho tạo hóa đơn thường rồi gắn hợp đồng chưa trả xe để vượt ràng buộc.
        contract = self.contract()
        invoice = self.env['account.move'].create(self.invoice_values())
        with self.assertRaisesRegex(UserError, 'thu hồi đầy đủ'), self.cr.savepoint():
            invoice.write({'contract_id': contract.id})
        self.assertFalse(invoice.contract_id)

    def test_attaching_charge_directly_to_line_is_checked(self):  # Sửa dòng hóa đơn trực tiếp vẫn chạy kiểm tra trên hóa đơn cha.
        contract = self.contract()
        invoice = self.env['account.move'].create(self.invoice_values())
        charge = self.charge(contract)
        line = invoice.invoice_line_ids
        with self.assertRaisesRegex(UserError, 'thu hồi đầy đủ'), self.cr.savepoint():
            line.write({'charge_id': charge.id})
        self.assertFalse(line.charge_id)

    def test_post_rechecks_legacy_draft_invoice(self):  # Hóa đơn nháp tồn tại trước ràng buộc mới vẫn phải được kiểm tra lại lúc xác nhận.
        contract = self.contract()
        invoice = self.env['account.move'].create(self.invoice_values())
        # SQL chỉ dùng trong dữ liệu thử để mô phỏng hóa đơn cũ đã có liên
        # kết trước khi cài ràng buộc; không phải hướng dẫn sửa dữ liệu thật.
        self.env.cr.execute(
            'UPDATE account_move SET contract_id=%s WHERE id=%s', (contract.id, invoice.id),
        )
        invoice.invalidate_recordset(['contract_id'])
        with self.assertRaisesRegex(UserError, 'thu hồi đầy đủ'), self.cr.savepoint():
            invoice.action_post()
        self.assertEqual(invoice.state, 'draft')

    def test_unrelated_invoice_is_unaffected(self):  # Hóa đơn khách hàng không liên quan nghiệp vụ thuê xe vẫn lập và xác nhận bình thường.
        invoice = self.env['account.move'].create(self.invoice_values())
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')
