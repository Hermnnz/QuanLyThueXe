# Rà các tình huống nghiệp vụ ngoài kiểm thử hiện có

Ngày 16/10/2026, đọc source và tái hiện bằng `archive/audit_business_edges_20261016.py` qua Odoo shell của demo. Mỗi tình huống chạy trong savepoint, cuối cùng rollback toàn bộ. Không giữ các bản ghi thử. Không sửa logic nghiệp vụ trong đợt rà này.

## Đã tái hiện

| Tình huống | Kết quả | Đánh giá |
| --- | --- | --- |
| Tạo hai xe cùng biển số | Được phép | Chưa có unique/chuẩn hóa biển số; thiếu kiểm soát định danh thực tế. Word chưa có unique biển số |
| Tạo xe không nhập mã | Mã trống, không tự sinh | Không có ir.sequence; Word chỉ yêu cầu mã unique, không chỉ định tự sinh |
| Giảm ODO trực tiếp từ 1000 về 20 | Bị chặn bởi write chuẩn Odoo | Không phải lỗi được tái hiện |
| Lưu trữ xe đang renting | Được phép | Có thể làm xe đang khai thác biến khỏi danh sách mặc định |
| Ghi thẳng renting → available khi technical_ready=True | Được phép | Readonly UI không bảo vệ mọi đường ORM/import/RPC; bỏ qua bước nhận trả |
| Tạo phiếu với state=done nhưng không result/thời gian thực tế | Được phép | Đã chủ ý cho phép nhập lịch sử; chưa giới hạn bằng cơ chế nhập lịch sử chuyên biệt |
| Hoàn tất qua workflow rồi xóa result | Được phép | Ràng buộc kết quả chỉ chạy khi đổi state; có thể mất kết quả sau hoàn tất |
| Bắt đầu ngay phiếu lên lịch năm 2030 | Được phép, xe sang maintenance | Cho phép làm sớm; không tự coi là lỗi vì docs không cấm |
| Đang bảo dưỡng: bỏ is_electric_motorbike rồi ghi available/true | Được phép dù service vẫn running | Lỗ hổng đáng ưu tiên: quy tắc bảo vệ phụ thuộc cờ có thể sửa |
| Brand/model archived rồi tạo xe theo ID | Xe mới vẫn active và đạt fleet_ok | Không có quy tắc ngừng danh mục lan sang xe; docs chưa quy định phải lan trạng thái |

## Thiếu/chưa có trong source

- Chưa có bảo hành chuyên biệt (thời hạn, chính sách, yêu cầu bảo hành, nhà chịu phí). Hiện chỉ bảo dưỡng/sửa chữa, docs không giao phân hệ bảo hành riêng.
- Chưa có tự sinh mã xe, chuẩn hóa mã khi nhập (khoảng trắng/hoa thường).
- Giao diện ngừng sử dụng hãng/dòng xe chưa nhất quán; bộ lọc With Models mặc định che hãng mới chưa có dòng xe. Đã xác minh trong lượt kiểm tra trước, chưa sửa trong lượt này.
- Nhập ODO đầu kỳ trên form chỉ đọc; Operations/API có thể cập nhật.
- Sửa ngày/kết quả trên phiếu done không phải cơ chế sổ lịch sử bất biến; sửa/xóa phiếu done có mốc tiếp theo không tự tính lại next_service_date của xe theo source hiện tại.
- Có thể lập các lịch bảo dưỡng trùng nhau; code không cấm. Nhiều việc cho cùng xe có thể hợp lệ, cần quy tắc nhóm trước khi thêm cấm.
- Chưa xác nhận tích hợp xuyên module trên dev/Odoo 18; local chỉ xác nhận phần Fleet Odoo 19. Không tuyên bố mọi thao tác Operations đều gọi API Fleet.

Các điểm Word im lặng không tự động là lỗi hoặc là ủy quyền mở thêm phân hệ. Các kết quả trên không chứng minh đã tìm hết lỗi; test 43/43 trước đó chỉ bao phủ các trường hợp được viết.
