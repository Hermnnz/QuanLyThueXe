# Rà soát toàn bộ source Fleet ngày 16 tháng 10 năm 2026

Phạm vi: toàn bộ 24 file Python trong module/scripts, XML, ACL, manifest, migration, schema/DBML và tài liệu hiện hành của nhánh Fleet. Bản sau sửa: `19.0.5.3.0`. Giữ các thay đổi menu `19.0.5.2.0` đang có trước đợt rà soát. Các SQL/ZIP tuần 6 là snapshot lịch sử, không phải module đang được nạp.

## Vấn đề đã tái hiện và sửa

| Vấn đề | Ảnh hưởng | Sửa |
| --- | --- | --- |
| Chờ kiểm tra/bảo dưỡng vẫn cho technical_ready=True | Phép kiểm tra Fleet có thể chấp nhận điều kiện kỹ thuật mâu thuẫn trạng thái | Constraint từ chối tổ hợp này; nút xác nhận vẫn đưa về available/true |
| Sao chép phiếu giữ result cũ | Phiếu mới có thể hoàn tất bằng kết quả công việc của lần trước | result đặt copy=False; bản sao cần nhập kết quả mới |
| Lịch scheduled chặn thuê có bắt đầu bằng kết thúc | Khoảng thời gian 0 không có ý nghĩa chặn thuê, dễ làm sai kết quả giao nhau | Yêu cầu thời lượng dương khi lịch scheduled và blocks_rental=True, kể cả khi bật cờ chặn sau |
| Chi phí NaN/vô hạn | Native Monetary làm tròn trước constraint và phát sinh lỗi kỹ thuật | Kiểm tra amount/cost trước create/write và giá trị mặc định qua context; trả ValidationError rõ ràng |

Bốn kiểm thử tái hiện trước sửa: 3 failed, 1 error. Sau sửa: toàn bộ 38/38 đạt trên database thử và demo nâng cấp. Không suy diễn kết quả này thành bảo đảm không còn lỗi ngoài tình huống đã kiểm thử.

## Script và tính nhất quán

- prepare_demo_local.py và load_year_demo.py từng trỏ tới runner/config tạm tuần 6 đã không còn. Chuyển sang runner trong repo, config demo hiện hành, có --config và kiểm tra đúng tên database. Chạy shell với cwd là workspace; backup bộ năm nằm trong archive được Git bỏ qua.
- validate_local.py và validate_week7_local.py chuyển sang validator hiện hành có backup/đối chiếu dữ liệu. check_week6_web.py chuyển sang kiểm tra web hiện hành, thay cho giả định rented và cho phép đảo ngược trạng thái của tuần 6.
- Kiểm tra cú pháp toàn bộ Python/XML, đường dẫn data trong manifest và cấu trúc ACL đạt. Các entry point helper đã kiểm tra --help; không nạp lại bộ dữ liệu một năm trong đợt rà soát này.
- Export SQL dùng version đã cài trong database và đường dẫn output theo workspace. Exporter DBML tuần 6 giữ guard từ chối SQL hiện hành, tránh ghi đè tài liệu lịch sử.
- Menu mở thẳng Kanban mới; quy tắc nghiệp vụ và ACL hiện có giữ nguyên ngoài bốn sửa nêu trên. Quy ước Giang nhận trả về pending được ghi trong ví dụ bàn giao; API vẫn hỗ trợ các kết quả rõ ràng khác.
- Mô tả chung xe đã có sẵn ở fleet_vehicle.description. Chưa có snapshot ngoại quan/phụ kiện từng chuyến trong repo này.

## Bằng chứng

- Cài mới motorbike_fleet_source_audit_20261016: 38/38, exit 0.
- Nâng cấp motorbike_fleet_simple_20261002: 38/38, exit 0.
- Log trước/sau: source-audit-before.log, source-audit-after.log, motorbike_fleet_source_audit_20261016.log, upgrade.log trong thư mục cấu hình local đã nêu ở README.
- Đối chiếu toàn bộ dòng ba bảng xe/bảo dưỡng/ODO: FLEET_SOURCE_AUDIT_DATA_PRESERVATION.json; 39 xe, 300 phiếu, 0 log ODO gốc, không đổi nội dung dữ liệu.
- Backup trước nâng cấp: archive/before-fleet-integration-20261016-162158.

## Giới hạn tích hợp

Nhánh này và máy kiểm thử dùng Odoo 19. Nhánh dev của nhóm đã chuyển sang Odoo 18 và sửa thêm code; kết quả này không xác nhận tính tương thích Odoo 18 hoặc toàn bộ hệ thống đã gộp. Chưa có source Rental/Operations/Finance trong working tree hiện tại. Các kiểm tra hợp đồng trùng lịch, chống xác nhận lặp của Operations, pin, phụ kiện và tính phí phải được kiểm thử khi nối module. Readonly trên form không cấm mọi write ORM/RPC; các đường cập nhật đó vẫn chịu constraints hiện có.

Đợt này không tự commit hoặc push. Những thay đổi menu và sửa source chỉ ở máy local cho đến khi người dùng yêu cầu đẩy lên GitHub.
