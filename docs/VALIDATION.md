# Xác minh phạm vi tuần 6 — 02/10/2026

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

Chưa triển khai/kiểm thử tích hợp Rental, Inspection, availability, đồng bộ giao–trả, workflow, validation nghiệp vụ tuần 7, Kanban hoặc report custom. Các công cụ sẵn có của Fleet chuẩn được giữ nguyên. Không thực hiện toàn bộ thao tác bằng click trình duyệt; dùng Odoo Form và RPC của ứng dụng web.
