# SQL bàn giao Fleet tối giản — tuần 6

Phiên bản `19.0.3.1.0`, 02/10/2026. Snapshot cấu trúc hai bảng `fleet_vehicle` và `fleet_vehicle_log_services`, bao gồm cột chuẩn Odoo, PK/FK/index. Không chứa dữ liệu kinh doanh hoặc mật khẩu.

Dùng để đối chiếu ERD/schema. SQL không thay thế cài/nâng cấp module Odoo: không tạo metadata, menu/action, ACL, related field hoặc giao diện. `cost` là alias của `amount`, `result` là cột Text. Default ORM không tự trở thành SQL DEFAULT.

Tuần 6 chỉ có nhập liệu CRUD. Các cột trạng thái/kỹ thuật/khóa thuê/thời gian/ngày bảo dưỡng là dữ liệu nhập tay; không có trigger hoặc logic tự động đồng bộ. Không có availability, Rental/Inspection relation hoặc workflow tùy chỉnh.

Tái sử dụng danh mục chuẩn: res_users/res_partner/res_company, fleet_vehicle_model/brand/category/state, fleet_service_type và ODO chuẩn khi FK gốc tham chiếu. Nếu nhóm đã có các bảng Fleet, hợp nhất định nghĩa thay vì tạo chồng bảng.

`scripts/export_minimal_schema.py` xuất schema thực tế, thực thi DDL trong schema tạm, so sánh cột/kiểu/nullability rồi rollback đối tượng kiểm tra. Không chỉnh dữ liệu public.

Xem `docs/Fleet_Minimal_ERD.md` và README module. Các bàn giao Week6 có model pin ở thư mục bên cạnh là lịch sử trước khi chốt kiến trúc tối giản.
