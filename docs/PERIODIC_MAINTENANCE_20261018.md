# Bảo dưỡng định kỳ và cảnh báo — Fleet 18.0.5.8.0

## Sử dụng

1. Mở **Phương tiện → xe → Bảo dưỡng định kỳ**.
2. Quản trị Fleet bấm **Cấu hình chu kỳ dòng xe**: nhập chu kỳ km và/hoặc tháng; tiêu chí bằng 0 được bỏ qua. Ngưỡng báo sớm mặc định 200 km/7 ngày, cho phép thay đổi. Đây là ngưỡng phần mềm, không phải thông số bảo dưỡng của hãng.
3. Với xe cũ, nhập **Ngày mốc ban đầu** và **ODO mốc ban đầu** đã xác minh. ODO 0 là giá trị hợp lệ. Không tự suy đoán từ ngày mua xe hoặc từ phiếu lịch sử thiếu số đo.
4. Xem **Hạn bảo dưỡng** trên danh sách, nhãn Kanban và khung cảnh báo trong hồ sơ xe. Bộ lọc: Sắp đến hạn, Đến hạn, Quá hạn, Thiếu mốc ban đầu.
5. Kỹ thuật viên/quản trị bấm **Tạo phiếu bảo dưỡng định kỳ**. Nếu có phiếu định kỳ mới/lên lịch/đang chạy, nút chuyển sang **Xem phiếu định kỳ đang xử lý**; bấm lặp không tạo thêm phiếu. Tạo phiếu chưa tự bắt đầu bảo dưỡng.
6. Thực hiện quy trình Bắt đầu → nhập kết quả → Hoàn tất như hiện tại. Khi hoàn tất phiếu **Định kỳ**, ODO hiện tại được chụp vào phiếu; ngày kết thúc và ODO đó là mốc tính kỳ sau. Phiếu sửa chữa/khẩn cấp không đặt lại chu kỳ.

Ví dụ minh họa: chu kỳ 2.000 km/3 tháng, mốc ban đầu 1.000 km ngày 01/10 → mốc sau 3.000 km hoặc 01/01 năm sau; điều kiện nào đến trước thì cảnh báo. Ví dụ này không phải khuyến nghị kỹ thuật áp dụng cho VinFast/Dat Bike.

## Quy tắc

- Chưa có cấu hình → **Chưa cấu hình chu kỳ**; có cấu hình nhưng thiếu mốc → **Thiếu mốc ban đầu**.
- Còn trong ngưỡng báo trước → **Sắp đến hạn**; bằng đúng mốc → **Đến hạn**; vượt mốc → **Quá hạn**. Lấy mức nghiêm trọng nhất giữa ngày và km.
- Trường `next_service_date` cũ vẫn là ngày hẹn riêng và vẫn được xét cảnh báo. Phiếu định kỳ hoàn tất sẽ tiêu thụ ngày hẹn đã đến hạn nếu không chỉ định ngày hẹn mới; ngày hẹn tương lai được giữ.
- Cảnh báo không sửa `operational_status`, `technical_ready` hoặc `rental_blocked`. Việc khóa thuê theo phiếu bảo dưỡng giữ nguyên.
- Mốc tự động lấy từ phiếu định kỳ hoàn tất có ODO chụp hợp lệ mới nhất, kể cả phiếu lưu trữ. Phiếu lịch sử cũ không có ODO chụp không được tự biến thành mốc. Khi xóa phiếu mới nhất, mốc được tính lại từ phiếu còn lại/mốc ban đầu.
- Khi ODO, mốc hoặc cấu hình thay đổi, cảnh báo được tính lại. Tác vụ **Fleet: cập nhật hạn bảo dưỡng hằng ngày** cập nhật phần hạn theo ngày khi server đang chạy; cấu hình demo đã bật cron worker. Cần tải lại trang đang mở để thấy thay đổi, không có thông báo đẩy hoặc tự tạo phiếu.
- Menu Danh mục vẫn bị ẩn cho mọi vai trò. Cấu hình chu kỳ nằm trong cửa sổ riêng ở hồ sơ xe và chỉ hiện cho quản trị Fleet; áp dụng chung cho các xe cùng dòng.
- Không tự điền chu kỳ cho 18 dòng xe hay mốc ban đầu cho 6 xe demo. Nhóm nhập chính sách đã thống nhất; dữ liệu cũ được giữ nguyên.

## Phạm vi thay đổi

Chỉ mở rộng ba model Fleet hiện hữu: `fleet.vehicle.model` (chu kỳ/ngưỡng), `fleet.vehicle` (mốc/hạn/cảnh báo), `fleet.vehicle.log.services` (ODO hoàn tất và cờ chụp số đo). Không tạo bảng kế hoạch riêng, không sửa logic giá của Rental Core hoặc Finance.

Kiểm tra giao diện còn phát hiện cụm nút chuẩn Drivers History/Contracts/Services chưa bị ẩn hết. Đã ẩn toàn bộ cụm chuẩn, giữ các điểm neo kế thừa để account_fleet không lỗi; nút Bảo dưỡng & Sửa chữa riêng vẫn hiện.

## Kiểm chứng

- Trên bản sao database: bộ hồi quy Fleet/Core/Operations/Demo đạt **82/82**; sau bổ sung kiểm tra xóa phiếu và đổi chính sách, bộ định kỳ đạt **11/11**.
- Nâng cấp demo 8078: nhóm kiểm tra định kỳ + giao diện đạt **15/15**. Sau chỉnh cụm nút chuẩn, nhóm giao diện đạt **5/5**. Không cộng các lượt thành tổng số kiểm thử độc lập.
- Đối chiếu toàn bộ các cột cũ của 8 bảng nghiệp vụ trước/sau nâng cấp đều nguyên vẹn: 6 xe, 18 dòng, 3 phiếu bảo dưỡng, 3 lịch sử ODO, 3 hợp đồng/3 dòng, 2 phiếu vận hành/2 dòng. Xem `PERIODIC_MAINTENANCE_DATA_PRESERVATION.json`.
- Đã mở hồ sơ xe và cửa sổ cấu hình chu kỳ trên web 8078; tác vụ cập nhật hạn hằng ngày đã chạy thành công trong log.
- Không khẳng định tương thích Odoo 19; môi trường kiểm chứng là Odoo 18. Chưa push GitHub.

## Bản sao lưu và khôi phục

Thư mục local: `archive/before-periodic-maintenance-20261018-095606/`.

- `workspace.zip`: code hiện tại, gồm cả thay đổi chưa commit trước chức năng này.
- `running-dev.zip`: source dev thực sự đang chạy trước khi sửa.
- `database.dump`, `filestore/`, `test.conf`: database demo, tệp đính kèm và cấu hình cũ.
- Bản dump này đã được phục hồi thành database kiểm thử riêng trước khi chạy nâng cấp.

Muốn quay lại: dừng Odoo 8078; giải nén code cũ vào đúng workspace/source chạy; phục hồi dump và filestore vào **database mới**, cấu hình trỏ sang database mới rồi kiểm tra trước khi thay bản demo. Khôi phục code và database cùng nhau; không chỉ hạ code trên database đã nâng cấp. Giữ thư mục backup tại máy, không push cấu hình/database lên GitHub vì có thông tin đăng nhập.
