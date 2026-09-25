# Fleet & Maintenance — tuần 5 (Odoo 19)

Module mở rộng `fleet.vehicle` và `fleet.vehicle.log.services`; phụ thuộc `fleet`.

## Phạm vi
- Menu Fleet → Fleet → Xe máy điện và bộ lọc Xe máy điện.
- Tab Xe máy điện: đánh dấu xe, sê-ri pin, dung lượng kWh, điện áp V,
  sức khỏe pin %, thời gian sạc và hạn bảo hành.
- Tái sử dụng model xe, biển số, số khung, công suất, tầm hoạt động và
  quan hệ lịch sử bảo dưỡng có sẵn của Fleet, không tạo bản sao model.
- Bảo dưỡng: hạng mục, kỹ thuật viên (liên hệ), kết quả và ngày bảo dưỡng tiếp theo.
- Kiểm tra thông số không âm, phần trăm trong 0–100 và thứ tự ngày bảo dưỡng.
- Ngày bảo dưỡng tiếp theo chỉ là thông tin; chưa có thông báo tự động.

## Phân quyền
Giữ ACL và quy tắc đa công ty của Fleet. ACL Odoo cộng dồn theo nhóm:

| Nhóm | Xe | Hồ sơ bảo dưỡng |
| --- | --- | --- |
| Fleet Officer | Theo Fleet: đọc/tạo/sửa/xóa | Chỉ đọc |
| Kỹ thuật viên xe điện | Kế thừa Fleet Officer | Đọc/tạo/sửa, không cấp quyền xóa |
| Fleet Administrator | Toàn quyền | Toàn quyền |
| Người dùng nội bộ không có quyền Fleet | Không được truy cập | Không được truy cập |

Nhóm kỹ thuật viên cấp quyền trên model dịch vụ Fleet, áp dụng cả xe khác loại
trong công ty được phép. Nếu đồng thời có nhóm Fleet Administrator thì có quyền xóa.

## Cài đặt và kiểm thử
Thêm thư mục cha `custom_addons` của repository vào `addons_path` trong cấu hình
riêng ngoài repository. Dùng Python của Odoo và một database demo riêng:

```powershell
& C:\odoo\venv\Scripts\python.exe C:\odoo\odoo-bin -c <config-rieng> -d <database-demo> -i motorbike_fleet_management --without-demo=all --test-enable --test-tags /motorbike_fleet_management --stop-after-init
& C:\odoo\venv\Scripts\python.exe C:\odoo\odoo-bin -c <config-rieng> -d <database-demo> -u motorbike_fleet_management --test-enable --test-tags /motorbike_fleet_management --stop-after-init
```

Bỏ `-i`, `-u`, `--test-enable`, `--test-tags` và `--stop-after-init` để chạy web.
Không đưa mật khẩu hoặc cấu hình cá nhân vào Git.

## Demo trên máy hiện tại
- Cấu hình: `C:\Users\bac\AppData\Local\Temp\codex-fleet-demo-20260925\odoo.conf`.
- Database: `motorbike_fleet_demo_20260925`.
- Địa chỉ: http://localhost:8070 (chỉ lắng nghe trên máy này).
- Cấu hình và dữ liệu chạy nằm trong thư mục tạm; cần chuyển sang nơi bền vững
  trước khi dùng lâu dài. Đây là môi trường demo, không phải production.

Khởi động lại bằng PowerShell:

```powershell
& C:\odoo\venv\Scripts\python.exe C:\odoo\odoo-bin -c C:\Users\bac\AppData\Local\Temp\codex-fleet-demo-20260925\odoo.conf
```

1. Đăng nhập tài khoản demo được cung cấp khi bàn giao.
2. Mở Fleet → Fleet → Xe máy điện, mở xe biển số DEMO-EV-001.
3. Xem tab Xe máy điện, thay đổi sức khỏe pin và lưu.
4. Nhập sức khỏe pin 101 hoặc dung lượng âm để xem thông báo lỗi; hủy thay đổi.
5. Mở Services/Dịch vụ, chọn hồ sơ của xe demo. Xem hạng mục Pin,
   kết quả, ngày tiếp theo; chuyển New → Running → Done.
6. Tạo xe mới: chọn model, nhập biển số và thông số pin.
7. Tạo hồ sơ dịch vụ liên kết xe; thử ngày tiếp theo trước ngày thực hiện.

## File thay đổi
Chỉ trong `custom_addons/motorbike_fleet_management`:
- `__init__.py`, `__manifest__.py`
- `models/__init__.py`, `models/fleet_vehicle.py`, `models/fleet_service.py`
- `security/groups.xml`, `security/ir.model.access.csv`
- `views/fleet_views.xml`
- `tests/__init__.py`, `tests/test_fleet.py`
- `README.md`

- `data/service_type.xml`: loại dịch vụ Bảo dưỡng xe điện.

## Kết quả xác minh (25/09/2026)
- Odoo 19.0, Python 3.12.10, PostgreSQL 18 trên Windows.
- Cài mới database `motorbike_fleet_clean_20260925`: 4/4 test đạt, 0 lỗi.
- Nâng cấp database demo: 4/4 test đạt, 0 lỗi.
- Test gồm giới hạn thông số pin, ngày và quan hệ bảo dưỡng,
  quyền Officer/Technician/Administrator/người ngoài Fleet và cách ly xe đa công ty.
- Đã đăng nhập trên trình duyệt, mở xe DEMO-EV-001 và xác nhận tab Xe máy điện
  hiển thị sê-ri, dung lượng 3.50 kWh, điện áp 72 V, sức khỏe 95%, sạc 5 giờ.
- Tài khoản demo lưu ngoài Git tại thư mục cấu hình: `demo-login.txt`.
- PostgreSQL Windows trên máy này: để tránh lỗi locale khi Odoo tự tạo database,
  tạo trước database trống bằng PostgreSQL rồi chạy lệnh cài module.
- Đây là bản nền đã kiểm thử độc lập; chưa xác nhận Data Contract và chưa kiểm thử tích hợp với Rental Core, Operation, Finance trên database chung. Chưa đủ tiêu chí hoàn thành sprint tích hợp của nhóm.
