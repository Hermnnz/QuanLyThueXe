# Tự tạo phiếu bảo dưỡng định kỳ — 20/10/2026

Fleet 18.0.5.10.0. Không thêm bảng hoặc trường dữ liệu mới.

- Xe đang sử dụng, là xe điện, đã có cấu hình chu kỳ và mốc xác minh: chạm hoặc vượt ODO hạn, hoặc đến/quá ngày hạn, thì hệ thống tạo phiếu `new` (Nháp/Mới), loại Định kỳ, ghi lý do vào Ghi chú, bật chặn thuê trên phiếu.
- Cập nhật ODO, chu kỳ hoặc mốc ban đầu, tạo xe hoặc khôi phục xe: xét ngay sau khi lưu thành công. ODO từ giao/nhận dùng cùng luồng.
- Theo thời gian: cron hiện có chạy mỗi ngày một lần, vừa tính cảnh báo vừa tạo phiếu. Không phải tác vụ chạy từng phút. Xe đến hạn sẵn khi nâng cấp được cron xử lý ở lần chạy tiếp theo; local đã chủ động chạy một lượt sau nâng cấp.
- Không tạo ở mức Sắp đến hạn, xe lưu trữ, xe không phải xe điện, thiếu mốc hoặc chưa cấu hình. Ngày hẹn thủ công riêng lẻ không tự tạo phiếu định kỳ nếu chu kỳ thực tế chưa đến hạn.
- Không tự bắt đầu bảo dưỡng, không tự đổi trạng thái xe hoặc khóa thuê. Xe đang thuê chỉ có phiếu Nháp chuẩn bị; muốn bắt đầu phải nhận trả trước theo quy tắc hiện có.
- Một phiếu định kỳ đang Mới/Đã lên lịch/Đang thực hiện sẽ ngăn tạo thêm, kể cả phiếu đã lưu trữ; khôi phục phiếu đó để tiếp tục. Khóa hàng xe dùng chung với nút tạo thủ công giúp tránh hai thao tác đồng thời tạo trùng.
- Phiếu hủy không có nghĩa đã bảo dưỡng: nếu vẫn đến hạn, lần kiểm tra tiếp theo có thể tạo lại. Phiếu hoàn tất có ODO chụp khi kết thúc đặt lại mốc theo quy tắc hiện có; đến kỳ mới sẽ tạo phiếu mới.
- Tạo tự động bằng quyền hệ thống, không phụ thuộc nhân viên nhập ODO có quyền tự tạo phiếu hay không. Quyền xem/sửa phiếu vẫn theo nhóm hiện có.
- Nạp dữ liệu cài đặt/nâng cấp (`install_mode`) không tạo phiếu ngay trong quá trình nạp XML, tránh sinh phiếu trước khi lịch sử mẫu được nạp xong. Cron xử lý sau đó.

Kiểm tra trên database riêng: 75/75 Fleet đạt, gồm 5 tình huống mới về ngưỡng km, ngày/cron, chống trùng, trạng thái xe và điều kiện bỏ qua. Không thêm liên kết khách hàng hoặc sự cố bên Operations.

Bản sao lưu trước thay đổi: đường dẫn trong `archive/latest-auto-preventive-backup.txt`, gồm code Fleet và database.dump. Không đổi hoặc xóa filestore.
