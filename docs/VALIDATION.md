# Rà soát cuối trước bàn giao

Ngày 12/10/2026, bản `19.0.5.1.0`. Kiểm tra code, SQL/DBML, trạng thái demo và các đường nhập trực tiếp bên cạnh workflow. Bổ sung kiểm tra số hữu hạn ở model `fleet.vehicle.odometer`: NaN/Infinity bị chặn cả khi tạo/sửa log trực tiếp, không chỉ qua API giao/trả. Test ODO chuẩn đã thêm các tình huống này.

Database cài mới riêng `motorbike_fleet_release_20261012` và lần chạy lại có bổ sung đều đạt 34/34; demo nâng cấp đạt 34/34, 0 failed, 0 errors. Log cuối: `release-final-audit.log`, `upgrade.log` tại `%LOCALAPPDATA%/Temp/codex-fleet-integration-20261012`. Fingerprint ba bảng trước/sau demo giữ nguyên: `FLEET_FINAL_AUDIT_DATA_PRESERVATION.json`. Backup: `archive/before-fleet-integration-20261012-162430`.

Kết luận chỉ áp dụng Fleet và các tình huống đã kiểm thử. Form có readonly nhưng ORM/RPC vẫn có thể cập nhật với constraints hiện có để các module tích hợp. Chưa kiểm thử xuyên module hoặc xác minh hình thức UI bằng click/screenshot. Không diễn đạt kết quả này thành bảo đảm hệ thống bốn module không thể có lỗi.

---

# Xác minh sửa theo Word nhóm trưởng

Phiên bản `19.0.5.1.0`, 12/10/2026. Đã bổ sung UNIQUE(vehicle_code) và đặt trạng thái/technical_ready chỉ đọc trên form; các luồng giao/trả, bảo dưỡng và xác nhận kỹ thuật vẫn hoạt động.

| Kiểm tra | Kết quả |
| --- | --- |
| Database thử riêng motorbike_fleet_word_fix_20261012 | 34/34 test, 0 failed, 0 errors |
| Nâng cấp demo motorbike_fleet_simple_20261002 | 34/34 test, 0 failed, 0 errors |
| Mã xe khi tạo/sửa và trùng với xe lưu trữ | UNIQUE ở PostgreSQL chặn đúng |
| Xe chưa cấp mã và copy xe | Cho phép nhiều NULL, bản sao không giữ mã cũ |
| Sửa tay trạng thái/kỹ thuật trên form | Odoo Form từ chối; nút và phương thức workflow vẫn chạy |
| RPC sau nâng cấp | Mã trùng bị từ chối; view có readonly; giao/trả/ODO/lịch bảo dưỡng đạt |
| Dữ liệu gốc | Giữ nguyên toàn bộ dòng của 39 xe, 300 bảo dưỡng, 0 ODO |
| SQL/DBML | SQL xuất từ demo có UNIQUE, thực thi schema tạm và rollback; DBML Week8 ghi unique đúng |

Đối chiếu: `FLEET_WORD_FIX_DATA_PRESERVATION.json`. Backup trước sửa: `archive/before-fleet-integration-20261012-161735` (Git bỏ qua). Log test riêng: `%LOCALAPPDATA%/Temp/codex-fleet-integration-20261012/word-fix-final.log`; log demo: `upgrade.log`, `server.log`.

Readonly là bảo vệ thao tác trên form. Module/ORM/RPC/import vẫn cập nhật với các validation hiện có; không tuyên bố đã cấm mọi cập nhật trạng thái trực tiếp ở server. Repo chưa có Rental/Operations/Finance, nên kiểm tra pin/đổi xe/đặt trùng xuyên module vẫn cần thành viên phụ trách nối. Dùng ODO chuẩn và trả xe theo kết quả kiểm tra như đã thống nhất, không khai báo đè field hay ghi available vô điều kiện theo đoạn mẫu Word.

Các phần bên dưới là lịch sử kiểm chứng các phiên bản trước.

---

# Xác minh Fleet tích hợp tuần 8 — 12/10/2026

Module `motorbike_fleet_management` `19.0.5.0.0`, Odoo 19.

| Kiểm tra | Kết quả |
| --- | --- |
| Cài mới `motorbike_fleet_integration_final_20261012` | 31/31 test, 0 failed, 0 errors |
| Nâng cấp `motorbike_fleet_simple_20261002` | 31/31 test, 0 failed, 0 errors |
| Giao xe và trả đạt/lỗi/chưa kết luận/cần bảo dưỡng | Đạt; kết quả kiểm tra bắt buộc, giữ khóa chủ động |
| Trả đạt nhưng còn bảo dưỡng đang chạy | Giữ maintenance/false |
| ODO chuẩn | Ghi lịch sử theo ngày, đọc giá trị mới ngay, 0 hợp lệ; chặn âm/giảm/NaN/Infinity |
| Lịch bảo dưỡng | Scheduled giao nhau chặn; biên liền nhau không chặn; running chưa xong không hứa ngày giải phóng |
| Điều kiện Fleet và phân quyền | Đạt; không thay cho kiểm tra hợp đồng trùng lịch của Rental |
| Hồi quy toàn bộ chức năng tuần 7 | 18 test trước đây tiếp tục đạt với khóa trạng thái thống nhất |
| RPC trên demo nâng cấp | Giao/trả, ODO, validation, lịch bảo dưỡng, bốn nhóm trạng thái và tải view đạt |
| Dữ liệu trước–sau | 39 xe, 300 bảo dưỡng, 0 ODO; chỉ đổi 8 rented và 6 inspection sang khóa mới |

Fingerprint toàn bộ dòng của ba bảng, sau chuẩn hóa riêng hai khóa trạng thái, bằng nhau; đồng thời số lượng từng trạng thái khớp phép đổi khóa, không còn khóa cũ. Bằng chứng: `FLEET_INTEGRATION_DATA_PRESERVATION.json`. Các test ORM rollback; RPC tạo/xóa bản ghi TEMP-W8 riêng, giữ số lượng dữ liệu gốc. Không seed lại bộ dữ liệu một năm.

Backup trước upgrade: `archive/before-fleet-integration-20261012-151415/database.dump` và filestore, Git bỏ qua. Log: `%LOCALAPPDATA%/Temp/codex-fleet-integration-20261012/motorbike_fleet_integration_final_20261012.log`, `upgrade.log`, `server.log`. Demo: http://localhost:8072, admin/admin.

Giới hạn: repo chỉ có Fleet; chưa kiểm thử xuyên Rental–Operations–Payment. Đã kiểm tra Form qua ORM, metadata/view loading qua RPC; chưa xác minh hình thức hiển thị bằng click/screenshot. Thông số ODO/pin của từng chuyến và chống xác nhận lặp thuộc Operations, chống đặt trùng hợp đồng và giao dịch đồng thời thuộc Rental.

Tài liệu tích hợp: `handoff/Fleet_Integration_Week8.md`. Các phần tuần 7/6 dưới đây là lịch sử kiểm chứng tại thời điểm đó.

---

# Xác minh tuần 7 — 09/10/2026

Module `motorbike_fleet_management` `19.0.4.0.0`, Odoo 19. Dừng ở `Ke hoach Sprint!F17:I17`, không triển khai tích hợp tuần 8. Không thêm cột/bảng nghiệp vụ; DBML tạm chờ giáo viên được giữ nguyên.

| Kiểm tra | Kết quả |
| --- | --- |
| Cài mới `motorbike_fleet_week7_final_20261009` | 18/18 test, 0 failed, 0 errors |
| Nâng cấp `motorbike_fleet_simple_20261002` | 18/18 test, 0 failed, 0 errors |
| Form CRUD xe/bảo dưỡng, cost alias | Đạt |
| Chi phí/thời gian/lịch dự kiến/mốc tiếp theo | Đạt validation |
| Điều kiện available, lý do khóa thuê, rented/archived | Đạt |
| Lên lịch → Bắt đầu → Hoàn tất/Hủy | Đạt; timestamps tự điền, giữ timestamps đã nhập |
| Nhiều hồ sơ chạy chặn thuê trên một xe | Chỉ trả về inspection khi hồ sơ cuối kết thúc |
| Không chặn thuê, hủy lịch chưa bắt đầu | Không đổi tình trạng xe |
| Xác nhận đạt kỹ thuật | Kiểm tra hồ sơ chạy, trạng thái thuê/lưu trữ; giữ khóa chủ động |
| Chuyển state trực tiếp qua write/RPC | Rule server có hiệu lực |
| Sửa lịch sử/cập nhật mốc từ hồ sơ cũ | Không ghi đè trạng thái/mốc hiện tại ngoài luồng quy định |
| ODO chuẩn | Chặn âm và giảm theo ngày, gồm ghi bổ sung ở giữa/sửa log |
| ACL/công ty chuẩn và phạm vi xe điện | Đạt |
| Search views, action List/Kanban/Form, bốn nhóm Kanban gồm nhóm trống | Đạt qua ORM và get_views/RPC |
| Web RPC admin | Luồng bảo dưỡng, validation, tìm kiếm, view loading đạt; bản ghi thử đã xóa |
| Dữ liệu toàn bộ xe/bảo dưỡng/ODO trước–sau nâng cấp | SHA256 bằng nhau; 39 xe, 300 bảo dưỡng, 0 ODO |

Kết quả fingerprint: `docs/WEEK7_DATA_PRESERVATION.json`. Dữ liệu test ORM rollback; RPC chỉ tạo/xóa bản ghi thử riêng, số lượng dữ liệu gốc giữ nguyên. Code tuần 6 sao lưu ở `archive/before-week7-code-735162a.zip`; database trước nâng cấp ở `archive/before-week7-20261009-140655/database.dump`.

Log hiện tại: `%LOCALAPPDATA%/Temp/codex-fleet-week7-20261009/motorbike_fleet_week7_final_20261009.log`, `upgrade.log`, `server.log`. Demo đang chạy tại http://localhost:8072, admin/admin. Runner/config mới mô tả trong README module.

Giới hạn kiểm tra UI: Computer Use dừng vì không xác định được URL Chrome đủ chắc chắn để thực thi policy. Không tiếp tục tự động hóa UI. Đã kiểm tra view hợp lệ khi cài/nâng cấp, Odoo Form, tải view bằng RPC và dữ liệu nhóm Kanban; chưa xác minh hình thức hiển thị bằng click/screenshot.

Không kiểm thử Rental/Inspection/availability, giao–trả liên module hoặc báo cáo, vì chưa triển khai trong tuần 7.

## Lịch sử kiểm tra tuần 6 — 02/10/2026

Module `motorbike_fleet_management`, Odoo 19, phiên bản `19.0.3.1.0`. Phạm vi nguồn: `ERP_Odoo (1).xlsx`, `Ke hoach Sprint!F13:I13` (Fleet của Bắc).

| Kiểm tra | Kết quả |
| --- | --- |
| Cài mới `motorbike_fleet_week6_crud_clean_20261002` | 6/6 test, 0 failed, 0 errors |
| Nâng cấp demo `motorbike_fleet_simple_20261002` | 6/6 test, 0 failed, 0 errors |
| Odoo Form xe: tạo/xem/sửa/xóa, sửa trực tiếp trạng thái/kỹ thuật | Đạt |
| Odoo Form bảo dưỡng: tạo/xem/sửa/xóa, sửa trạng thái/thời gian/chi phí/kết quả | Đạt |
| Sửa hồ sơ bảo dưỡng không tự cập nhật xe hoặc ngày bảo dưỡng | Đạt |
| ACL cơ bản và quy tắc công ty chuẩn | Đạt |
| Action chỉ List/Form, không Search view hoặc API/workflow custom cũ | Đạt |
| Web CRUD đăng nhập admin qua RPC | Đạt; bản ghi tạm đã xóa |
| Schema SQL hai bảng trong schema tạm | DDL thực thi thành công; cột/kiểu/nullability trùng; rollback schema tạm |
| Dữ liệu trước/sau nâng cấp | Fingerprint toàn bộ 39 dòng xe và 300 dòng bảo dưỡng giống nhau |

Các test chạy trong transaction kiểm thử; bản ghi thử trên web cũng được xóa sau khi xác minh. Không thay đổi bộ dữ liệu đã tạo một năm. So sánh dữ liệu đọc được trong `docs/WEEK6_DATA_PRESERVATION.json`.

Logs:
- `%TEMP%/codex-fleet-simple-20261002/week6_clean.log`.
- `%TEMP%/codex-fleet-simple-20261002/week6_upgrade.log`.
- `%TEMP%/codex-fleet-simple-20261002/server.log`.

Demo: http://localhost:8072, admin/admin. Đã khởi động lại tiến trình để sử dụng code mới. Script web kiểm tra: `scripts/check_week6_web.py`.

Bản sao trước điều chỉnh: `archive/before-week6-scope-20261002/code.zip`, `database.dump`, filestore và `data-fingerprint.json`.

Tại mốc tuần 6 chưa triển khai/kiểm thử tích hợp Rental, Inspection, availability, đồng bộ giao–trả, workflow, validation tuần 7, Kanban hoặc report custom. Mục lịch sử này không mô tả bản tuần 7 hiện hành.
