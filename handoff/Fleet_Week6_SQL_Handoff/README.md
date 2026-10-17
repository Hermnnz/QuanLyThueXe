# Bàn giao SQL Fleet và Maintenance tuần 5–6

Ngày đối chiếu: 02/10/2026. Odoo 19, module `motorbike_fleet_management` phiên bản `19.0.2.0.0`, commit `b8ae865`, nhánh `module/fleet-maintenance` của https://github.com/Hermnnz/QuanLyThueXe.

## Mục đích và cách gộp

`Fleet_Maintenance_Week6_Current.sql` là bản chụp cấu trúc PostgreSQL đang triển khai, gồm CREATE TABLE, primary key, unique, foreign key và index của 6 bảng. Không có dữ liệu khách hàng, dữ liệu demo, mật khẩu hoặc cấu hình máy.

Dùng file để đối chiếu và gộp thiết kế database/ERD của nhóm. Ba bảng `fleet_*` chứa cả cột Odoo chuẩn và cột mở rộng của Fleet; không tạo lại các bảng này nếu bản tổng hợp của nhóm đã có. Chọn một định nghĩa chung, sau đó bổ sung cột và quan hệ còn thiếu. Đây không phải script ALTER nâng cấp database đang chạy và không được chạy trực tiếp đè lên database Odoo.

Để gộp ứng dụng thực tế, lấy module Python/XML từ nhánh Fleet, giữ dependency `fleet`, rồi cài/nâng cấp bằng Odoo. SQL không tạo metadata model/field của Odoo, ACL, menu, view, dữ liệu loại dịch vụ hoặc logic nghiệp vụ. Gộp SQL đơn thuần không thay thế gộp module.

## Sáu bảng bàn giao

| Model Odoo | Bảng PostgreSQL | Vai trò |
| --- | --- | --- |
| fleet.vehicle | fleet_vehicle | Hồ sơ xe, mở rộng bảng chuẩn |
| fleet.vehicle.odometer | fleet_vehicle_odometer | Lịch sử ODO, mở rộng bảng chuẩn |
| fleet.vehicle.log.services | fleet_vehicle_log_services | Bảo dưỡng/sửa chữa, mở rộng bảng chuẩn |
| motorbike.battery | motorbike_battery | Hồ sơ pin riêng |
| motorbike.battery.assignment | motorbike_battery_assignment | Lịch sử pin gắn vào xe |
| motorbike.maintenance.plan | motorbike_maintenance_plan | Kế hoạch bảo dưỡng |

File chỉ bao gồm sáu bảng này; không phải bản dump toàn bộ ứng dụng Fleet/Odoo hoặc các bảng quan hệ phụ của Odoo chuẩn.

## Các bảng dùng chung cần có trước

Các FK ngoài phạm vi sáu bảng tham chiếu tới:

- `res_users(id)`: người tạo/sửa và người quản lý xe.
- `res_partner(id)`: tài xế, kỹ thuật viên, garage/vendor.
- `res_company(id)`: công ty theo Odoo chuẩn.
- `fleet_vehicle_model(id)`, `fleet_vehicle_model_brand(id)`, `fleet_vehicle_model_category(id)`.
- `fleet_vehicle_state(id)`: trạng thái chuẩn Odoo, khác operational_status của đề tài.
- `fleet_service_type(id)`: loại dịch vụ chuẩn.

Nhóm dùng Odoo nên tái sử dụng các bảng trên, không tạo bản sao khách hàng, nhân viên hay danh mục trong Fleet. `technician_id` hiện là FK tới `res_partner`, chưa phải `hr_employee`.

## Các cột riêng do module bổ sung vào bảng chuẩn

`fleet_vehicle`:
- Tuần 6: vehicle_code, lifecycle_status, operational_status, technical_ready, rental_blocked, block_reason, current_battery_id, min_rental_soc, next_service_date, next_service_odo.
- Tuần 5 giữ lại: is_electric_motorbike, battery_serial, battery_capacity_kwh, battery_voltage, battery_health, charging_time_hours, battery_warranty_until.
- Những cột pin cũ còn tồn tại để bảo toàn dữ liệu khi nâng cấp. Thông số pin hiện tại phải đọc từ `motorbike_battery`; không dùng cột pin cũ làm nguồn chính.

`fleet_vehicle_odometer`: source_type, service_id, note.

`fleet_vehicle_log_services`: maintenance_component, technician_id, maintenance_result, next_maintenance_date, maintenance_type, scheduled_start, scheduled_end, actual_start, actual_end, blocks_rental. Trường `state` là cột chuẩn, được bổ sung giá trị `scheduled`.

## Trường ORM không phải cột riêng

| Trường | Cách triển khai |
| --- | --- |
| fleet.vehicle.current_soc / current_soh | Related không lưu; lấy từ pin hiện tại |
| fleet.vehicle.battery_assignment_ids | One2many; FK nằm ở battery_assignment.vehicle_id |
| fleet.vehicle.maintenance_plan_ids | One2many; FK nằm ở maintenance_plan.vehicle_id |
| motorbike.battery.assignment_ids | One2many; FK nằm ở battery_assignment.battery_id |
| motorbike.battery.current_vehicle_id | Compute không lưu; tìm lần gắn chưa tháo |
| fleet.vehicle.log.services.cost | Alias ghi được của amount, không có cột cost riêng |
| fleet.vehicle.log.services.result | Alias ghi được của maintenance_result |
| fleet.vehicle.log.services.is_electric_motorbike | Related không lưu từ xe |

`fleet_vehicle.current_battery_id` là compute có `store=True`, nên có cột và FK thực. Odoo cập nhật từ lịch sử gắn pin, không có SQL trigger trong file. Ghi trực tiếp SQL vào lịch sử sẽ không tự chạy compute.

## Giá trị Selection hiện tại và default ORM

| Trường | Giá trị hợp lệ trong code | Default Odoo |
| --- | --- | --- |
| lifecycle_status | active, suspended, retired | active |
| operational_status | available, rented, inspection, maintenance | inspection |
| motorbike_battery.status | available, installed, charging, maintenance, retired | available |
| source_type | manual, delivery, return, maintenance | manual |
| maintenance_type | preventive, corrective, emergency, battery | preventive |
| maintenance_component | general, battery, motor, brakes, tires, charger | general |
| fleet_vehicle_log_services.state | new, scheduled, running, done, cancelled | new |

Các default khác: min_rental_soc = 70; technical_ready = false; battery.soh = 100; blocks_rental = true; active của pin/kế hoạch = true; installed_at = thời điểm tạo. Đây là default ở Python/Odoo, không phải SQL DEFAULT trong database. Default sequence cho id được biểu diễn bằng `serial` trong file để PostgreSQL tạo sequence tương ứng.

Tên nghiệp vụ Draft và In Progress tương ứng key Odoo `new` và `running`; không đổi thành `draft`/`in_progress` khi tích hợp nếu chưa sửa code đồng bộ.

## Ràng buộc thực tế

Có ở PostgreSQL và đã xuất:
- PK, NOT NULL theo schema thực tế và FK đúng hành vi ON DELETE.
- Unique mã pin; unique serial nếu có (PostgreSQL vẫn cho nhiều NULL).
- Unique index có điều kiện cho battery_id và vehicle_id khi removed_at IS NULL: mỗi pin/mỗi xe chỉ có một lần gắn chưa tháo.

Có trong Python/Odoo, không phải SQL CHECK/trigger:
- SOC/SOH trong 0–100, thông số pin và chu kỳ không âm.
- SOC tối thiểu trong 0–100, ODO mốc bảo dưỡng không âm.
- Thời điểm tháo không trước thời điểm gắn; kiểm tra ODO gắn/tháo và trùng khoảng lịch sử gắn pin.
- Thời gian kết thúc bảo dưỡng không trước bắt đầu; ngày bảo dưỡng tiếp theo không trước ngày thực hiện.
- Các chu kỳ, ODO và ngưỡng cảnh báo kế hoạch không âm.

Không tự thêm CHECK, ENUM hoặc trigger vào bản tổng hợp rồi coi đó là logic đã triển khai. Nếu cần tăng cường ràng buộc SQL, thống nhất và cập nhật module cùng các thành viên trước.

## Liên kết với thành viên khác

Điểm liên kết đã tồn tại là `fleet_vehicle.id`. Các module khác nên Many2one tới `fleet.vehicle` thay vì tạo bảng xe mới.

Các quan hệ sau mới là hướng tích hợp theo tài liệu V2, CHƯA có trong phần tuần 6:
- Rental Order Line → fleet.vehicle: chờ thống nhất model, field và các trạng thái khóa lịch với Rental Core.
- Inspection → fleet.vehicle và cập nhật ODO/SOC: chờ Operations.
- inspection_id, incident_id trên hồ sơ bảo dưỡng; inspection_id trên ODO: chưa tạo vì model Operations chưa được tích hợp.
- Availability và kiểm tra trùng lịch Rental/Maintenance: chưa triển khai; không có bảng vehicle_availability.

Không cần tạo các bảng V1 đã loại bỏ: vehicle_hold, vehicle_transfer, vehicle_document, maintenance_schedule hoặc maintenance_cost_line.

## Xác minh file

Đã thực thi DDL trong một schema kiểm tra tạm trên PostgreSQL, tạo đủ sáu bảng cùng constraints/indexes, đối chiếu toàn bộ tên cột, kiểu dữ liệu và nullability với database hiện tại; sau đó rollback toàn bộ schema kiểm tra. Các bảng dùng chung được tham chiếu từ Odoo có sẵn. Không thay đổi dữ liệu vận hành.
