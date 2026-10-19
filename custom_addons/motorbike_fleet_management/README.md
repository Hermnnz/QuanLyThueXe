> Hiện tại: Fleet `18.0.5.9.0`, menu **Quản lý xe**, chu kỳ và ngưỡng cảnh báo cấu hình riêng trên từng xe. Không kế thừa từ dòng xe. Code cũ được giữ trong `legacy/model_policy_18_0_5_8_0`. Xem [hướng dẫn mới](../../docs/PER_VEHICLE_MAINTENANCE_20261018.md).

> Mới ngày 18/10: Fleet `18.0.5.8.0` bổ sung chu kỳ bảo dưỡng ngày/ODO và cảnh báo. Xem [hướng dẫn sử dụng và khôi phục](../../docs/PERIODIC_MAINTENANCE_20261018.md).

> Bản tích hợp hiện hành dùng Odoo 18 theo dev: Fleet `18.0.5.7.0`. Xem [hướng dẫn tích hợp](../../docs/INTEGRATION_DEV_18_20261016.md). Các ghi chú Odoo 19 bên dưới mô tả bản demo cũ, không phải môi trường triển khai chung.

# Fleet & Maintenance — tích hợp giao/trả tuần 8

## Tổ chức file giao diện

Các khai báo XML được nạp theo thứ tự trong `__manifest__.py`:

| File trong `views/` | Nội dung |
| --- | --- |
| `fleet_vehicle_views.xml` | Form, danh sách, tìm kiếm và Kanban phương tiện |
| `fleet_catalog_views.xml` | Giao diện hãng và dòng xe |
| `fleet_service_views.xml` | Form, danh sách và tìm kiếm bảo dưỡng |
| `fleet_actions.xml` | Action mở màn hình và thứ tự các chế độ xem |
| `fleet_menu.xml` | Menu nghiệp vụ và điều chỉnh menu Fleet chuẩn |

Đợt tách file giữ nguyên XML ID và nội dung khai báo; không đổi nghiệp vụ, quyền hoặc phiên bản module. File gộp `fleet_views.xml` đã được thay bằng năm file trên. Các báo cáo cũ dẫn tới file gộp là bằng chứng lịch sử.

Odoo 19, module `motorbike_fleet_management`, phiên bản `19.0.5.6.0`.
Giữ chức năng tuần 7, bổ sung phần Fleet theo giải pháp tích hợp tuần 8 của nhóm trưởng. Hợp đồng và dòng giao/trả thuộc module của các thành viên khác.

## Chức năng

Ứng dụng **Đội xe cho thuê** mở trực tiếp Kanban Xe máy điện. Hai mục Xe máy điện và Bảo dưỡng xe điện nằm ngay trên thanh menu chính. Các mục Fleet gốc gom dưới **Quản lý chuẩn Odoo**, trong đó danh sách xe gốc có tên **Xe (quản lý chuẩn)**. Màn hình gốc dùng state_id của Odoo, màn hình cho thuê dùng operational_status; không dùng trạng thái mua/đăng ký xe để suy ra xe thuê được hay không.

- Fleet → Xe máy điện: List/Form và Kanban nhóm theo available/renting/pending_inspection/maintenance. Kanban hiển thị đủ bốn cột kể cả cột trống; không kéo thả trạng thái.
- Tìm xe theo mã/biển số/dòng xe; lọc trạng thái, khóa thuê, chưa đạt kỹ thuật, đến hạn bảo dưỡng, lưu trữ. Nhóm theo trạng thái/dòng xe.
- Fleet → Bảo dưỡng xe điện: List/Form/Search, tìm theo xe/mô tả/loại/trạng thái, lọc lịch dự kiến/chặn thuê/lưu trữ; nhóm theo xe/trạng thái/loại. Không làm Kanban bảo dưỡng.
- Chỉ hai model nghiệp vụ kế thừa: `fleet.vehicle`, `fleet.vehicle.log.services`. Hãng và dòng xe sử dụng danh mục Fleet chuẩn.
- Kiểm tra ODO trên model chuẩn `fleet.vehicle.odometer`: số hữu hạn, không âm, có ngày, không giảm theo ngày; hỗ trợ nhập bổ sung lịch sử nằm giữa hai mốc. ODO hiện tại lưu trực tiếp theo Word bổ sung; không tạo bảng/menu ODO riêng.
- Không thêm pin asset, SOC/SOH, bảng pin hay battery_status.

## Luồng bảo dưỡng

`new → scheduled → running → done`, hoặc hủy từ new/scheduled/running. Có thể bắt đầu trực tiếp từ new. Done/cancelled không quay lại trạng thái trước.

1. Nhập lịch bắt đầu/kết thúc rồi **Lên lịch**. Lịch tương lai chưa đổi trạng thái hiện tại của xe.
2. **Bắt đầu**: tự điền actual_start nếu chưa nhập. Nếu blocks_rental=True, xe phải đang khai thác và không đang thuê; chuyển xe sang maintenance, technical_ready=False.
3. Nhập kết quả rồi **Hoàn tất**: tự điền actual_end nếu chưa nhập. Khi không còn bảo dưỡng chạy đang chặn, xe về pending_inspection và vẫn chưa đạt kỹ thuật.
4. Trên hồ sơ xe, **Xác nhận đạt kỹ thuật**: kiểm tra không còn bảo dưỡng chạy chặn thuê, xe không đang thuê/đã lưu trữ; cập nhật technical_ready=True và available. Khóa thuê chủ động vẫn giữ nguyên.

Hủy bảo dưỡng đang chạy cũng yêu cầu kiểm tra kỹ thuật lại. Hủy lịch chưa bắt đầu không đổi xe. Bảo dưỡng không chặn thuê không đổi trạng thái/điều kiện kỹ thuật xe.

Khi chuyển running → done, next_service_date của hồ sơ hoàn thành gần nhất (theo date rồi id) cập nhật lên xe nếu có. Không xóa mốc xe khi hồ sơ chưa nhập mốc tiếp theo. Import/sửa ghi chú hồ sơ đã hoàn thành trong lịch sử không tự đổi tình trạng hiện tại hay mốc xe.

## Ràng buộc

- Xe chờ kiểm tra/bảo dưỡng phải technical_ready=False.
- Phiếu sao chép không giữ kết quả công việc cũ; phải nhập kết quả mới khi hoàn tất.
- Lịch đã lên có chặn thuê cần kết thúc sau bắt đầu (không nhận thời lượng 0).

- Mã xe đã cấp phải duy nhất, kể cả xe lưu trữ; ràng buộc UNIQUE ở PostgreSQL. Cho phép nhiều xe chưa cấp mã (NULL); copy xe không sao chép mã.
- Trạng thái và điều kiện kỹ thuật chỉ đọc trên form. Nhân viên dùng workflow giao/trả/bảo dưỡng và nút xác nhận kỹ thuật. Các module vẫn được cập nhật qua ORM với validation hiện có; đây không phải cơ chế cấm mọi write từ RPC/import.

- Xe available phải đạt kỹ thuật. Xe có bảo dưỡng chạy chặn thuê phải maintenance và technical_ready=False.
- Khóa thuê cần lý do; technical_ready và rental_blocked độc lập.
- Chi phí là số hữu hạn, không âm; giá trị nhập sai được từ chối trước bước làm tròn tiền tệ; cho phép bảo dưỡng miễn phí (0).
- Kết thúc cần có bắt đầu và không trước bắt đầu; scheduled cần đủ lịch dự kiến; next_service_date phải sau date hồ sơ.
- Hoàn tất cần kết quả công việc. Kiểm tra state flow ở server, kể cả cập nhật qua RPC/import.
- Hồ sơ đang running không đổi xe, đổi blocks_rental, lưu trữ hay xóa; phải hoàn tất/hủy trước. Hồ sơ kết thúc không đổi xe.
- Quy tắc tùy chỉnh chỉ áp dụng xe điện; vẫn giữ ACL/công ty của Fleet chuẩn.

## Quyền

Ứng dụng Quản lý đội xe có các menu Phương tiện, Bảo dưỡng & Sửa chữa và Danh mục cần thiết (hãng/dòng xe). Ẩn nhánh quản lý xe chuẩn, báo cáo Fleet chuẩn, thiết lập Fleet chung, loại hoạt động và cấu hình trạng thái/tag chuẩn. Chỉ ẩn menu, không xóa dữ liệu hay thay đổi quyền model; ODO hiện tại lưu trên xe theo Word bổ sung; lịch sử chuẩn được giữ.

Form xe điện có bố cục thuê xe riêng: thanh operational_status chỉ đọc, nhận diện xe, điều kiện khai thác, ODO và mô tả tình trạng. Khối tài xế/cấp xe nhân viên, hợp đồng Fleet, thuế, thông số ô tô/xe đạp và thanh state_id chuẩn không hiển thị cho xe điện. Nút lịch sử bảo dưỡng mở action của module với đúng xe. Xe ngoài phạm vi điện vẫn dùng form chuẩn. Danh mục dòng xe dùng tên, hãng và vehicle_type theo Word; không thay đổi dữ liệu gốc.

Fleet Officer: quản lý xe, đọc bảo dưỡng. Kỹ thuật viên xe điện: thêm/sửa bảo dưỡng, không xóa. Fleet Administrator: CRUD. Người ngoài nhóm Fleet không được cấp quyền. Các nút vẫn kiểm tra quyền server.

## Tích hợp giao/trả và kiểm tra lịch

Fleet cung cấp `check_fleet_availability(start, end)`, `action_deliver_vehicle(...)` và `action_return_vehicle(...)`. Giao xe chuyển `renting`; trả xe cần kết quả kiểm tra bắt buộc: đạt → available, lỗi/chưa kết luận → pending_inspection, cần sửa → maintenance. Khóa thuê chủ động và bảo dưỡng đang chạy vẫn được bảo vệ.

Theo Word bổ sung, fleet.vehicle.odometer là Float lưu trực tiếp; Operations có thể write số hiện tại. API Fleet đồng thời lưu log chuẩn để giữ lịch sử. Không thêm pin asset, bảng hợp đồng, dòng giao/trả hoặc snapshot pin vào Fleet. Rental vẫn phải kiểm tra hợp đồng trùng lịch; Operations lưu số đo đầu–cuối và ngăn xác nhận trùng.

Chữ ký phương thức, ví dụ gọi, quy tắc UTC và trách nhiệm thành viên: `handoff/Fleet_Integration_Week8.md`. DBML hiện hành: `handoff/fleet_minimal/Fleet_Week8.dbml`, tiếp tục tạm bỏ các trường chờ giáo viên chốt trong sơ đồ nghiệp vụ.

## Chạy và kiểm thử tại máy hiện tại

```powershell
# Cài mới trên database kiểm thử riêng, không ghi đè database đã có.
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -X utf8 scripts/validate_fleet_integration_local.py

# Sao lưu rồi nâng cấp demo hiện tại, chạy kiểm thử và đối chiếu dữ liệu.
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -X utf8 scripts/validate_fleet_integration_local.py --upgrade

# Chạy demo sau nâng cấp.
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -X utf8 scripts/run_odoo_local.py -c "$env:LOCALAPPDATA/Temp/codex-fleet-integration-20261012/demo.conf"
```

Runtime cần Odoo tại `C:/odoo`, PostgreSQL cấu hình trong `C:/odoo/odoo.conf`. Script không đưa mật khẩu vào repo. Config/log/data mới ở `%LOCALAPPDATA%/Temp/codex-fleet-integration-20261012`. Khi database test đã tồn tại, chọn `--database <ten-moi>`.

Demo: http://localhost:8072, database `motorbike_fleet_simple_20261002`, tài khoản `admin` / `admin`. Dữ liệu giả lập một năm giữ nguyên nội dung; chỉ đổi khóa trạng thái rented/inspection sang renting/pending_inspection khi upgrade. Không nhập lại dữ liệu mẫu. Backup trước nâng cấp ở `archive/before-fleet-integration-*`, được Git bỏ qua.

Kiểm tra sửa theo Word: `docs/FLEET_WORD_FIX_DATA_PRESERVATION.json`. Kết quả kiểm tra: `docs/VALIDATION.md`; đối chiếu dữ liệu: `docs/FLEET_INTEGRATION_DATA_PRESERVATION.json`. Dữ liệu test trong TransactionCase được rollback.

Các entry point validate_local.py/validate_week7_local.py/check_week6_web.py nay chuyển sang kiểm tra bản hiện tại, không thực thi quy tắc CRUD lịch sử. prepare_demo_local.py/load_year_demo.py dùng runner trong repo và --config hiện hành; không phụ thuộc file tạm tuần 6. Ghi chú chung của xe có sẵn trong fleet_vehicle.description (tab Note); chưa có snapshot ngoại quan/phụ kiện trên Operations.

## Sửa nghiệp vụ ngày 16/10/2026

Bản 19.0.5.6.0: tự sinh mã, chống trùng biển số/mã đã chuẩn hóa, active rõ trên form, nhập ODO đầu kỳ, chặn bỏ phân loại để né kiểm soát, bảo vệ trạng thái và kết quả bảo dưỡng. Chi tiết hiện trạng/kết quả/giới hạn: docs/THUC_TRANG_VA_KET_QUA_SUA_20261016.md. Bộ cuối: 54/54 trên demo và bản sao backup nâng cấp, web RPC đạt. Không coi đây là bảo đảm tích hợp Odoo 18 hoặc toàn bộ hệ thống nhóm.
