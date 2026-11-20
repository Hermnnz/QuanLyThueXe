from odoo import Command  # Command mô tả thao tác thêm/xóa dòng xe.
from odoo.tests import TransactionCase, tagged  # Công cụ kiểm thử; dữ liệu thử được hoàn tác sau mỗi ca.


@tagged('post_install', '-at_install')  # Chạy sau khi cài đủ module.
class TestDepositPerVehicle(TransactionCase):  # Kiểm tra Core tính cọc và Finance đồng bộ phiếu.
    def setUp(self):  # Chuẩn bị khách, bảng giá và 4 xe riêng cho từng ca thử.
        super().setUp()  # Khởi tạo môi trường kiểm thử Odoo.
        self.customer = self.env['res.partner'].create({'name': 'Khách thử cọc theo xe'})  # Khách thử riêng.
        brand = self.env['fleet.vehicle.model.brand'].create({'name': 'Hãng thử cọc'})  # Hãng xe thử.
        model = self.env['fleet.vehicle.model'].create({'name': 'Xe thử cọc', 'brand_id': brand.id, 'vehicle_type': 'bike'})  # Dòng xe chung.
        self.price = self.env['rental.vehicle.type'].create({'name': 'Giá thử cọc', 'model_id': model.id, 'daily_rate': 300000})  # Tiền thuê độc lập với cọc.
        self.vehicles = self.env['fleet.vehicle'].create([{'model_id': model.id, 'is_electric_motorbike': True, 'technical_ready': True, 'operational_status': 'available'} for _ in range(4)])  # 3 xe gốc và 1 xe thay thế.

    def _line(self, vehicle, subfleet=False):  # Tạo lệnh thêm xe; subfleet=True nghĩa là xe thay thế.
        return Command.create({'vehicle_id': vehicle.id, 'vehicle_type_id': self.price.id, 'subfleet': subfleet})  # Không nhập cọc thủ công.

    def _contract(self, lines):  # Tạo hợp đồng nháp và để Finance tự tạo phiếu thu.
        return self.env['rental.contract'].create({'customer_id': self.customer.id, 'start_date': '2026-12-01 03:00:00', 'end_date': '2026-12-02 03:00:00', 'line_ids': lines})  # Cọc tính từ các dòng xe.

    def _assert_deposit(self, contract, amount):  # Đối chiếu cọc trên hợp đồng với đúng một phiếu cọc nháp.
        self.assertEqual(contract.deposit_amount, amount)  # Hợp đồng phải đúng số tiền.
        receipts = contract.payment_ids.filtered(lambda payment: payment.transaction_type == 'deposit' and payment.state == 'draft')  # Bỏ phiếu đã hủy.
        self.assertEqual(len(receipts), 1 if amount else 0)  # Không tạo trùng; không còn xe thì không còn phiếu cọc hoạt động.
        self.assertEqual(sum(receipts.mapped('amount')), amount)  # Phiếu phải khớp hợp đồng.

    def test_add_remove_vehicles_syncs_single_deposit(self):  # Kiểm tra 1 → 3 → 2 → 0 → 3 xe, không tạo trùng phiếu.
        contract = self._contract([self._line(self.vehicles[0])])  # Ban đầu một xe.
        self._assert_deposit(contract, 1000000)  # Một xe cọc một triệu.
        receipt = contract.payment_ids.filtered(lambda payment: payment.transaction_type == 'deposit')  # Giữ phiếu ban đầu.
        contract.write({'line_ids': [self._line(vehicle) for vehicle in self.vehicles[1:3]]})  # Thêm hai xe.
        self._assert_deposit(contract, 3000000)  # Ba xe cọc ba triệu.
        contract.write({'line_ids': [Command.delete(contract.line_ids[-1].id)]})  # Bỏ một xe.
        self._assert_deposit(contract, 2000000)  # Hai xe cọc hai triệu.
        contract.write({'line_ids': [Command.clear()]})  # Bỏ hết xe trong bản nháp.
        self._assert_deposit(contract, 0)  # Phiếu cọc chuyển sang hủy.
        contract.write({'line_ids': [self._line(vehicle) for vehicle in self.vehicles[:3]]})  # Thêm lại ba xe.
        self._assert_deposit(contract, 3000000)  # Phiếu cọc cũ được dùng lại.
        self.assertEqual(receipt.state, 'draft')  # Không tạo thêm phiếu mới.
        self.assertEqual(receipt.amount, 3000000)  # Cập nhật phiếu cũ thành ba triệu.

    def test_replacement_does_not_increase_deposit(self):  # Đảm bảo xe thay thế không phát sinh thêm cọc.
        contract = self._contract([self._line(vehicle) for vehicle in self.vehicles[:3]])  # Ba xe gốc.
        contract.write({'line_ids': [self._line(self.vehicles[3], subfleet=True)]})  # Thêm một xe thay thế.
        self._assert_deposit(contract, 3000000)  # Bốn dòng nhưng chỉ ba xe phải cọc.

    def test_new_form_recomputes_deposit(self):  # Kiểm tra cọc khi chọn xe trên bản ghi chưa lưu.
        contract = self.env['rental.contract'].new({'line_ids': [self._line(vehicle) for vehicle in self.vehicles[:3]]})  # Dữ liệu trong bộ nhớ như trên form.
        self.assertEqual(contract.deposit_amount, 3000000)  # Hiển thị ba triệu trước khi lưu.

    def test_closed_contract_keeps_historical_deposit(self):  # Giữ tiền cọc lịch sử khi tính lại trường trên hợp đồng đã hoàn tất.
        contract = self._contract([self._line(vehicle) for vehicle in self.vehicles[:3]])  # Hợp đồng ba xe.
        self.env.flush_all()  # Lưu các giá trị đang chờ tính trước khi chuẩn bị dữ liệu lịch sử.
        self.env.cr.execute('UPDATE rental_contract SET state = %s, deposit_amount = %s WHERE id = %s', ['done', 500000, contract.id])  # Chỉ giả lập hợp đồng cũ trong database thử.
        contract.invalidate_recordset(['state', 'deposit_amount'])  # Đọc lại dữ liệu đã chuẩn bị, bỏ bộ nhớ tạm.
        contract.modified(['line_ids'])  # Báo Odoo tính lại các trường phụ thuộc danh sách xe theo đúng cơ chế của hệ thống.
        self.assertEqual(contract.deposit_amount, 500000)  # Không đổi cọc lịch sử thành ba triệu.
