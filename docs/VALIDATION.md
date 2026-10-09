# Xác minh tuần 7 — 09/10/2026

Module `motorbike_fleet_management` `19.0.4.0.0`, Odoo 19. Dừng ở `Ke hoach Sprint!F17:I17`, không triển khai tích hợp tuần 8. Không thêm cột/bảng nghiệp vụ; DBML tạm chờ giáo viên được giữ nguyên.

| Kiểm tra | Kết quả |
| --- | --- |
| Cài mới `motorbike_fleet_week7_final_20261009` | 18/18 test, 0 failed, 0 errors |
| Nâng cấp `motorbike_fleet_simple_20261002` | 18/18 test, 0 failed, 0 errors |
| Form CRUD xe/bảo dưỡng, cost alias | Đạt |
| Chi phí/thời gian/lịch dự kiến/mốc tiếp theo | Đạt validation |
| Điều kiện available, lý do khóa thuê, rented/archived | Đạt |
| Lên lịch → Bắt đầu → Hoàn tất/Hủy | Đạt; timestamps tự điền, giữ timestamps đã nhập |
| Nhiều hồ sơ chạy chặn thuê trên một xe | Chỉ trả về inspection khi hồ sơ cuối kết thúc |
| Không chặn thuê, hủy lịch chưa bắt đầu | Không đổi tình trạng xe |
| Xác nhận đạt kỹ thuật | Kiểm tra hồ sơ chạy, trạng thái thuê/lưu trữ; giữ khóa chủ động |
| Chuyển state trực tiếp qua write/RPC | Rule server có hiệu lực |
| Sửa lịch sử/cập nhật mốc từ hồ sơ cũ | Không ghi đè trạng thái/mốc hiện tại ngoài luồng quy định |
| ODO chuẩn | Chặn âm và giảm theo ngày, gồm ghi bổ sung ở giữa/sửa log |
| ACL/công ty chuẩn và phạm vi xe điện | Đạt |
| Search views, action List/Kanban/Form, bốn nhóm Kanban gồm nhóm trống | Đạt qua ORM và get_views/RPC |
| Web RPC admin | Luồng bảo dưỡng, validation, tìm kiếm, view loading đạt; bản ghi thử đã xóa |
| Dữ liệu toàn bộ xe/bảo dưỡng/ODO trước–sau nâng cấp | SHA256 bằng nhau; 39 xe, 300 bảo dưỡng, 0 ODO |

Kết quả fingerprint: `docs/WEEK7_DATA_PRESERVATION.json`. Dữ liệu test ORM rollback; RPC chỉ tạo/xóa bản ghi thử riêng, số lượng dữ liệu gốc giữ nguyên. Code tuần 6 sao lưu ở `archive/before-week7-code-735162a.zip`; database trước nâng cấp ở `archive/before-week7-20261009-140655/database.dump`.

Log hiện tại: `%LOCALAPPDATA%/Temp/codex-fleet-week7-20261009/motorbike_fleet_week7_final_20261009.log`, `upgrade.log`, `server.log`. Demo đang chạy tại http://localhost:8072, admin/admin. Runner/config mới mô tả trong README module.

Giới hạn kiểm tra UI: Computer Use dừng vì không xác định được URL Chrome đủ chắc chắn để thực thi policy. Không tiếp tục tự động hóa UI. Đã kiểm tra view hợp lệ khi cài/nâng cấp, Odoo Form, tải view bằng RPC và dữ liệu nhóm Kanban; chưa xác minh hình thức hiển thị bằng click/screenshot.

Không kiểm thử Rental/Inspection/availability, giao–trả liên module hoặc báo cáo, vì chưa triển khai trong tuần 7.

## Lịch sử kiểm tra tuần 6 — 02/10/2026

Module `motorbike_fleet_management`, Odoo 19, phiên bản `19.0.3.1.0`. Phạm vi nguồn: `ERP_Odoo (1).xlsx`, `Ke hoach Sprint!F13:I13` (Fleet của Bắc).

| Kiểm tra | Kết quả |
| --- | --- |
| Cài mới `motorbike_fleet_week6_crud_clean_20261002` | 6/6 test, 0 failed, 0 errors |
| Nâng cấp demo `motorbike_fleet_simple_20261002` | 6/6 test, 0 failed, 0 errors |
| Odoo Form xe: tạo/xem/sửa/xóa, sửa trực tiếp trạng thái/kỹ thuật | Đạt |
| Odoo Form bảo dưỡng: tạo/xem/sửa/xóa, sửa trạng thái/thời gian/chi phí/kết quả | Đạt |
| Sửa hồ sơ bảo dưỡng không tự cập nhật xe hoặc ngày bảo dưỡng | Đạt |
| ACL cơ bản và quy tắc công ty chuẩn | Đạt |
| Action chỉ List/Form, không Search view hoặc API/workflow custom cũ | Đạt |
| Web CRUD đăng nhập admin qua RPC | Đạt; bản ghi tạm đã xóa |
| Schema SQL hai bảng trong schema tạm | DDL thực thi thành công; cột/kiểu/nullability trùng; rollback schema tạm |
| Dữ liệu trước/sau nâng cấp | Fingerprint toàn bộ 39 dòng xe và 300 dòng bảo dưỡng giống nhau |

Các test chạy trong transaction kiểm thử; bản ghi thử trên web cũng được xóa sau khi xác minh. Không thay đổi bộ dữ liệu đã tạo một năm. So sánh dữ liệu đọc được trong `docs/WEEK6_DATA_PRESERVATION.json`.

Logs:
- `%TEMP%/codex-fleet-simple-20261002/week6_clean.log`.
- `%TEMP%/codex-fleet-simple-20261002/week6_upgrade.log`.
- `%TEMP%/codex-fleet-simple-20261002/server.log`.

Demo: http://localhost:8072, admin/admin. Đã khởi động lại tiến trình để sử dụng code mới. Script web kiểm tra: `scripts/check_week6_web.py`.

Bản sao trước điều chỉnh: `archive/before-week6-scope-20261002/code.zip`, `database.dump`, filestore và `data-fingerprint.json`.

Tại mốc tuần 6 chưa triển khai/kiểm thử tích hợp Rental, Inspection, availability, đồng bộ giao–trả, workflow, validation tuần 7, Kanban hoặc report custom. Mục lịch sử này không mô tả bản tuần 7 hiện hành.
