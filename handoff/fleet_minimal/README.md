# SQL và DBML Fleet hiện hành

Snapshot `19.0.5.1.0`, 12/10/2026. `Fleet_Minimal_Current.sql` chứa cấu trúc hai bảng Fleet chuẩn được mở rộng, gồm PK/FK/index và UNIQUE(vehicle_code); không chứa dữ liệu kinh doanh/mật khẩu. `Fleet_Week8.dbml` dùng cho ERD nghiệp vụ, giữ quyết định tạm ẩn trường chờ giáo viên.

Mã đã cấp là duy nhất kể cả xe lưu trữ; cho phép nhiều NULL khi chưa cấp mã. ODO là compute/inverse chuẩn, không phải cột SQL trên xe. Các phương thức giao/trả, validation, quyền và workflow nằm trong ORM nên SQL này không thay thế cài/nâng cấp module.

`scripts/export_minimal_schema.py --config <local-config>` xuất schema thực tế và thực thi DDL trong schema tạm để đối chiếu rồi rollback; không thay đổi dữ liệu public. File Week6/Physical và các ZIP cũ là snapshot lịch sử trước khi thêm UNIQUE, không dùng để suy ra ràng buộc hiện hành.

Hướng dẫn gọi phương thức: `handoff/Fleet_Integration_Week8.md`. Cài/chạy: README module. Không đưa dump database hoặc cấu hình có mật khẩu lên GitHub.
