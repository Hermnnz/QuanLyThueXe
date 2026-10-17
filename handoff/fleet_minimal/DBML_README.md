# DBML bàn giao Fleet — bản tạm chờ giáo viên chốt

## Bản nghiệp vụ hiện hành

Dùng `Fleet_Week8.dbml` để dán vào dbdiagram.io. Sơ đồ hiện chỉ có 4 bảng:

`fleet_vehicle_model_brand` → `fleet_vehicle_model` → `fleet_vehicle` → `fleet_vehicle_log_services`.

Theo yêu cầu, tạm bỏ khỏi sơ đồ:
- `company_id` trên Xe và Bảo dưỡng.
- `vendor_id`, `service_type_id`, `technician_id` trên Bảo dưỡng.
- Bảng `res_company`, `res_partner`, `fleet_service_type` và các FK liên quan.

Còn 28 cột thuộc hai bảng nghiệp vụ Fleet, 8 cột danh mục Hãng/Dòng xe và 3 quan hệ. Không có Ref trỏ tới bảng hoặc cột đã bỏ. Sau khi hỏi giáo viên, nhóm mới quyết định có thêm lại các phần tạm bỏ hay không.

Đây là lựa chọn trình bày ERD, không phải thay đổi model hay schema đang chạy. Odoo vẫn giữ các trường/bảng chuẩn, trong đó `service_type_id` vẫn là trường bắt buộc của Fleet chuẩn.

## Bản đối chiếu thực tế

`Fleet_Week6_Physical.dbml` giữ nguyên để đối chiếu cấu trúc database tại mốc xuất tuần 6: 87 cột trong hai bảng Fleet, các FK gốc cùng quan hệ Hãng–Dòng xe. Các bảng tham chiếu ngoài Hãng/Dòng xe chỉ có id để vẽ quan hệ, không phải schema đầy đủ của chúng. Không dùng bản vật lý này thay cho bản nghiệp vụ tạm khi trao đổi phạm vi với giáo viên.

Bản nghiệp vụ trước khi lược cột đã được lưu tại `archive/Fleet_Week6_before_teacher_review.dbml`. Script `scripts/export_week6_dbml.py` chỉ phục vụ snapshot SQL tuần 6 và dừng nếu nhận SQL hiện hành, tránh ghi đè sơ đồ lịch sử với ràng buộc thiếu.

## Cách sử dụng

Mở `Fleet_Week8.dbml`, sao chép toàn bộ nội dung và dán vào vùng soạn thảo DBML tại https://dbdiagram.io/. Không gộp hai file DBML cùng lúc vì chúng định nghĩa trùng bảng Fleet.

Chi phí lưu ở `amount`; `cost` chỉ là alias ORM. Bản Week8 (19.0.5.1.0) cập nhật trạng thái/cách kiểm tra lịch và UNIQUE mã xe đúng Word, không thêm cột/bảng. Ràng buộc duy nhất áp dụng cả xe lưu trữ; nhiều NULL được phép khi chưa cấp mã. ODO tính toán chuẩn không phải cột SQL trên xe. Rental/Operations tự khai báo quan hệ tới xe trong sơ đồ toàn nhóm và gọi phương thức Fleet theo `handoff/Fleet_Integration_Week8.md`.

Các file Week6 là snapshot lịch sử; script `export_week6_dbml.py` xuất tài liệu cho mốc đó, không dùng để ghi đè bản Week8.

Tạo/sửa DBML không thay đổi database demo hoặc bộ dữ liệu một năm. File `.dbml` dùng để thiết kế và đối chiếu, không dùng cài/nâng cấp module Odoo.
