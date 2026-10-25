# Báo cáo lỗi ảnh hưởng giao diện sau khi nạp Odoo — 22/10/2026

## Phạm vi

Báo cáo này **chỉ tính lỗi trong thao tác mà người dùng có thể thực hiện từ giao diện Odoo**. Một test gọi ORM/API bị lỗi nhưng thao tác đó không thuộc quy trình giao diện hiện hành, hoặc test vẫn theo nghiệp vụ cũ, **không được cộng vào số lỗi giao diện**. Một lỗi phát sinh ở backend vẫn được tính nếu nó chặn thao tác bình thường trên giao diện, ví dụ lưu hóa đơn.

Đã cập nhật bốn module đang cài trong database `QuanLyThueXe`: Rental Core, Fleet Management, Rental Operation và Rental Finance. Odoo khởi động lại thành công; trang đăng nhập `/web/login` trả HTTP 200. Mã nguồn tại commit `da5ad86` trên nhánh `dev`. Không sửa code nghiệp vụ trong lượt kiểm thử.

Các kịch bản nghiệp vụ dưới đây được chạy bằng Odoo ORM trên **database bản sao**, sử dụng chính các hàm mà giao diện Odoo gọi khi lưu và bấm nút. **Chưa tự động nhấp thử trên trình duyệt**; vì vậy kết quả xác nhận đường xử lý của thao tác giao diện, chưa xác nhận bố cục/hiển thị trực quan của form.

## Kết quả sau khi bỏ lỗi API-only và test cũ

| Mức | Số lỗi đã xác nhận | Ý nghĩa |
|---|---:|---|
| Chặn nghiệp vụ trên giao diện | **1** | Tạo hóa đơn sau khi thu hồi xe bị lỗi Fleet chặn; xem `UI-01`. |
| Lỗi giao diện khác đã xác nhận | **0** | Chưa tìm thấy lỗi thứ hai từ các kịch bản đã chạy. Điều này không có nghĩa toàn bộ giao diện đã được kiểm thử. |

Bộ test tự động báo **139 bài, 4 FAIL và 39 ERROR**, nhưng **không tính 43 kết quả này thành 43 lỗi giao diện**. Nhiều bài gọi ORM/API theo nghiệp vụ cũ: tự xác nhận từng phiếu tiền, tạo thêm phiếu tiền thuê, xóa hồ sơ bảo dưỡng, hoặc hủy hợp đồng sau khi bắt đầu giao xe. Một lỗi khởi tạo bộ test hóa đơn cũng có cùng nguyên nhân với `UI-01`, không phải lỗi thứ hai. Chi tiết cách loại trừ nằm ở cuối báo cáo.

## UI-01 — Đã thu hồi xe nhưng không tạo được hóa đơn

**Module cần xử lý:** `motorbike_fleet_management`. **Mức ưu tiên:** cao, vì chặn hoàn cọc/thu thêm và tự đóng hợp đồng.

### Cách tái hiện

1. Tạo hợp đồng thuê một xe: tiền thuê **600.000đ**, cọc **2.000.000đ**. Hệ thống tự tạo hai phiếu thu nháp.
2. Tích đã nhận đủ tiền, chọn phương thức tiền mặt, xác nhận hợp đồng. Hai phiếu chuyển sang đã xác nhận.
3. Tạo phiếu vận hành, giao xe; hợp đồng chuyển sang `in_progress`.
4. Thử lập hóa đơn trước khi thu hồi: Odoo chặn đúng vì xe chưa được thu hồi.
5. Xác nhận thu hồi xe. Phiếu vận hành `done`, hợp đồng vẫn `in_progress` để chờ hóa đơn — đúng quy trình.
6. Tạo hóa đơn thuê xe sau thu hồi: Odoo báo **“Không được xóa hồ sơ bảo dưỡng; hãy hủy hoặc lưu trữ nếu cần.”** Kịch bản này không có hồ sơ bảo dưỡng nào.

### Nguyên nhân đã xác định

`custom_addons/motorbike_fleet_management/models/fleet_service.py:173-175` ghi đè `unlink()` và luôn phát `UserError`, **kể cả khi `self` là tập rỗng**. Khi tạo/lưu hóa đơn, Odoo đồng bộ các dòng kế toán; phần `account_fleet` của Odoo gọi `vehicle_log_service_ids.unlink()`. Không có hồ sơ bảo dưỡng liên kết thì tập này rỗng, nhưng code Fleet vẫn báo lỗi. Trace trong log kiểm thử cũng cho thấy cùng đường đi khi Odoo chuẩn bị dữ liệu của bộ test hóa đơn.

Đây là lỗi **người dùng có thể gặp khi tạo hóa đơn trên giao diện**, dù vị trí phát lỗi nằm trong hàm Python của Fleet. Nó không phải lỗi chỉ có thể tạo ra bằng API. Thông báo “không được xóa hồ sơ” cũng khiến người dùng không hiểu vì sao thao tác lập hóa đơn thất bại.

### Kết quả đúng phải là gì

Sau khi tất cả xe được xác nhận thu hồi, người dùng tạo và xác nhận hóa đơn gồm tiền thuê cùng phụ phí đã duyệt, xác nhận khoản phải hoàn/thu thêm, hệ thống ghi phiếu tiền tương ứng rồi chuyển hợp đồng sang `done`. Quy tắc **không được xóa hồ sơ bảo dưỡng thật** vẫn phải giữ nguyên.

### Hướng xử lý và điều kiện nghiệm thu

- Trong Fleet `unlink()`, nếu không có bản ghi nào cần xóa thì cho thao tác rỗng kết thúc bình thường; nếu có hồ sơ thật thì tiếp tục chặn xóa.
- Kiểm thử lại ngay trên giao diện: hợp đồng đã thu hồi đủ xe phải tạo được hóa đơn; hợp đồng chưa thu hồi phải tiếp tục bị chặn.
- Xác nhận hóa đơn, kiểm tra phiếu hoàn cọc/thu thêm được ghi đúng và hợp đồng chuyển `done`. Thử thêm trường hợp thực sự có hồ sơ bảo dưỡng để chắc chắn lịch sử vẫn được giữ.
- Chạy lại bộ test hóa đơn sau khi sửa Fleet. Hiện bộ này chết ở `setUpClass`, nên chưa thể kết luận bước cuối kỳ còn lỗi nào khác hay không.

**Chưa áp dụng hướng sửa này.**

## Những bước nghiệp vụ đã qua trên đường xử lý của giao diện

| Thao tác | Kết quả quan sát trên database kiểm thử |
|---|---|
| Tạo hợp đồng nháp có cọc 2.000.000đ và tiền thuê 600.000đ | Có đúng một phiếu cọc nháp và một phiếu tiền thuê nháp. |
| Tích đã nhận đủ hai khoản, chọn phương thức, ký hợp đồng | Hợp đồng `confirmed`; hai phiếu đều `confirmed`. |
| Đã ký nhưng chưa giao: xác nhận hoàn cọc 2.000.000đ | Hợp đồng `cancelled`; phiếu hoàn `confirmed`; phiếu vận hành `contract_cancelled`. |
| Cố bắt đầu giao xe trên phiếu của hợp đồng đã hủy | Bị chặn. |
| Giao xe của một hợp đồng khác | Hợp đồng `in_progress`, xe `renting`. |
| Tạo hóa đơn khi xe chưa thu hồi | Bị chặn đúng theo nghiệp vụ. |
| Thu hồi xe | Xe `returned`, phiếu vận hành `done`, hợp đồng vẫn `in_progress`. |
| Tạo hóa đơn sau thu hồi | **Thất bại do `UI-01`**; chưa thử tiếp được xác nhận hóa đơn và đóng hợp đồng. |

Các bản ghi thử đã được `rollback`; không thêm hợp đồng hoặc phiếu tiền thử vào database đang dùng.

## Những kết quả **không** tính là lỗi giao diện

| Nhóm test | Số kết quả lỗi | Vì sao không cộng vào số lỗi giao diện |
|---|---:|---|
| Fleet | 6 ERROR | Test còn thử xóa hồ sơ bảo dưỡng hoặc sửa hồ sơ đã kết thúc, trong khi nghiệp vụ mới chủ ý cấm. Cần cập nhật test, không mở lại quyền xóa chỉ để test xanh. |
| Rental Core | 8 ERROR | Test gọi ký hợp đồng trực tiếp mà chưa tích đã nhận cọc và tiền thuê; màn hình hiện tại bắt buộc bước này. Chúng chưa chạy tới điều kiện Core định kiểm tra. |
| Rental Operation | 15 ERROR | 14 bài dùng fixture tự xác nhận phiếu tiền hoặc tạo thêm phiếu thuê theo luồng cũ; 1 bài gắn xe thứ hai với bảng giá khác model. Riêng bài hủy hợp đồng sau khi bắt đầu giao còn trái quy tắc hiện hành. |
| Rental Finance — thu tiền đầu vào | 4 FAIL + 9 ERROR | Kỳ vọng một phiếu cọc duy nhất, xác nhận từng phiếu, trả từng phần hoặc cọc 0đ; không khớp luồng hai phiếu tự sinh và ký trên hợp đồng. |
| Rental Finance — hóa đơn | 1 ERROR tại `setUpClass` | Bị cùng lỗi Fleet `UI-01` chặn lúc tạo dữ liệu kế toán thử. Đây là bằng chứng bổ sung cho một lỗi đã tính, không phải lỗi giao diện độc lập. |

**Lưu ý:** Loại khỏi *số lỗi giao diện hiện đã xác nhận* không có nghĩa bỏ vĩnh viễn việc sửa test. Sau khi fixture được cập nhật, các bài đó có thể bộc lộ lỗi giao diện hoặc logic mới; khi ấy phải đánh giá lại theo đường đi thực tế của người dùng.

Log cập nhật module cũng có cảnh báo `placeholder` của wizard, hai trường cùng nhãn “Cần sửa chữa?”, icon thiếu mô tả và template Kanban cũ. Chúng **chưa được xác minh bằng quan sát giao diện** và không chặn các kịch bản đã thử, nên chưa cộng vào số lỗi chức năng. Có thể xử lý sau khi khôi phục luồng hóa đơn.

## Giới hạn và tài liệu đối chiếu

- Đã cập nhật module trong database `QuanLyThueXe`, nhưng kiểm thử tự động và kịch bản tạo dữ liệu chạy trên bản sao `QuanLyThueXe_test_20261022`, sau đó bản sao được dọn.
- Chưa chạy kiểm thử nhấp chuột end-to-end bằng trình duyệt; chưa xác nhận bước hóa đơn cuối kỳ vì `UI-01` chặn việc tạo hóa đơn.
- Nhật ký đầy đủ: `C:\Users\ADMIN\AppData\Local\Temp\odoo_tests_20261022.log`.
- Bản sao lưu database trước cập nhật: `C:\Users\ADMIN\AppData\Local\Temp\QuanLyThueXe_before_update_20261022.dump`.
- Báo cáo này chỉ thay đổi tài liệu; chưa sửa code hoặc cập nhật lại test.
