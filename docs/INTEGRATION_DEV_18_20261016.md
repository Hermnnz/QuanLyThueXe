# Tích hợp Fleet – Rental Core – Operations với dev

## Phạm vi

Nhánh Fleet tích hợp toàn bộ `dev` tại `8d0365e`, giữ các sửa đổi Fleet đã push ở `5650b73`. Môi trường triển khai chung là **Odoo 18**, theo Dockerfile/docker-compose của dev. Không chuyển database Odoo 19 sang Odoo 18; database demo trên máy Bắc vẫn là database Odoo 19 riêng.

Phiên bản mới: Fleet `18.0.5.7.0`, Core `18.0.1.0.8`, Operations `18.0.1.1.0`. Finance giữ code từ dev.

## Các điểm đã nối

- Dòng hợp đồng dùng cùng `fleet.vehicle`; dòng giá phải khớp `fleet.vehicle.model` của xe.
- Xác nhận hợp đồng kiểm tra cả hợp đồng trùng lịch và `check_fleet_availability(start, end)`: xe điện, còn hoạt động, hãng/dòng hoạt động, đạt kỹ thuật, không khóa thuê và không vướng bảo dưỡng chặn thuê.
- Website đặt xe sử dụng cùng kiểm tra Fleet khi tính số xe còn trống; yêu cầu khách tạo hợp đồng nháp, chưa tự giữ chỗ.
- Khi bắt đầu vận chuyển, Operations gọi Fleet giao xe, giữ xe ở `renting`. Khi xác nhận bàn giao, không giao lại lần thứ hai. Có thể xác nhận bàn giao trực tiếp từ Chưa giao như UI cũ.
- Khi thu hồi, Operations gọi Fleet nhận trả với kết quả `pending`: xe về Chờ kiểm tra, chưa đạt kỹ thuật. Nếu có bảo dưỡng chặn đang chạy, Fleet tiếp tục giữ trạng thái Bảo dưỡng.
- Operations lưu `odo_start`, `odo_end`; Fleet cập nhật ODO hiện tại và tạo lịch sử ODO chuẩn trong cùng giao dịch. Mốc giao/nhận được ghi theo lúc thao tác. ODO không được âm hoặc giảm.
- Các nút và ghi trạng thái qua ORM dùng cùng luồng kiểm tra; chặn chuyển ngược, bấm lặp, đổi xe/phiếu sau khi bắt đầu giao và xóa lịch sử giao/nhận đã thực hiện.
- Tạo phiếu vận hành qua ORM tự lấy xe từ hợp đồng nếu chưa truyền dòng xe; onchange giao diện vẫn hoạt động.
- Rental User kế thừa Fleet Officer. Quy tắc quyền cho đội xe điện dùng chung cho phép nhân viên xử lý xe thuê, thay vì bị giới hạn bởi tài xế cá nhân như Fleet Odoo 18 chuẩn. Quy tắc đa công ty chuẩn vẫn có hiệu lực; không dùng sudo để bỏ qua quyền giao/nhận.
- Giao diện giữ các nút chuẩn trong cấu trúc kế thừa và ẩn chúng; không xóa điểm neo mà `account_fleet` cần. Giữ menu nghiệp vụ Phương tiện, Bảo dưỡng & Sửa chữa, Danh mục.

## Luồng trạng thái

Sẵn sàng → bắt đầu giao/xác nhận giao tại Operations → Đang thuê → xác nhận thu hồi → Chờ kiểm tra.

Chờ kiểm tra → xác nhận đạt kỹ thuật tại Fleet → Sẵn sàng.

Chờ kiểm tra → bắt đầu phiếu sửa chữa chặn thuê → Bảo dưỡng → hoàn thành/hủy phiếu chặn cuối cùng → Chờ kiểm tra → xác nhận đạt kỹ thuật → Sẵn sàng.

Phiếu bảo dưỡng mới/lên lịch không tự đổi trạng thái hiện tại của xe; khoảng thời gian đã lên lịch được dùng khi kiểm tra đặt xe.

## Cách nhóm gộp và cập nhật

Gộp **cả nhánh/merge commit**, không chỉ chép riêng thư mục Fleet: có thay đổi kết nối trong Core, Operations và quyền truy cập. Nếu dev có commit mới sau mốc trên, phải giải quyết và kiểm tra phần phát sinh trước khi gộp.

Sau khi sao lưu database/filestore của nhóm, dừng web và cập nhật đủ bốn module (thay `TEN_DATABASE` bằng tên thực tế):

```bash
docker compose stop web
docker compose build web
docker compose run --rm web odoo -d TEN_DATABASE -u motorbike_fleet_management,motorbike_rental_core,motorbike_rental_operation,motorbike_rental_finance --stop-after-init --no-http
docker compose up -d web
```

Máy cài mới: dùng `-i motorbike_rental_finance` để cài chuỗi phụ thuộc. Không chạy lệnh cài mới này để thay thế dữ liệu cũ.

Migration Fleet Odoo 18 giữ metadata, đổi khóa trạng thái cũ và cấp mã còn thiếu. Nếu dữ liệu cũ trùng biển số/mã sau chuẩn hóa, migration dừng và báo ID để nhóm xử lý; không tự xóa hoặc đoán biển số. Không tự đánh dấu tất cả xe cũ đạt kỹ thuật. ODO giao/nhận của chuyến cũ chưa có số đo cần nhân viên đối chiếu và nhập, không dựng lại số liệu lịch sử.

## Kết quả kiểm thử thực tế ngày 16/10/2026

- Odoo Community 18.0, đủ bốn module Fleet/Core/Operations/Finance được cài chung. Bộ kiểm thử Fleet, Core (bao gồm HTTP website) và Operations: **71/71 đạt, 0 failed, 0 errors**. Finance được kiểm chứng cài đặt và kế thừa cùng hệ thống, chưa có bộ kiểm thử đầy đủ nghiệp vụ tài chính.
- Kiểm thử tài khoản Rental User thực hiện xác nhận hợp đồng, giao và nhận xe thành công; kiểm thử Fleet Officer cũng đạt.
- Tạo database riêng từ code dev `8d0365e`, tạo xe có ODO 67, hợp đồng xác nhận, phiếu đang thuê và bảo dưỡng lên lịch; nâng cấp lên bản mới thành công. Các cột cũ của sáu bảng được đối chiếu nguyên vẹn (ngoại trừ mã xe còn thiếu được cấp); ODO 67 được giữ. Thử nhận trả phiếu cũ với ODO 90 thành công, về Chờ kiểm tra; thao tác thử được rollback. Xem `DEV18_UPGRADE_VERIFICATION.json`.
- Python/XML được kiểm tra cú pháp. Database demo Odoo 19 và server cổng 8072 không được nâng cấp trong đợt tích hợp này.
- Log kiểm thử trong `archive/fleet_team_test_20261016_01/test.log`; log nâng cấp trong `archive/fleet_team_test_upgrade_20261016/test.log`, không đưa database/config chứa thông tin đăng nhập lên GitHub.

## Giới hạn kiểm chứng

Kết quả thực chạy được ghi trong báo cáo kiểm thử kèm theo; không đồng nghĩa mọi chức năng Finance, mọi tình huống đồng thời hoặc dữ liệu riêng của nhóm đều đã được kiểm thử. Trước khi cập nhật database thật cần chạy nâng cấp trên bản sao dữ liệu của nhóm. Nhánh `dev` trên GitHub chưa bị thay đổi bởi việc chuẩn bị này.
