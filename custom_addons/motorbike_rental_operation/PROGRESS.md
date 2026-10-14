# Tiến độ module `motorbike_rental_operation` (Giang)

> Cập nhật lần cuối: 2026-10-14
> Quy tắc: chỉ sửa trong thư mục module này, KHÔNG sửa module của người khác.
> Không làm ODO, không làm Pin.

## Đã hoàn thành

- [x] `__manifest__.py`: depends `['base', 'fleet', 'motorbike_rental_core']`, đã bỏ `data/fleet.vehicle.csv`.
- [x] Đã xoá model mock `fleet.vehicle` và quyền `access_fleet_vehicle_mock`.
- [x] Các trường tiền chuyển sang `fields.Monetary` (+ `currency_id`).
- [x] `rental.operation.ticket.vehicle.vehicle_id` = `Many2one('fleet.vehicle')`.
- [x] **Case 1 – Phiếu vận hành** (`models/rental_operation_ticket.py`):
  - `contract_id` có `required=True`.
  - `rental_order_ref` = `related='contract_id.name', store=True, readonly=True`
    (đã bỏ dòng gán tay trong `_onchange_contract_id`).
  - Thêm `actual_return_date = Datetime('Giờ trả thực tế')`.
  - Công thức `total_rent_amount`: đã cộng thêm phí giao xe `delivery_fee`.
  - Đổi tên trạng thái: `waiting` (Chưa thực hiện), `renting` (Đang cho thuê), `done` (Hoàn tất).
  - Bỏ nút/trường "Đã thanh toán tiền thuê" và "Đã thu CCCD gốc" khỏi form/list.
  - Thêm nút hành động:
    + "Xác nhận đã giao xe thành công" (`action_confirm_delivery`): có popup cảnh báo xác nhận chắc chắn, chuyển `state` sang `renting` (Đang cho thuê) và cập nhật dòng xe `status='renting'`.
    + "Xác nhận hoàn tất trả xe" (`action_confirm_return`): có popup cảnh báo xác nhận chắc chắn, chuyển `state` sang `done` (Hoàn tất), gán `actual_return_date = now()`, cập nhật dòng xe `status='returned'`.
    + Đã bỏ nút "Đặt lại chưa thực hiện".
  - Khóa toàn bộ các trường lấy từ Hợp đồng (`readonly=True`, chuyển sang `related='contract_id...'`): Khách hàng, Mã HĐ, Ngày giao, Ngày trả, Thời gian thuê, Tiền tệ, Tiền cọc, Tổng tiền, Số tiền còn lại; Trong bảng xe con: khóa Mã xe, Giá xe, Ngày giao/nhận và chặn tự ý thêm xe lẻ (`create="0"`).

## Sửa lỗi tương thích Odoo 18 (2026-10-14)

- [x] `motorbike_fleet_management/models/fleet_vehicle.py` (module của Bắc, sửa theo yêu cầu để cài được):
  - Lỗi khi cài: `AttributeError: module 'odoo.models' has no attribute 'Constraint'`.
  - Nguyên nhân: `models.Constraint(...)` chỉ có ở Odoo 19, trong khi image chạy `odoo:18.0`.
  - Sửa: `_vehicle_code_unique = models.Constraint('UNIQUE(vehicle_code)', ...)`
    → `_sql_constraints = [('vehicle_code_unique', 'UNIQUE(vehicle_code)', '...')]`.
  - ⚠️ Cần báo Bắc để đồng bộ (tránh bị ghi đè khi merge).

## Sửa quyền truy cập `rental.contract` (2026-10-14)

- [x] `motorbike_rental_core/security/rental_security.xml` (module của Nhân, sửa theo yêu cầu):
  - Lỗi: `Access Error` khi mở `rental.contract` vì user chưa thuộc nhóm Rental User/Manager.
  - Sửa: thêm vào record `group_rental_manager`:
    `<field name="users" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>`
    → admin tự động thuộc nhóm Rental Manager khi cài/nâng cấp module.
  - Cần chạy: `-u motorbike_rental_core`, sau đó đăng xuất và đăng nhập lại.
  - User khác vẫn phải gán nhóm thủ công trong Settings → Users.
  - ⚠️ Cần báo Nhân để đồng bộ (tránh bị ghi đè khi merge).

## Cần làm tiếp (theo thứ tự đề xuất)

### Case 2 – Giao xe / Trả xe (`models/rental_operation_ticket_vehicle.py`)
- [ ] `action_deliver_vehicle`: `status='renting'`, `vehicle_id.write({'operational_status': 'renting'})`.
- [ ] `action_return_vehicle`: `status='returned'`, `ticket_id.actual_return_date = fields.Datetime.now()`,
      ghi trạng thái xe bên Bắc.
- [ ] `views/ticket_views.xml`: hiển thị `actual_return_date`; thêm nút "Giao xe", "Trả xe" trên list dòng xe.
- ❓ **Cần chốt**: khi trả xe ghi `available` hay `pending_inspection`?
  (`available` sẽ báo ValidationError nếu xe điện có `technical_ready=False`.)

### Case 4 – Đổi tên field sang Many2one `fleet.vehicle`
- [ ] `rental.operation.incident.log`: `vehicle_ref` (Char) → `vehicle_id = Many2one('fleet.vehicle', 'Xe gặp sự cố', required=True)`.
- [ ] `rental.operation.vehicle.replacement`: `old_vehicle_ref`/`new_vehicle_ref` → `old_vehicle_id`/`new_vehicle_id` (Many2one `fleet.vehicle`).
- [ ] Cập nhật đồng bộ `views/incident_views.xml` (list, form, search, kanban) và `views/ticket_views.xml` (list sự cố dùng `vehicle_ref`).
- [ ] `action_confirm_replacement`: cập nhật `vehicle_id` trên `rental.contract.line` và dòng phiếu vận hành;
      xe cũ → `maintenance`, xe mới → `renting`.
      Lưu ý ràng buộc `UNIQUE(contract_id, vehicle_id)` bên core, và xe mới phải đang rảnh.
- [ ] Thêm nút "Xác nhận đổi xe" vào view.

### Case 3 – Tạo phụ phí sang Finance (CHƯA LÀM, cần bàn với Đức Anh)
- [ ] `is_charge_created` (Boolean), `charge_id` (Many2one `motorbike.rental.charge`), `action_create_charge`, nút "Tạo phụ phí bồi thường".
- ⚠️ Finance đã `depends` vào module này → KHÔNG được thêm finance vào `depends` (vòng lặp phụ thuộc).
- ⚠️ `motorbike.rental.charge` có field bắt buộc: `name`, `customer_id`, `price_catalog_id`, `quantity`, `unit_price`.
- Hướng tốt: để Finance kế thừa `rental.operation.incident.log` để thêm các field/nút này.

## Lưu ý khi nâng cấp module
- `contract_id required=True`: nếu DB có phiếu cũ không có hợp đồng sẽ lỗi `NOT NULL`
  → xoá dữ liệu test cũ hoặc bỏ tạm `required`.
- Sau khi sửa model/view, chạy lại với `-u motorbike_rental_operation` để kiểm tra lỗi.

## Tham chiếu module khác (chỉ đọc)
- `motorbike_fleet_management/models/fleet_vehicle.py`: `operational_status` (available/renting/pending_inspection/maintenance), `technical_ready`.
- `motorbike_rental_core/models/rental_contract.py`: `rental.contract`, `rental.contract.line` (`vehicle_id`, `daily_rate`).
- `motorbike_rental_finance/models/rental_charge.py`: `motorbike.rental.charge`.
