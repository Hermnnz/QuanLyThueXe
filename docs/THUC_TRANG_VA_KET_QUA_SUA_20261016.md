# Fleet–Maintenance: thực trạng và kết quả sửa

Ngày 16/10/2026. Bản local `19.0.5.5.0`, Odoo 19, nhánh `module/fleet-maintenance`. Đã cập nhật source và database demo trên máy; chưa commit/push GitHub.

## 1. Thực trạng trước sửa

Module đã có hồ sơ xe, hãng/dòng xe, bốn trạng thái vận hành, bảo dưỡng, ODO và API giao/trả. Tuy nhiên, các kiểm thử cũ chưa đủ để kết luận nghiệp vụ hoàn chỉnh. Một số trường có trong database nhưng thiếu thao tác rõ ràng; một số quy tắc chỉ bảo vệ trên giao diện hoặc khi chuyển trạng thái, có thể vượt qua bằng cách cập nhật khác.

## 2. Vấn đề đã giải quyết

| Vấn đề trước sửa | Kết quả hiện tại |
| --- | --- |
| Xe mới thiếu mã, phải nhập tay | Cấp mã tự động dạng XE00001, XE00002… nếu không nhập. Bỏ qua mã đã được dùng; sao chép xe cấp mã mới. Không được xóa mã đã cấp |
| Trùng mã qua chữ hoa/thường/khoảng trắng | Có khóa định danh chuẩn hóa và UNIQUE ở PostgreSQL; giữ nguyên mã cũ, mã nhập mới được chuẩn hóa |
| Hai xe có thể cùng biển số | UNIQUE theo biển số đã chuẩn hóa: bỏ dấu phân cách/khoảng trắng và không phân biệt hoa thường. Bảo vệ cả create/write và xe lưu trữ; cho phép nhiều xe chưa có biển số theo phạm vi docs |
| Sao chép xe mang theo biển số cũ | Không sao chép biển số; người dùng nhập biển số của chiếc mới |
| active của hãng/dòng xe khó tìm hoặc thiếu trên form | Có ô Đang sử dụng trên form hãng, dòng xe, xe và phiếu bảo dưỡng; lưu trữ/khôi phục chuẩn Odoo vẫn dùng được theo quyền. Phiếu đang chạy không được ngừng sử dụng |
| Hãng mới không có dòng xe bị ẩn | Bỏ bộ lọc With Models mặc định; không giấu hãng mới vì chưa có dòng xe |
| Bỏ tick Xe máy điện làm xe biến khỏi danh sách và lộ form chuẩn | Danh sách Phương tiện không còn lọc cứng xe điện; dùng cùng bố cục tinh gọn. Checkbox vẫn nằm trong Thông tin phương tiện |
| Bỏ tick Xe máy điện để thoát kiểm soát bảo dưỡng | Chặn đổi từ xe điện khi đang thuê hoặc đã có hồ sơ bảo dưỡng, kể cả hồ sơ lưu trữ; giữ liên kết và quy tắc lịch sử |
| ODO đầu kỳ chỉ đọc | Cho nhập ODO khi xe chưa ở Đang thuê/Bảo dưỡng. Các trạng thái đó chỉ đọc trên form; Operations/API vẫn cập nhật được. Kiểm tra số hữu hạn, không âm; write chuẩn Odoo chặn giảm |
| Lưu trữ/xóa xe đang thuê | Bị chặn; phải xử lý nhận trả trước. Xe đang bảo dưỡng không được xóa; xe có lịch sử bảo dưỡng phải ngừng sử dụng thay vì xóa |
| Ghi thẳng xe về Sẵn sàng | Write/import/RPC trực tiếp bị chặn khi chuyển từ trạng thái khác về available. Dùng xác nhận đạt kỹ thuật hoặc API nhận trả có kết quả rõ ràng; không dựa riêng vào readonly UI |
| Phiếu hoàn tất vẫn xóa/sửa được kết quả, chi phí, ngày và nội dung | Khóa các trường nghiệp vụ của phiếu done/cancelled tại server; các ô chính cũng readonly trên form. Vẫn cho bổ sung notes để ghi chú mà không sửa kết quả đã chốt |
| Tạo thẳng phiếu done thiếu nội dung | Nhập lịch sử hoàn tất chỉ cho Fleet Administrator, phải có kết quả và đủ thời gian thực tế; các kiểm tra thời gian/chi phí vẫn áp dụng |
| Xóa phiếu done làm mốc bảo dưỡng trên xe bị cũ | Nếu phiếu bị xóa là nguồn của mốc hiện tại, tính lại từ hồ sơ hoàn tất còn lại, gồm hồ sơ lưu trữ. Không ghi đè một mốc đã được người dùng chỉnh sang giá trị khác |
| Hãng/dòng xe ngừng sử dụng nhưng vẫn được chọn để tạo/giao xe | Chặn chọn danh mục đã ngừng sử dụng qua create/write; API kiểm tra Fleet trả inactive_catalog và từ chối giao. Không tự xóa hoặc đổi trạng thái các xe đã có |

Các yêu cầu thêm ở đợt này (tự sinh mã, chống trùng biển số, siết dữ liệu) thực hiện theo yêu cầu trực tiếp “sửa tất cả” của người dùng; không coi là các quy tắc được Word ghi đầy đủ từ trước.

## 3. Dữ liệu đã xử lý theo xác nhận của người dùng

- Giữ biển số DEMO-EV-101 tại xe ID 48; bỏ giá trị biển số bị trùng tại ID 49.
- Giữ biển số DEMO-EV-103 tại xe ID 50; bỏ giá trị biển số bị trùng tại ID 278.
- Cấp mã XE00001 cho ID 276, XE00002 cho ID 278 vì trước đó chưa có mã. Giữ các mã đã có.
- ID 49 và 278 đang chờ người dùng nhập lại biển số đúng. Không xóa hồ sơ xe hoặc hợp nhất các bản ghi.
- Giữ 42 xe, 300 phiếu bảo dưỡng, 0 log ODO có sẵn; ODO hiện tại và trạng thái gốc được giữ nguyên.
- Backup gốc trước sửa dữ liệu: archive/before-fleet-integration-20261016-183552/database.dump, kèm filestore nếu có.
- Việc bổ sung cột khóa chuẩn hóa ban đầu khiến Odoo ghi lại write_uid/write_date. Đã đối chiếu từng cột rồi khôi phục đúng metadata gốc từ backup; migration cuối có bước bảo toàn metadata. Chỉ còn các thay đổi dữ liệu đã nêu và tên hiển thị được tính lại theo biển số trống.

## 4. Kiểm tra thực hiện

- Database cài mới riêng: lượt đầu 53 trường hợp, sau sửa tình huống test cũ đạt 53/53; thêm kiểm thử chống ghi thẳng Sẵn sàng thành tổng 54.
- Database demo sau bản sửa cuối: 54/54 đạt, 0 failed, 0 errors.
- Database thử khôi phục từ backup bản cũ rồi nâng cấp: 54/54 đạt.
- So toàn bộ cột của ba bảng xe/bảo dưỡng/ODO trên bản nâng cấp thử với backup: chỉ khác đúng dữ liệu đã được cho phép; metadata gốc giữ nguyên.
- Web RPC: giao, trả, ODO, khoảng bảo dưỡng, UNIQUE mã xe, trạng thái và readonly đạt; số bản ghi sau kiểm tra giữ nguyên.
- UI thực tế: form ID 276 hiển thị XE00001, checkbox Xe máy điện/Đang sử dụng và ô ODO nhập được; form hãng Toyota mẫu có Đang sử dụng.
- Schema SQL đã xuất lại và kiểm tra trong transaction. Bộ kiểm thử bổ sung: test_business_hardening.py (11 trường hợp) và các kiểm thử hiển thị theo Word.

Bằng chứng: FLEET_BUSINESS_HARDENING_DATA_PRESERVATION.json, FLEET_HARDENING_FINAL_DATA_PRESERVATION.json, FLEET_HARDENING_CLONE_PRESERVATION.json. Log: upgrade.log, hardening-retest.log và hardening-clone-final.log trong thư mục cấu hình local codex-fleet-integration-20261012.

## 5. Giới hạn và việc còn cần phối hợp

- Đây là module bảo dưỡng/sửa chữa, chưa có phân hệ bảo hành riêng (thời hạn, yêu cầu bảo hành, đơn vị chịu phí). Word chưa giao nghiệp vụ đó; không tự tạo thêm phân hệ.
- Chưa xác nhận toàn bộ dự án đã gộp chạy trên Odoo 18 của nhánh dev. Repo local đang dùng Odoo 19 và chỉ chứa module Fleet.
- Operations phải dùng API Fleet, đặc biệt không write trực tiếp về available. Quy ước nhận trả về pending_inspection giữ theo người dùng; nhận trả passed chỉ dùng khi đã có kết quả kiểm tra đạt.
- Fleet không kiểm tra hợp đồng trùng lịch, tiền cọc, thanh toán, pin/phụ kiện theo chuyến hoặc tính bồi thường; các module thành viên khác thực hiện và cần kiểm thử tích hợp.
- Không tự cấm mọi lịch bảo dưỡng trùng nhau hoặc bắt buộc chờ đúng ngày mới bắt đầu: nhiều công việc cùng xe/làm sớm có thể hợp lệ, docs chưa quy định cấm.
- Không tự tạo phiếu/nhắc việc/khóa xe chỉ vì đến ngày bảo dưỡng; đây chưa là yêu cầu được triển khai.
- Mặc định Chờ kiểm tra, nút xác nhận kỹ thuật, khóa kéo Kanban là các lựa chọn triển khai đã được công khai, không phải yêu cầu nguyên văn trong Word.

Kết quả này xác nhận những tình huống đã kiểm tra, không phải bảo đảm tuyệt đối không còn lỗi hoặc toàn bộ hệ thống nhóm đã thông nhau.
