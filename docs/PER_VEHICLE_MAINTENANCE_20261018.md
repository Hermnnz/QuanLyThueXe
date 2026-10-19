# Bảo dưỡng cấu hình riêng từng xe — 18/10/2026

Fleet 18.0.5.9.0; Demo 18.0.1.2.2. Menu: **Quản lý xe**.

Vào Phương tiện → chọn xe → Bảo dưỡng định kỳ. Nhập chu kỳ km, chu kỳ tháng, báo trước km/ngày, mốc ngày và ODO đã xác minh rồi lưu. Đặt chu kỳ 0 để tắt tiêu chí tương ứng. Mốc nào đến trước sẽ cảnh báo; không tự khóa xe hay tự tạo phiếu.

Bốn trường cấu hình nằm trên `fleet.vehicle`, không còn là related từ `fleet.vehicle.model`. Đổi cấu hình một xe hoặc đổi dòng xe không thay đổi cấu hình xe khác. Xe mới mặc định chưa đặt chu kỳ, báo trước 200 km/7 ngày; không tự kế thừa từ dòng xe. Mốc ban đầu và lịch sử hoàn thành vẫn riêng từng xe.

Migration 18.0.5.9.0 sao chép bốn giá trị cũ từ dòng xe xuống mọi xe hiện có, kể cả xe đã lưu trữ, một lần. Không ghi đè cấu hình riêng khi nâng cấp tiếp. Dữ liệu dòng xe cũ được giữ để tham khảo nhưng không được dùng tính lịch; popup cấu hình cũ bị vô hiệu hóa, không còn nút mở trên hồ sơ xe. Thư mục `legacy/model_policy_18_0_5_8_0` giữ nguyên code, view, test cũ, không được import.

Demo XML nay đặt bốn trường trực tiếp trên từng xe; giữ XML ID và không reset lịch sử đã nạp. Cấu hình minh họa của cửa hàng, không phải khuyến nghị nhà sản xuất.

## Xác nhận

Bản sao: 16 kiểm tra đạt. Database chạy cổng 8078: 21 kiểm tra đạt, bao gồm cảnh báo, độc lập cấu hình cùng dòng, các trường giao diện và dữ liệu demo. Đối chiếu 8 bảng nghiệp vụ giữa bản sao và database trước triển khai: giữ nguyên 14 xe, 18 dòng xe, 10 phiếu bảo dưỡng, 3 số đo ODO, 3 hợp đồng/3 dòng, 2 phiếu vận hành/2 dòng. Việc nâng cấp có thay đổi dấu thời gian/người cập nhật kỹ thuật của xe; không thay đổi giá trị nghiệp vụ cũ.

Sao lưu: xem `archive/latest-per-vehicle-backup.txt`. Có database.dump, source.zip, runtime.zip. Khi khôi phục cần dừng đúng Odoo 8078, khôi phục đồng thời database và runtime từ bản lưu; không ghi đè database đang chạy. Filestore hiện có được giữ nguyên, thay đổi này không xóa hay thay ảnh.

Chưa commit/push GitHub. Code khác của Rental/Operations/Finance không sửa.

## Thời gian thực hiện

Bắt đầu 10:37:35 giờ Việt Nam. Đến bước kiểm tra HTTP cuối: 332 giây (5 phút 32 giây). Thời lượng tới lúc trả lời có thêm thời gian ghi báo cáo. Hai lượt Odoo nâng cấp trên bản sao và bản chạy mỗi lượt khoảng 18–19 giây; thực thi test lần lượt 1,61 và 1,82 giây, đã nằm trong thời gian nâng cấp. Phần còn lại gồm đọc/sửa code, sao lưu/khôi phục bản sao, đối chiếu dữ liệu, tài liệu và vòng gọi công cụ. Cần sửa câu lệnh đối chiếu để bỏ cột audit kỹ thuật và dùng đúng tên bảng dòng vận hành. Tiến trình nâng cấp hoàn tất nhưng chưa thoát khi trình duyệt còn WebSocket, phải dừng tiến trình hoàn tất và chạy server bình thường. Không gọi Serena/DBHub trong lượt này, không có thời gian chờ phản hồi từ hai công cụ đó; chưa đo chi phí khởi động nền nếu có. Chi tiết trong PER_VEHICLE_MAINTENANCE_TIMING_20261018.json.
