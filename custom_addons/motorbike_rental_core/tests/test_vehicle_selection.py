from odoo import Command  # Lệnh thêm dòng xe trên hợp đồng.
from odoo.tests import TransactionCase, tagged  # Kiểm thử trong transaction được hoàn tác, không lưu dữ liệu thử.


@tagged('post_install', '-at_install')  # Chạy khi các module liên quan đã sẵn sàng.
class TestVehicleSelection(TransactionCase):  # Kiểm tra danh sách xe mà giao diện được phép hiển thị.
    def setUp(self):  # Chuẩn bị xe sẵn sàng, xe khóa thuê và xe chưa đạt kỹ thuật.
        super().setUp()  # Khởi tạo môi trường thử.
        self.customer = self.env['res.partner'].create({'name': 'Khách thử lọc xe'})  # Khách riêng của ca thử.
        brand = self.env['fleet.vehicle.model.brand'].create({'name': 'Hãng thử lọc xe'})  # Hãng xe thử.
        model = self.env['fleet.vehicle.model'].create({'name': 'Dòng thử lọc xe', 'brand_id': brand.id, 'vehicle_type': 'bike'})  # Cùng dòng để kiểm tra lọc theo trạng thái.
        self.price = self.env['rental.vehicle.type'].create({'name': 'Giá thử lọc xe', 'model_id': model.id, 'daily_rate': 100000})  # Bảng giá tương ứng.
        self.ready = self.env['fleet.vehicle'].create([{'model_id': model.id, 'is_electric_motorbike': True, 'technical_ready': True, 'operational_status': 'available'} for _ in range(3)])  # Ba xe đủ điều kiện ban đầu.
        self.blocked = self.env['fleet.vehicle'].create({'model_id': model.id, 'is_electric_motorbike': True, 'technical_ready': True, 'operational_status': 'available', 'rental_blocked': True, 'block_reason': 'Xe thử bị khóa'})  # Sẵn sàng nhưng bị khóa vẫn phải ẩn.
        self.pending = self.env['fleet.vehicle'].create({'model_id': model.id, 'is_electric_motorbike': True, 'technical_ready': False, 'operational_status': 'pending_inspection'})  # Xe chưa kiểm tra kỹ thuật.
        self.renting = self.env['fleet.vehicle'].create({'model_id': model.id, 'is_electric_motorbike': True, 'technical_ready': True, 'operational_status': 'renting'})  # Xe đang được khách khác sử dụng.

    def _draft(self, **values):  # Tạo dữ liệu hợp đồng chưa lưu như khi nhân viên đang nhập trên form.
        return self.env['rental.contract'].new({'customer_id': self.customer.id, 'start_date': '2026-12-01 03:00:00', 'end_date': '2026-12-02 03:00:00', 'line_ids': [Command.create({'vehicle_type_id': self.price.id})], **values})  # Dòng mới chỉ chọn bảng giá, chưa chọn xe.

    def test_filters_current_fleet_status(self):  # Chỉ hiển thị xe sẵn sàng và đạt kỹ thuật, không bị khóa thuê.
        options = self._draft().line_ids.available_vehicle_ids._origin  # _origin chuyển bản ghi tạm trên form về xe thật để so sánh.
        self.assertEqual(options, self.ready)  # Xe khóa, chưa đạt kỹ thuật và đang thuê đều không xuất hiện.

    def test_filters_reservations_and_allows_boundary(self):  # Xe đã giữ lịch bị ẩn; hai chuyến nối tiếp đúng thời điểm vẫn được phép.
        booked = self.env['rental.contract'].create({'customer_id': self.customer.id, 'start_date': '2026-12-01 03:00:00', 'end_date': '2026-12-02 03:00:00', 'line_ids': [Command.create({'vehicle_type_id': self.price.id, 'vehicle_id': self.ready[0].id})]})  # Hợp đồng dùng để giả lập lịch đã giữ.
        self.env.flush_all()  # Lưu dữ liệu trước khi chuẩn bị trạng thái lịch bận.
        self.env.cr.execute('UPDATE rental_contract SET state = %s WHERE id = %s', ['confirmed', booked.id])  # Chỉ tạo tình huống lịch bận trong test, không kiểm thử lại thu tiền/ký hợp đồng.
        booked.invalidate_recordset(['state'])  # Bỏ trạng thái nháp trong bộ nhớ tạm.
        self.assertNotIn(self.ready[0], self._draft().line_ids.available_vehicle_ids._origin)  # Trùng khoảng thuê thì phải ẩn.
        self.assertIn(self.ready[0], self._draft(start_date='2026-12-02 03:00:00', end_date='2026-12-03 03:00:00').line_ids.available_vehicle_ids._origin)  # Trả đúng lúc chuyến sau bắt đầu thì không trùng.

    def test_excludes_other_selected_vehicles(self):  # Không gợi ý lại xe đã chọn ở dòng khác trong cùng bản nháp.
        contract = self._draft(line_ids=[Command.create({'vehicle_type_id': self.price.id, 'vehicle_id': self.ready[0].id}), Command.create({'vehicle_type_id': self.price.id})])  # Một dòng đã chọn xe và một dòng đang chọn.
        first, second = contract.line_ids  # Tách hai dòng để kiểm tra độc lập.
        self.assertIn(self.ready[0], first.available_vehicle_ids._origin)  # Giữ xe hiện tại của chính dòng đó trong danh sách.
        self.assertNotIn(self.ready[0], second.available_vehicle_ids._origin)  # Dòng thứ hai không được chọn trùng xe thứ nhất.

    def test_missing_dates_show_empty_options(self):  # Không phát lỗi khi người dùng chưa nhập đủ ngày thuê.
        self.assertFalse(self._draft(end_date=False).line_ids.available_vehicle_ids)  # Chưa có ngày trả thì chưa gợi ý xe.
