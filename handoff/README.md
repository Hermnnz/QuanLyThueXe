> Bản bàn giao mới cho dev dùng Odoo 18. Xem [hướng dẫn tích hợp](../docs/INTEGRATION_DEV_18_20261016.md). Nội dung dưới đây giữ để tra cứu bản demo Odoo 19 trước đó.

# Bàn giao Fleet–Maintenance hiện hành

Module `motorbike_fleet_management` `19.0.5.6.0`, thêm phần Fleet cho tích hợp tuần 8: trạng thái thống nhất, giao/trả có kết quả kiểm tra, ODO chuẩn và điều kiện Fleet theo lịch bảo dưỡng.

- Điều hướng: ứng dụng Đội xe cho thuê mở thẳng Kanban mới; mục gốc nằm trong Quản lý chuẩn Odoo. Cấu trúc bảng không đổi; SQL được xuất từ bản đang cài, DBML vẫn giữ mốc schema 19.0.5.1.0.
- Cách thành viên Rental/Operations gọi: `Fleet_Integration_Week8.md`.
- DBML đưa vào dbdiagram: `fleet_minimal/Fleet_Week8.dbml`. Vẫn tạm ẩn company/vendor/service type/technician trong sơ đồ theo yêu cầu chờ giáo viên.
- Hướng dẫn chạy: `custom_addons/motorbike_fleet_management/README.md`.
- Kiểm thử: `docs/VALIDATION.md`; bảo toàn dữ liệu: `docs/FLEET_INTEGRATION_DATA_PRESERVATION.json`.

Không thêm cột/bảng nghiệp vụ mới. SQL hiện hành `fleet_minimal/Fleet_Minimal_Current.sql` mô tả cấu trúc có UNIQUE mã xe, không chứa dữ liệu demo và không thay thế nâng cấp module Odoo. Các DBML/ZIP tuần 6 và báo cáo tuần 7 là snapshot lịch sử; không dùng chúng để suy ra workflow hiện tại. Không đưa dump database, mật khẩu hoặc filestore lên GitHub.

Repo chỉ có Fleet. Các thành viên khác cần nối model và gọi phương thức đã bàn giao trước khi kiểm thử xuyên module.

Rà soát source bản 19.0.5.6.0: docs/SOURCE_AUDIT_20261016.md.
