# Fleet & Maintenance — dừng ở tuần 6

Module `motorbike_fleet_management`, Odoo 19, phiên bản `19.0.3.1.0`.

Phạm vi theo kế hoạch `ERP_Odoo (1).xlsx`, sheet `Ke hoach Sprint`, hàng 13: menu/action, List/Form cho hồ sơ xe và bảo dưỡng, nhập thử bản ghi để kiểm tra Create/Read/Update. Giữ model, quan hệ và ACL cơ bản của tuần 5. Không triển khai nhiệm vụ tuần 7 trở đi.

## Những gì có thể dùng

- Fleet → Xe máy điện: danh sách, tạo hồ sơ xe, xem và sửa thông tin.
- Fleet → Bảo dưỡng xe điện: danh sách, tạo hồ sơ bảo dưỡng, xem và sửa chi phí/kết quả/thời gian/trạng thái.
- Hai model nghiệp vụ: `fleet.vehicle` và `fleet.vehicle.log.services` (kế thừa chuẩn Odoo).
- Danh mục model xe, loại dịch vụ, partner/vendor, công ty và tiền tệ dùng lại của Odoo.
- Không quản lý pin như tài sản riêng, không lịch sử gắn/tháo pin, không kế hoạch bảo dưỡng riêng, không mở rộng ODO. ODO chuẩn vẫn tồn tại.

## Nhập liệu thủ công

Trên form xe, nhập mã xe, model/biển số, `operational_status`, `technical_ready`, `rental_blocked`, lý do và ngày bảo dưỡng tiếp theo. Tất cả trường nghiệp vụ này đều sửa được theo quyền xe chuẩn; chưa có workflow hay validation nghiệp vụ tùy chỉnh. `active` chuẩn dùng lưu trữ xe.

Trên form bảo dưỡng, chọn xe và loại dịch vụ, nhập loại bảo dưỡng, kỹ thuật viên/vendor, thời gian dự kiến/thực tế, trạng thái, chi phí và kết quả. `state` giữ key Odoo `new`, `scheduled`, `running`, `done`, `cancelled`; trạng thái được chọn trực tiếp. `actual_start`/`actual_end` do người dùng nhập, không tự ghi giờ hiện tại.

`cost` là alias ghi được của `amount`, không lưu chi phí hai nơi. `technician_id` liên kết `res.partner`. Quan hệ xe–bảo dưỡng là 1:N, dùng `vehicle_id` và `log_services` chuẩn.

**Ghi nhận chặn/khóa thuê chỉ là dữ liệu nhập ở tuần 6.** Chưa có cơ chế chặn thuê thực tế. Sửa trạng thái bảo dưỡng không đổi trạng thái xe, điều kiện kỹ thuật hoặc ngày bảo dưỡng tiếp theo của xe; nhân viên nhập các thông tin đó riêng.

Không có các nút xác nhận kỹ thuật/giao/trả/bắt đầu/hoàn tất tùy chỉnh. Không có Search/Filter/Kanban/report tùy chỉnh; các công cụ chuẩn đi kèm module Fleet vẫn tồn tại. Hai action mới chỉ mở List/Form.

## Quyền cơ bản

| Nhóm | Xe | Bảo dưỡng |
| --- | --- | --- |
| Fleet Officer | CRUD chuẩn Odoo | Đọc |
| Kỹ thuật viên xe điện | Kế thừa Officer | Tạo/đọc/sửa, không cấp xóa |
| Fleet Administrator | CRUD | CRUD |
| Nội bộ không thuộc Fleet | Không cấp quyền | Không cấp quyền |

Giữ ACL và quy tắc công ty chuẩn. Chưa thêm quyền riêng cho từng thao tác nghiệp vụ.

## Chưa triển khai

Tuần 7: Search/Filter/Kanban tùy chỉnh, validation nghiệp vụ, workflow trạng thái và tự cập nhật mốc bảo dưỡng.
Tuần 8: API availability, kiểm tra lịch Rental/Maintenance, đồng bộ giao/trả, liên kết Inspection/Rental.
Các tuần sau: xử lý ngoại lệ liên module, báo cáo mới và E2E hệ thống. Không để API stub hoặc nút nghiệp vụ chưa làm trên bản tuần 6.

ERD hiện hành: `docs/Fleet_Minimal_ERD.md`. SQL schema: `handoff/fleet_minimal/Fleet_Minimal_Current.sql`. Các bản bàn giao pin/ODO/kế hoạch tuần 6 cũ là lịch sử trước khi chốt kiến trúc tối giản.

## Demo và dữ liệu

- URL: http://localhost:8072.
- Database: `motorbike_fleet_simple_20261002`.
- Tài khoản demo: `admin` / `admin`.
- Giữ nguyên bộ dữ liệu đã tạo: 39 xe và 300 hồ sơ bảo dưỡng, bao gồm xe/hồ sơ lưu trữ. Số liệu một năm chỉ là fixture có sẵn để nhập/xem/sửa; không coi là hoàn thành nhiệm vụ báo cáo tuần 10.
- Xem `docs/FLEET_YEAR_DEMO.md` để biết dữ liệu giả lập và cách xem hồ sơ lưu trữ.

Khởi động trên máy hiện tại:

```powershell
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" `
  "$env:TEMP/codex-fleet-week6-20261001/run_odoo.py" `
  -c "$env:TEMP/codex-fleet-simple-20261002/odoo.conf"
```

Config, log và filestore demo nằm tại `%TEMP%/codex-fleet-simple-20261002`; không lưu mật khẩu kết nối trong repo.

## Cài đặt và kiểm tra

```powershell
& <python-odoo> <odoo-bin> -c <config> -d <database-moi> -i motorbike_fleet_management --without-demo=all --test-enable --test-tags /motorbike_fleet_management --stop-after-init
```

`scripts/validate_local.py --fresh` cài trên database kiểm thử tuần 6 riêng, không ghi đè database đã có. `--upgrade` nâng cấp demo tối giản hiện tại và chạy kiểm thử CRUD. Không dùng script này để nâng cấp trực tiếp database tuần 6 có kiến trúc pin cũ.

Bộ kiểm thử hiện hành: Form xe/bảo dưỡng Create/Read/Update/Delete; quyền cơ bản; quy tắc công ty chuẩn; trạng thái/thời gian sửa bằng tay; sửa bảo dưỡng không đồng bộ xe; phạm vi chỉ List/Form. Kết quả xem `docs/VALIDATION.md`.

## Sao lưu

Trước khi đưa về tuần 6, lưu code/database/filestore ở `archive/before-week6-scope-20261002/`. Bộ dữ liệu một năm còn bản backup tại `archive/year-demo-20261002/`; các backup database không đưa vào Git. Bản code trước tối giản pin nằm ở `archive/fleet-before-simplification.zip`.
