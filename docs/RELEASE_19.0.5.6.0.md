# Bản Fleet chuẩn bị bàn giao lên nhánh riêng — 19.0.5.6.0

Ngày 16/10/2026. Phạm vi: sửa các điểm ưu tiên và lỗi kiểm thử đã xác nhận, giữ những thay đổi local trước đó. Chỉ áp dụng cho Fleet Odoo 19; không phải bản tích hợp dev/Odoo 18.

## Sửa trong đợt này

1. Chặn xóa xe đang thuê/bảo dưỡng và xe có hồ sơ bảo dưỡng (gồm lưu trữ). Kiểm tra quyền unlink trước khi kiểm tra liên kết.
2. Không cho bỏ cờ xe điện khi đã có hồ sơ bảo dưỡng, kể cả done/cancelled/lưu trữ; tránh mất đường tra cứu và vượt các ràng buộc dành cho xe điện.
3. Ghi thẳng từ trạng thái khác về available bị từ chối. Nút xác nhận kỹ thuật và API trả xe dùng đường cập nhật nội bộ, vẫn kiểm tra ACL và các điều kiện nghiệp vụ.
4. Không sao chép biển số. Bản sao nhận mã xe mới qua sequence; kiểm thử sao chép không còn thất bại.
5. Khi hoàn tất và khi xóa phiếu, cùng xét hồ sơ đã lưu trữ để xác định mốc bảo dưỡng mới nhất. Kiểm thử phiếu mới hơn đã lưu trữ không bị phiếu cũ ghi đè ngày trên xe; xóa nguồn mới nhất thì lấy lại nguồn còn lại.
6. Giữ cột ID phiếu trên danh sách bảo dưỡng và default_order=id desc; người dùng có thể bấm cột để đảo chiều.

## Kiểm chứng

- Nâng cấp demo: 56/56 kiểm thử đạt, 0 failed, 0 errors. Bao gồm bốn trường hợp từng thất bại và hai tình huống hồ sơ lưu trữ mới bổ sung.
- `FLEET_RELEASE_1956_DATA_PRESERVATION.json` đối chiếu các bản ghi xe/bảo dưỡng/ODO và ODO hiện tại, không có thay đổi ngoài dự kiến. Bản ghi thử của TransactionCase được rollback.
- Backup trước nâng cấp: archive/before-fleet-integration-20261016-191645 (được Git bỏ qua).
- Kiểm tra web giao/trả/ODO/lịch bảo dưỡng/unique/form sau khi nạp lại server: PASS. Giữ 42 xe, 302 phiếu và 0 log ODO có sẵn sau kiểm tra; schema SQL xuất lại và kiểm tra trong transaction đạt.

Kết quả 54/54 và báo cáo BA trước đó là snapshot của thời điểm khác. Không dùng các báo cáo đó để suy luận source đã đóng băng hoặc mọi phiên bản về sau vẫn đạt.

## Giới hạn còn giữ nguyên

- Chưa merge dev, chưa kiểm trên Odoo 18 hoặc đủ Contract/Operations/Finance.
- Giữ quy ước người dùng: nhận trả về pending_inspection; chỉ dùng passed khi đã xác nhận đạt. Operations cần dùng API chính thức thay vì write thẳng available.
- Chưa mở rộng kỹ thuật viên/nhà cung cấp/loại dịch vụ theo tài liệu NV chưa được nhóm xác nhận; không tự coi chúng là yêu cầu mới của GQ/BS.
- Đường xem lịch sử ODO và việc ghi log cho mọi write ODO trực tiếp chưa được mở rộng trong đợt bốn điểm ưu tiên này. API giao/trả vẫn ghi log chuẩn.
- Không thêm bảo hành riêng, kho pin, phụ tùng hoặc mô hình hợp đồng/phiếu giả.
- Dữ liệu PostgreSQL/filestore local không được đưa lên GitHub. Máy khác cần cài hoặc upgrade module và kiểm tra dữ liệu trùng trước khi bật các constraint mới.

Nhánh riêng dùng để bàn giao/review phần Fleet; báo cáo này không xác nhận toàn bộ hệ thống nhóm đã sẵn sàng nghiệm thu.
