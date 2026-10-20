# Thông báo phiếu bảo dưỡng mới — 20/10/2026

Fleet 18.0.5.11.0. Dùng mail.activity chuẩn Odoo, không tạo bảng nghiệp vụ riêng.

Khi tạo phiếu mới còn Mới/Đã lên lịch cho xe điện đang sử dụng, tạo Hoạt động “Phiếu bảo dưỡng mới #ID — Mã xe”, hạn hôm nay, có nội dung phiếu và liên kết mở phiếu. Áp dụng cả phiếu thủ công và phiếu định kỳ tự động. Xem từ biểu tượng đồng hồ trên thanh trên cùng hoặc phần hoạt động của phiếu. Không phải hộp thoại bắt buộc xuất hiện, không phải banner đỏ quá hạn bảo dưỡng của xe.

Người nhận ưu tiên người quản lý được gán trên xe nếu tài khoản nội bộ đang hoạt động, đúng công ty và có quyền đọc phiếu. Nếu chưa có người phù hợp, dùng quản lý Fleet đủ quyền cùng công ty; không giao cho tài khoản hệ thống ẩn. Không tạo thêm quyền truy cập cho người nhận. Nếu không có người nhận phù hợp thì không thể giao hoạt động; cần cấu hình quản lý Fleet.

Một hoạt động cho mỗi người nhận/phiếu; gọi lại không tạo trùng hoạt động đang mở. Không phát email thông báo phân công; hoạt động vẫn xuất hiện trong ứng dụng và cập nhật bộ đếm qua bus Odoo. Khi Bắt đầu, Hoàn tất hoặc Hủy phiếu, đóng các hoạt động loại này; không đóng hoạt động khác. Người nhận cũng có thể đánh dấu hoàn tất hoạt động; thao tác đó không hoàn tất phiếu bảo dưỡng.

Không tạo hoạt động cho lịch sử hoàn tất/hủy hoặc quá trình nạp XML nâng cấp/cài đặt, không thông báo hồi tố mọi phiếu cũ. Không thay đổi trạng thái xe hoặc kết quả kỹ thuật chỉ vì có thông báo.

Kiểm tra trên database riêng: 79/79 Fleet đạt, gồm 4 kiểm tra mới về người nhận, tự động đến hạn, chống trùng, đóng nhắc việc, lịch sử và cài đặt. Source và database đã được sao lưu trước thay đổi trong archive/before-service-notifications-*. Chưa push thay đổi này lên GitHub.
