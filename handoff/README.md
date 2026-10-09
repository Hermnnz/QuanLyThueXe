# Bản bàn giao hiện hành — cấu trúc tối giản, code đến tuần 7

Module `motorbike_fleet_management` `19.0.4.0.0`: hai model Xe/Bảo dưỡng, Search/Filter, Kanban đội xe, validation và workflow bảo dưỡng. Tuần 7 không thêm cột/bảng nghiệp vụ nên SQL/DBML giữ mốc tên tuần 6 vẫn dùng để đối chiếu cấu trúc. DBML nghiệp vụ vẫn tạm bỏ các trường chờ giáo viên chốt.

- ERD: `docs/Fleet_Minimal_ERD.md`.
- Hướng dẫn: `custom_addons/motorbike_fleet_management/README.md`.
- SQL hiện hành: `handoff/fleet_minimal/Fleet_Minimal_Current.sql`.
- Kiểm tra tuần 7 và lịch sử tuần 6: `docs/VALIDATION.md`.

Các thư mục `fleet_week6`, `Fleet_Week6_SQL_Handoff` và ZIP tuần 6 cũ là tài liệu lịch sử của kiến trúc có pin/ODO/kế hoạch riêng. Không dùng để hợp nhất schema hiện hành.

Chưa có availability theo thời gian, tích hợp Rental/Inspection, giao/trả liên module hoặc report tùy chỉnh. Bộ dữ liệu một năm được giữ lại làm dữ liệu thử, không phải chức năng báo cáo mới. Các ZIP đã xuất ở tuần 6 là snapshot tài liệu tại thời điểm đó; README trong repo phản ánh logic tuần 7.
