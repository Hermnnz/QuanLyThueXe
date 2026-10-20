# Luồng bảo dưỡng đơn giản — 20/10/2026

Fleet 18.0.5.12.0; Demo 18.0.1.2.3.

Bỏ trường scheduled_start/scheduled_end khỏi model đang dùng và mọi form/list/search; bỏ action_schedule, lựa chọn scheduled, nút Lên lịch, bộ lọc Đã lên lịch và Lịch dự kiến. Không đặt lịch bảo dưỡng theo khoảng thời gian nữa. Mới → Đang thực hiện → Hoàn tất/Hủy; có thể hủy ngay từ Mới.

Phiếu Mới không giữ lịch xe. Rental vẫn kiểm tra lịch hợp đồng; phiếu đang thực hiện và có chặn thuê vẫn chặn khai thác, không có ngày dự kiến trả xe. Bắt đầu vẫn chuyển xe sang Bảo dưỡng; phiếu cuối cùng hoàn tất/hủy trả xe về Chờ kiểm tra để xác nhận đạt kỹ thuật.

actual_start / actual_end giữ kiểu Datetime và tên kỹ thuật, đổi nhãn thành Ngày bắt đầu / Ngày kết thúc trên form/list. Nút Bắt đầu/Hoàn tất tiếp tục tự ghi thời điểm nếu chưa có. Không đổi dữ liệu thời gian cũ. Giữ service_odometer và cơ chế chụp ODO hoàn tất để tính kỳ kilomet tiếp theo. Không bổ sung liên kết khách hàng/sự cố.

Tự tạo phiếu khi đến hạn, chống trùng và thông báo phiếu mới nay chỉ xét phiếu Mới/Đang thực hiện. Không tạo thông báo hàng loạt khi nâng cấp XML.

Migration pre 18.0.5.12.0 chuyển phiếu scheduled sang new, kèm một dòng Ghi chú chứa lịch dự kiến cũ. Không xóa phiếu, kết quả, chi phí hoặc thời gian thực tế. Bản sao toàn bộ code/runtime/database trước thay đổi ở đường dẫn trong archive/latest-remove-planned-backup.txt. Dữ liệu dự kiến của bản cũ cũng có trong database.dump; các cột cũ không còn được code nghiệp vụ đọc hoặc ghi.

Demo giữ nguyên XML ID, bỏ lệnh lên lịch và dữ liệu dự kiến. Chỉ sửa bài kiểm tra tích hợp Operations bị ảnh hưởng, không sửa logic nghiệp vụ module đó. Kiểm tra bản gộp trên database riêng: 99/99 đạt, gồm Fleet, Rental Core/website, Operations và Demo.

Chưa push thay đổi này lên GitHub.
