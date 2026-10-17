# Bàn giao Fleet–Maintenance cho tích hợp tuần 8

Module `motorbike_fleet_management`, Odoo 19, phiên bản `19.0.5.6.0`.

## Phần Fleet đã sửa

- Bố trí menu: Quản lý đội xe mở Kanban Phương tiện; Phương tiện và Bảo dưỡng & Sửa chữa ở menu chính. Các menu chuẩn ngoài phạm vi đã ẩn; danh mục chỉ có hãng và dòng xe. Thay đổi chỉ điều hướng/giao diện, không đổi chữ ký phương thức hoặc workflow tích hợp.

- Mã xe đã cấp là duy nhất trên toàn bộ xe, gồm xe lưu trữ, được bảo vệ bằng UNIQUE trong database. Xe thiếu mã được cấp tự động bằng sequence XE00001; sao chép cấp mã mới và không sao chép biển số.
- Trạng thái và technical_ready chỉ đọc trên form; thay đổi bằng workflow. ORM/RPC/import của module vẫn áp dụng các validation hiện có, không bị cấm toàn bộ write.

- Thống nhất trạng thái xe: `available`, `renting`, `pending_inspection`, `maintenance`; cập nhật bộ lọc, Kanban và script dữ liệu mẫu.
- Cung cấp kiểm tra điều kiện Fleet theo khoảng thời gian và hai phương thức giao/trả xe. Các phương thức kiểm tra quyền truy cập server.
- Giao xe chuyển sang `renting`; trả xe phải truyền kết quả kiểm tra rõ ràng. Không tự coi việc nhận xe là kiểm tra đạt.
- Theo Word bổ sung: `odometer` là Float lưu trực tiếp trên xe, nhận cập nhật từ Operations. Ghi lịch sử chuẩn theo ngày giao/trả, cập nhật giá trị hiện tại ngay trong giao dịch; chặn âm, giảm, giá trị không hữu hạn. Giá trị 0 hợp lệ; bỏ trống dùng `None`.
- Giữ toàn bộ workflow bảo dưỡng tuần 7. Bảo dưỡng hoàn tất vẫn cần xác nhận đạt kỹ thuật; khóa thuê chủ động không bị xóa.
- Nâng cấp đổi khóa trạng thái cũ `rented → renting`, `inspection → pending_inspection`, có backup và đối chiếu dữ liệu. Không tạo lại bộ dữ liệu một năm.

## Giao diện để các thành viên gọi

Các ví dụ sau là ORM bên trong cùng giao dịch Odoo. Người xác nhận giao/trả cần quyền Fleet Officer (hoặc nhóm tích hợp được cấp quyền tương đương); người chỉ có nhóm Operations/Rental chưa mặc nhiên có quyền Fleet. Cấu hình quyền ở module gọi và kiểm thử bằng tài khoản thật, không bỏ qua ACL bằng sudo. Module gọi khai báo dependency `motorbike_fleet_management`; Fleet không phụ thuộc ngược Rental/Operations.

```python
vehicle = self.env['fleet.vehicle'].browse(vehicle_id)

# Rental: điều kiện Fleet, chưa phải kết luận cuối cùng về đặt thuê.
result = vehicle.check_fleet_availability(start_datetime, end_datetime)[0]
if not result['fleet_ok']:
    raise UserError(', '.join(result['reasons']))
# Sau đó Rental kiểm tra hợp đồng trùng lịch, điều kiện khách/thanh toán...

# Operations: sau khi hợp đồng và điều kiện giao đã hợp lệ.
vehicle.action_deliver_vehicle(
    rental_start=start_datetime, rental_end=end_datetime,
    odometer_start=odo_start, checkout_at=checkout_datetime)

# Operations: theo phân công hiện tại, nhận trả về chờ Fleet kiểm tra.
vehicle.action_return_vehicle(
    inspection_result='pending',
    odometer_end=odo_end, checkin_at=checkin_datetime)
```

`check_fleet_availability` nhận một hoặc nhiều xe, trả danh sách `{vehicle_id, fleet_ok, reasons}`. Mã lý do: `not_electric_motorbike`, `archived`, `not_technical_ready`, `rental_blocked`, `blocking_maintenance`, `inactive_catalog`.

Datetime theo UTC của Odoo, khoảng `[start, end)`: kết thúc đúng lúc lịch khác bắt đầu không tính trùng. Bảo dưỡng `scheduled`, đang hoạt động và `blocks_rental=True` chặn khi giao nhau; bảo dưỡng `running` chưa hoàn tất không có thời điểm giải phóng bảo đảm dù đã nhập ngày kết thúc dự kiến. Hồ sơ mới/hủy/hoàn tất/lưu trữ hoặc không chặn thuê không chặn lịch.

Trạng thái `renting` hiện tại không tự loại xe khỏi mọi lịch tương lai. Rental phải kiểm tra khoảng thời gian hợp đồng của xe. Điều kiện kỹ thuật/khóa thuê hiện tại vẫn được áp dụng; xe chưa đạt kỹ thuật không được hứa sẵn sàng vào tương lai chỉ dựa trên ngày dự kiến.

Giao xe yêu cầu trạng thái hiện tại `available`, xe hoạt động, đạt kỹ thuật, không khóa thuê và không trùng lịch bảo dưỡng chặn. Operations kiểm tra thêm thời điểm giao thực tế đúng hợp đồng.

| Kết quả trả xe | Trạng thái xe | technical_ready |
| --- | --- | --- |
| `passed` — kiểm tra đạt | `available` | true |
| `failed` — chưa đạt | `pending_inspection` | false |
| `pending` — chưa kết luận | `pending_inspection` | false |
| `maintenance` — cần sửa chữa | `maintenance` | false |

Còn bảo dưỡng đang chạy chặn thuê thì giữ `maintenance/false` kể cả khi truyền `passed`. Mọi trường hợp giữ `rental_blocked` và `block_reason`. `maintenance` ở kết quả trả chỉ đánh dấu xe cần sửa; nhân viên tạo hồ sơ công việc bảo dưỡng theo thực tế, phương thức không tự tạo hồ sơ thiếu nội dung.

## Phần cần thành viên khác nối

- Operations: kiểm tra pin lúc giao/trả theo ngưỡng nhóm chốt. Khi xe chưa đủ điều kiện khai thác sau trả, gửi `pending`/`failed` thay vì `passed`; phí pin thấp được Finance xử lý riêng. Fleet không tự suy luận pin từ ODO.
- Operations: khi đổi xe, trả/đánh giá xe cũ và giao xe mới qua phương thức Fleet, đồng thời cập nhật hợp đồng/phiếu trong cùng transaction; đổi riêng vehicle_id không cập nhật trạng thái hai xe.
- Operations: Many2one xe/hợp đồng; snapshot ODO/pin đầu–cuối, kết quả kiểm tra và ghi chú trên dòng giao/trả. Kiểm tra ODO cuối ≥ ODO đầu của chính chuyến. Dùng `None` khi không có số đo, không dùng 0 thay cho thiếu dữ liệu.
- Operations: xác thực dòng thuộc chuyến đang diễn ra, chỉ xác nhận một lần; gọi Fleet và cập nhật dòng trong cùng transaction. Không gọi bằng `sudo()` để bỏ qua quyền. Trả xe chấp nhận `renting` hoặc `maintenance` để xử lý xe có sự cố trong chuyến; vì vậy việc ngăn nhận trả lặp phải có trên dòng Operations.
- Rental: dùng `fleet.vehicle.model` cho dòng xe, `fleet.vehicle` cho xe cụ thể; Datetime cho lịch thuê; kiểm tra hợp đồng trùng lịch và trạng thái hợp đồng có hiệu lực. Kiểm tra lại khi xác nhận/giao, đồng thời bảo vệ khỏi hai yêu cầu đặt cùng xe chạy song song bằng cơ chế khóa giao dịch phù hợp.
- Payment/Charge: liên kết hợp đồng/phiếu/sự cố do thành viên phụ trách thực hiện. Fleet không thay đổi nghiệp vụ tài chính.

Repo này chỉ có module Fleet. Chưa thể xác nhận luồng xuyên Rental–Operations–Payment chạy hoàn chỉnh trước khi các module đó gọi những phương thức trên. Không thêm model Rental/Inspection giả vào Fleet.

## ERD và dữ liệu

DBML hiện hành: `handoff/fleet_minimal/Fleet_Week8.dbml`. Hai bảng lõi và hai danh mục hãng/dòng xe; vẫn tạm ẩn company/vendor/service type/technician theo quyết định chờ giáo viên. Các field chuẩn đó vẫn tồn tại trong Odoo. Không thêm pin asset, kế hoạch bảo dưỡng, kho phụ tùng hay bảng availability.

ODO là field tính toán chuẩn; không thêm cột `odometer` vào bảng SQL `fleet_vehicle`. Lịch sử nằm trong `fleet.vehicle.odometer` chuẩn, không phát triển thành phân hệ custom riêng. Khi nhóm cần ERD tích hợp, các dòng giao/trả sở hữu snapshot ODO/pin, không thêm các snapshot đó vào hồ sơ xe.

Hướng dẫn chạy/nâng cấp: README module. Bằng chứng kiểm thử: `docs/VALIDATION.md`; đối chiếu dữ liệu: `docs/FLEET_INTEGRATION_DATA_PRESERVATION.json` cho lần đổi trạng thái và `docs/FLEET_WORD_FIX_DATA_PRESERVATION.json` cho lần thêm UNIQUE/readonly. Backup chứa dữ liệu và cấu hình máy không đưa lên GitHub.

Bản 19.0.5.6.0 chặn các trạng thái chờ kiểm tra/bảo dưỡng đi cùng technical_ready=True, kiểm tra chi phí hữu hạn trước làm tròn, yêu cầu lịch chặn thuê có thời lượng dương và xóa kết quả công việc khi sao chép phiếu. Không thay chữ ký API; nhóm hiện dùng pending khi nhận trả, các kết quả khác vẫn được API hỗ trợ khi có kết luận tương ứng.
