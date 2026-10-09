# Fleet & Maintenance — hoàn thành tuần 7

Odoo 19, module `motorbike_fleet_management`, phiên bản `19.0.4.0.0`.
Phạm vi: `ERP_Odoo (1).xlsx`, `Ke hoach Sprint!F17:I17`, điều chỉnh theo kiến trúc tối giản đã chốt.

## Chức năng

- Fleet → Xe máy điện: List/Form và Kanban nhóm theo available/rented/inspection/maintenance. Kanban hiển thị đủ bốn cột kể cả cột trống; không kéo thả trạng thái.
- Tìm xe theo mã/biển số/dòng xe; lọc trạng thái, khóa thuê, chưa đạt kỹ thuật, đến hạn bảo dưỡng, lưu trữ. Nhóm theo trạng thái/dòng xe.
- Fleet → Bảo dưỡng xe điện: List/Form/Search, tìm theo xe/mô tả/loại/trạng thái, lọc lịch dự kiến/chặn thuê/lưu trữ; nhóm theo xe/trạng thái/loại. Không làm Kanban bảo dưỡng.
- Chỉ hai model nghiệp vụ kế thừa: `fleet.vehicle`, `fleet.vehicle.log.services`. Hãng và dòng xe sử dụng danh mục Fleet chuẩn.
- Kiểm tra ODO trên model chuẩn `fleet.vehicle.odometer`: không âm, có ngày, không giảm theo ngày; hỗ trợ nhập bổ sung lịch sử nằm giữa hai mốc. Không thêm field/bảng/menu ODO custom.
- Không thêm pin asset, SOC/SOH, bảng pin hay battery_status.

## Luồng bảo dưỡng

`new → scheduled → running → done`, hoặc hủy từ new/scheduled/running. Có thể bắt đầu trực tiếp từ new. Done/cancelled không quay lại trạng thái trước.

1. Nhập lịch bắt đầu/kết thúc rồi **Lên lịch**. Lịch tương lai chưa đổi trạng thái hiện tại của xe.
2. **Bắt đầu**: tự điền actual_start nếu chưa nhập. Nếu blocks_rental=True, xe phải đang khai thác và không đang thuê; chuyển xe sang maintenance, technical_ready=False.
3. Nhập kết quả rồi **Hoàn tất**: tự điền actual_end nếu chưa nhập. Khi không còn bảo dưỡng chạy đang chặn, xe về inspection và vẫn chưa đạt kỹ thuật.
4. Trên hồ sơ xe, **Xác nhận đạt kỹ thuật**: kiểm tra không còn bảo dưỡng chạy chặn thuê, xe không đang thuê/đã lưu trữ; cập nhật technical_ready=True và available. Khóa thuê chủ động vẫn giữ nguyên.

Hủy bảo dưỡng đang chạy cũng yêu cầu kiểm tra kỹ thuật lại. Hủy lịch chưa bắt đầu không đổi xe. Bảo dưỡng không chặn thuê không đổi trạng thái/điều kiện kỹ thuật xe.

Khi chuyển running → done, next_service_date của hồ sơ hoàn thành gần nhất (theo date rồi id) cập nhật lên xe nếu có. Không xóa mốc xe khi hồ sơ chưa nhập mốc tiếp theo. Import/sửa ghi chú hồ sơ đã hoàn thành trong lịch sử không tự đổi tình trạng hiện tại hay mốc xe.

## Ràng buộc

- Xe available phải đạt kỹ thuật. Xe có bảo dưỡng chạy chặn thuê phải maintenance và technical_ready=False.
- Khóa thuê cần lý do; technical_ready và rental_blocked độc lập.
- Chi phí không âm; cho phép bảo dưỡng miễn phí (0).
- Kết thúc cần có bắt đầu và không trước bắt đầu; scheduled cần đủ lịch dự kiến; next_service_date phải sau date hồ sơ.
- Hoàn tất cần kết quả công việc. Kiểm tra state flow ở server, kể cả cập nhật qua RPC/import.
- Hồ sơ đang running không đổi xe, đổi blocks_rental, lưu trữ hay xóa; phải hoàn tất/hủy trước. Hồ sơ kết thúc không đổi xe.
- Quy tắc tùy chỉnh chỉ áp dụng xe điện; vẫn giữ ACL/công ty của Fleet chuẩn.

## Quyền

Fleet Officer: quản lý xe, đọc bảo dưỡng. Kỹ thuật viên xe điện: thêm/sửa bảo dưỡng, không xóa. Fleet Administrator: CRUD. Người ngoài nhóm Fleet không được cấp quyền. Các nút vẫn kiểm tra quyền server.

## Dừng trước tuần 8

Không có availability theo khoảng thời gian, kiểm tra trùng lịch thuê, API giao/trả, tích hợp Rental/Inspection, báo cáo tùy chỉnh hay Calendar/Gantt. Trạng thái rented vẫn do nhân viên nhập; chưa phải luồng giao/trả liên module.

DBML đã tạm bỏ company_id/vendor/service_type/technician và bảng partner/company vẫn giữ nguyên quyết định chờ giáo viên. Tuần 7 không thêm cột hay bảng nghiệp vụ; DBML/SQL tuần 6 vẫn mô tả cấu trúc dữ liệu đó.

## Chạy và kiểm thử tại máy hiện tại

```powershell
# Cài mới trên database kiểm thử riêng, không ghi đè database đã có.
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -X utf8 scripts/validate_week7_local.py

# Sao lưu rồi nâng cấp demo hiện tại, chạy kiểm thử và đối chiếu dữ liệu.
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -X utf8 scripts/validate_week7_local.py --upgrade

# Chạy demo sau nâng cấp.
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -X utf8 scripts/run_odoo_local.py -c "$env:LOCALAPPDATA/Temp/codex-fleet-week7-20261009/demo.conf"
```

Runtime cần Odoo tại `C:/odoo`, PostgreSQL cấu hình trong `C:/odoo/odoo.conf`. Script không đưa mật khẩu vào repo. Config/log/data mới ở `%LOCALAPPDATA%/Temp/codex-fleet-week7-20261009`. Khi database test đã tồn tại, chọn `--database <ten-moi>`.

Demo: http://localhost:8072, database `motorbike_fleet_simple_20261002`, tài khoản `admin` / `admin`. Dữ liệu giả lập một năm giữ nguyên, không nhập lại. Backup trước nâng cấp ở `archive/before-week7-*`, được Git bỏ qua.

Kết quả kiểm tra: `docs/VALIDATION.md`; đối chiếu dữ liệu: `docs/WEEK7_DATA_PRESERVATION.json`. Dữ liệu test trong TransactionCase được rollback.
