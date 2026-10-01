# Fleet & Maintenance tuần 6 — Odoo 19

Module `motorbike_fleet_management`, phiên bản `19.0.2.0.0`, triển khai model và UI/CRUD theo Database Final V2 trong phạm vi tuần 6.

## Những gì đã có

- Mở rộng `fleet.vehicle`: mã xe, vòng đời, trạng thái vận hành, technical ready, khóa thuê, SOC tối thiểu và mốc bảo dưỡng.
- Mở rộng `fleet.vehicle.odometer`: nguồn ghi nhận, liên kết bảo dưỡng và ghi chú; dùng List/Form ODO chuẩn.
- Mở rộng `fleet.vehicle.log.services`: loại bảo dưỡng, thời gian dự kiến/thực tế, khóa lịch thuê, kỹ thuật viên, kết quả; dùng vendor và chi phí chuẩn.
- `motorbike.battery`: tài sản pin riêng, mã/serial duy nhất, dung lượng, điện áp, SOC/SOH, chu kỳ sạc, trạng thái, bảo hành.
- `motorbike.battery.assignment`: lịch sử gắn/tháo. Pin hiện tại trên xe và xe hiện tại trên pin được lấy từ lần gắn chưa tháo. SOC/SOH trên xe chỉ đọc từ pin.
- `motorbike.maintenance.plan`: chu kỳ km/ngày, lần trước, lần tiếp theo và ngưỡng cảnh báo.
- Fleet → Fleet: Xe máy điện, Pin xe điện, Bảo dưỡng xe điện; mỗi action mới dùng List/Form.
- Kế hoạch bảo dưỡng ở Fleet → Configuration và trong tab hồ sơ xe. Lịch sử pin nằm trong hồ sơ xe/pin, không thêm menu chính.

## Cách nhập liệu tuần 6

1. Với tài khoản Fleet Administrator, tạo pin tại Pin xe điện.
2. Tạo xe tại Xe máy điện, chọn model, nhập biển số và mã xe, mở tab Xe máy điện.
3. Mở Lịch sử pin, thêm pin và thời điểm gắn, lưu. Trường Pin hiện tại tự cập nhật.
4. Để thay pin: điền thời điểm tháo cho dòng cũ và lưu trước; sau đó thêm dòng pin mới và lưu. Một xe/một pin chỉ có một lần gắn chưa tháo; không được trùng khoảng lịch sử. Chưa có wizard thay pin.
5. Trạng thái pin (đã gắn/sẵn sàng/đang sạc...), trạng thái xe, technical ready và các mốc bảo dưỡng hiện được cập nhật thủ công. Lịch sử gắn pin là nguồn xác định pin hiện tại, không phải trường trạng thái pin.
6. Tạo hồ sơ Bảo dưỡng xe điện; nhập loại, hạng mục, thời gian, kỹ thuật viên/vendor, mô tả, chi phí và kết quả. Sửa chi phí rồi lưu để kiểm tra Update.
7. Tạo kế hoạch ở tab Kế hoạch bảo dưỡng trên xe hoặc menu Configuration; thử chu kỳ 5.000 km/180 ngày. Mốc tiếp theo nhập tay ở tuần 6, chưa tự tính hoặc tổng hợp về xe.
8. Xem/thêm/sửa ODO bằng giao diện Odometers chuẩn; chưa chặn ODO thấp hơn lịch sử trong phạm vi tuần 6.

## Mapping với Database V2

| Khái niệm V2 | Cách triển khai trên Odoo |
| --- | --- |
| Draft / Scheduled / In Progress / Done / Cancelled | Giữ `state`: `new` / `scheduled` / `running` / `done` / `cancelled`; không đổi key chuẩn Odoo |
| `cost` | Alias ghi được của `amount`, tránh lưu chi phí hai nơi |
| `result` | Alias ghi được của `maintenance_result` tuần 5 |
| Mô tả chi tiết | Tái sử dụng `description` và `notes` của dịch vụ Fleet |
| `technician_id` | Tiếp tục liên kết `res.partner` như tuần 5 |
| `inspection_id`, `incident_id` | Chờ model/Data Contract Operations ở tuần tích hợp; không tạo quan hệ giả |

`technical_ready` mặc định false và xe mặc định chờ kiểm tra. `operational_status = available` chưa phải kết quả kiểm tra khả dụng theo lịch.

## Quyền truy cập

ACL Odoo cộng dồn theo các nhóm. Giữ quyền Fleet có sẵn, không giả lập hạn chế bằng cách chỉ ẩn nút trên form.

| Nhóm | Xe/ODO | Bảo dưỡng | Pin / lịch sử pin / kế hoạch |
| --- | --- | --- | --- |
| Fleet Officer | CRUD theo Fleet chuẩn | Đọc | Đọc |
| Kỹ thuật viên xe điện | Kế thừa Officer, vẫn có CRUD | Tạo/đọc/sửa, không cấp xóa | Đọc |
| Fleet Administrator | CRUD | CRUD | CRUD |
| Nội bộ không có nhóm Fleet | Không cấp quyền | Không cấp quyền | Không cấp quyền |

Nếu cần kỹ thuật viên chỉ đọc xe như ví dụ trong tài liệu tham khảo, phải thiết kế lại nhóm kế thừa ở giai đoạn rà quyền. Chưa thay đổi mô hình này trong tuần 6. Các model custom phục vụ một cửa hàng, chưa bổ sung phân tách đa công ty; quy tắc công ty của model Fleet chuẩn được giữ nguyên.

## Nâng cấp từ tuần 5

Migration `migrations/19.0.2.0.0/post-migrate.py` chuyển thông tin pin cũ của xe điện sang pin riêng và tạo lịch sử gắn hiện tại.

- Giữ serial, dung lượng, điện áp, SOH và hạn bảo hành; mã pin chuyển đổi là `LEGACY-VEH-<id>`.
- SOC cũ chưa tồn tại nên để 0, cần nhập mức thực tế sau nâng cấp.
- Thời điểm gắn tạo khi nâng cấp và có ghi chú đây không phải thời điểm gắn lịch sử thực tế.
- Nếu serial cũ trùng nhau, dừng nâng cấp và yêu cầu đối chiếu, không tự đoán hai xe đang dùng chung một pin.
- Các field pin tuần 5 được giữ để bảo toàn dữ liệu, nhưng ẩn khỏi UI mới và không dùng làm nguồn thông số pin hiện tại. Code bên ngoài đang ghi các field cũ cần chuyển sang model pin.
- Mốc bảo dưỡng tuần 5 trên từng dịch vụ được giữ nguyên; không tự suy diễn thành kế hoạch định kỳ.

Sao lưu database và filestore trước khi nâng cấp môi trường khác. Với Python/môi trường Odoo đã cấu hình:

```powershell
& <python-odoo> <odoo-bin> -c <config> -d <database-demo> -i motorbike_fleet_management --without-demo=all --test-enable --test-tags /motorbike_fleet_management --stop-after-init
& <python-odoo> <odoo-bin> -c <config> -d <database-demo> -u motorbike_fleet_management --test-enable --test-tags /motorbike_fleet_management --stop-after-init
```

## Bản demo trên máy hiện tại

- Địa chỉ: http://localhost:8071
- Database: `motorbike_fleet_week6_upgrade_20261001` — bản sao nâng cấp từ demo tuần 5.
- Giữ tài khoản đăng nhập của demo tuần 5. File thông tin đăng nhập nằm ngoài Git: `%TEMP%/codex-fleet-demo-20260925/demo-login.txt`.
- Cấu hình và trình chạy: `%TEMP%/codex-fleet-week6-20261001/odoo.conf` và `run_odoo.py`.
- Có XE001–XE003, BAT001–BAT003, ba lịch sử gắn pin, ba kế hoạch, ODO và hồ sơ bảo dưỡng đã thử sửa chi phí 500.000 → 650.000.
- Database demo tuần 5 không bị nâng cấp trực tiếp. Bản sao lưu trước nâng cấp: `%TEMP%/codex-fleet-week6-20261001/week5-before-upgrade.dump`.

Khởi động lại nếu server đã dừng:

```powershell
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" "$env:TEMP/codex-fleet-week6-20261001/run_odoo.py" -c "$env:TEMP/codex-fleet-week6-20261001/odoo.conf"
```

Trình chạy dùng thư viện Odoo hiện có tại `C:/odoo/venv/Lib/site-packages`. Cấu hình, log và filestore demo đang ở thư mục tạm, cần lưu sang vị trí bền vững nếu dùng lâu dài.

## Kết quả kiểm tra ngày 01/10/2026

- Cài mới trên database riêng: 6/6 test đạt, không lỗi.
- Nâng cấp bản sao tuần 5: 6/6 test đạt; migration giữ serial, dung lượng và SOH của xe demo cũ.
- Sau khi bổ sung kiểm thử Form và giao diện ODO: 7/7 test đạt trên bản nâng cấp.
- Test bao gồm CRUD các model mới, pin hiện tại và SOC liên quan, đóng/thay/xóa lịch sử pin, khoảng gắn trùng, chi phí/kết quả alias, quyền theo nhóm, cách ly xe theo công ty và Form xe/pin/ODO/bảo dưỡng/kế hoạch.
- Bộ dữ liệu mẫu đã tạo và lưu qua Odoo Form; trang đăng nhập demo đã mở thành công trên trình duyệt. Chưa thực hiện toàn bộ kịch bản CRUD bằng click trong trình duyệt.

## Ngoài phạm vi tuần 6

Chưa triển khai availability, overlap Rental/Maintenance, integration với Rental/Operations/Finance, automation giao/trả/đổi pin/bảo dưỡng, tính mốc kế hoạch tự động, Kanban custom, bộ lọc mới hoặc báo cáo. Bộ lọc xe điện và các view chuẩn đã có của Odoo được giữ lại.
