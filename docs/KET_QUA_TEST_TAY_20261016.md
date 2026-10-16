# Sổ kết quả kiểm thử bằng tay

Đọc [kịch bản và đáp án](KICH_BAN_TEST_TAY_TOAN_HE_THONG_20261016.md) trước khi ghi. Mọi dòng hiện là NOT_RUN. Codex chưa kiểm thử ứng dụng.

## Môi trường

- URL: http://localhost:8072/
- Database: …
- Odoo: …
- Phiên bản/bản source đem nộp của từng module: …
- Có Đội xe / Hợp đồng / Vận hành / Tài chính: …
- Người thử / vai trò / thời gian bắt đầu và kết thúc: …
- Múi giờ / tiền tệ: …
- Ngày D và các mã dữ liệu TEST: …
- Backup đã được xác nhận / người giữ / cách phục hồi: …

## Quyết định tài liệu

Chép câu trả lời nhóm trưởng, người trả lời, ngày giờ và đường dẫn ảnh/tin nhắn. Xem nội dung Q trong bộ kịch bản.

| Mã | Quyết định | Người/ngày/bằng chứng |
| --- | --- | --- |
| Q1 | CHƯA CHỐT | |
| Q2 | CHƯA CHỐT | |
| Q3 | CHƯA CHỐT | |
| Q4 | CHƯA CHỐT | |
| Q5 | CHƯA CHỐT | |
| Q6 | CHƯA CHỐT | |
| Q7 | CHƯA CHỐT | |
| Q8 | CHƯA CHỐT | |

## Kết quả từng ca

Trạng thái cho phép: NOT_RUN, PASS, FAIL, BLOCKED, PARTIAL, N/A. Có nhiều biến thể thì thêm dòng `.a/.b/.c`; chỉ đánh ca gốc PASS khi mọi biến thể đạt. Ghi tiền thực tế, trạng thái xe, mã chứng từ; không chỉ ghi “OK”.

| Mã | Ưu tiên | Tên ca | Kết quả | Thực tế / bản ghi / biến thể | Bằng chứng / người / giờ |
| --- | --- | --- | --- | --- | --- |
| ENV-01 | P0 | Mở đúng địa chỉ | NOT_RUN | | |
| ENV-02 | P0 | Xác định module có thể kiểm | NOT_RUN | | |
| ENV-03 | P0 | Chốt bản đem nộp | NOT_RUN | | |
| ENV-04 | P0 | Bảo vệ dữ liệu trước test | NOT_RUN | | |
| ENV-05 | P0 | Chuẩn bị người dùng theo vai trò | NOT_RUN | | |
| ENV-06 | P0 | Chốt các điểm mâu thuẫn tài liệu | NOT_RUN | | |
| ENV-07 | P1 | Múi giờ và tiền tệ | NOT_RUN | | |
| ENV-08 | P0 | Kiểm tra lại sau đóng/mở trình duyệt | NOT_RUN | | |
| REF-01 | P0 | Tạo hãng và dòng xe dùng chung | NOT_RUN | | |
| REF-02 | P0 | Loại xe thuê liên kết mẫu Fleet | NOT_RUN | | |
| REF-03 | P1 | Cập nhật tên mẫu dùng chung | NOT_RUN | | |
| REF-04 | P1 | Lưu trữ hãng/dòng đang tham chiếu | NOT_RUN | | |
| REF-05 | P0 | Tạo khách thuê | NOT_RUN | | |
| REF-06 | P0 | Dùng chung khách giữa các phân hệ | NOT_RUN | | |
| REF-07 | P1 | Tài liệu khách hàng | NOT_RUN | | |
| REF-08 | P1 | Thiếu dữ liệu bắt buộc khách/tài liệu | NOT_RUN | | |
| REF-09 | P0 | Danh mục giá tiền | NOT_RUN | | |
| REF-10 | P1 | Không phá lịch sử khi sửa danh mục | NOT_RUN | | |
| FLT-01 | P0 | Tạo xe mới | NOT_RUN | | |
| FLT-02 | P0 | Mã xe trùng đang hoạt động | NOT_RUN | | |
| FLT-03 | P0 | Mã xe trùng xe lưu trữ | NOT_RUN | | |
| FLT-04 | P1 | Sao chép hồ sơ xe | NOT_RUN | | |
| FLT-05 | P1 | Sửa hồ sơ và mô tả chung | NOT_RUN | | |
| FLT-06 | P0 | Xác nhận đạt kỹ thuật | NOT_RUN | | |
| FLT-07 | P0 | Không xác nhận khi đang thuê | NOT_RUN | | |
| FLT-08 | P0 | Không xác nhận khi đang sửa chặn thuê | NOT_RUN | | |
| FLT-09 | P0 | Khóa thuê phải có lý do | NOT_RUN | | |
| FLT-10 | P0 | Khóa thuê khác kỹ thuật | NOT_RUN | | |
| FLT-11 | P0 | Xác nhận kỹ thuật không xóa khóa | NOT_RUN | | |
| FLT-12 | P0 | Mở khóa chủ động | NOT_RUN | | |
| FLT-13 | P1 | Lưu trữ và khôi phục xe | NOT_RUN | | |
| FLT-14 | P0 | Không khai thác xe lưu trữ | NOT_RUN | | |
| FLT-15 | P0 | Trạng thái không sửa bằng kéo thả | NOT_RUN | | |
| FLT-16 | P1 | Xem bảo dưỡng đúng xe | NOT_RUN | | |
| ODO-01 | P0 | Ghi ODO lúc giao | NOT_RUN | | |
| ODO-02 | P0 | Ghi ODO lúc trả | NOT_RUN | | |
| ODO-03 | P0 | Chặn ODO giao thấp hơn xe | NOT_RUN | | |
| ODO-04 | P0 | Chặn ODO trả thấp hơn đầu chuyến | NOT_RUN | | |
| ODO-05 | P0 | Chặn ODO trả thấp hơn ODO hiện tại | NOT_RUN | | |
| ODO-06 | P1 | ODO đầu bằng cuối | NOT_RUN | | |
| ODO-07 | P0 | ODO âm | NOT_RUN | | |
| ODO-08 | P1 | ODO bằng 0 khác thiếu số đo | NOT_RUN | | |
| ODO-09 | P1 | ODO thập phân | NOT_RUN | | |
| ODO-10 | P1 | Giữ snapshot đầu cuối | NOT_RUN | | |
| ODO-11 | P1 | Lịch sử ODO giảm theo ngày | NOT_RUN | | |
| ODO-12 | P1 | ODO và trạng thái không cập nhật nửa chừng | NOT_RUN | | |
| MNT-01 | P0 | Lập phiếu đầy đủ | NOT_RUN | | |
| MNT-02 | P1 | Ba loại bảo dưỡng | NOT_RUN | | |
| MNT-03 | P0 | Lên lịch hợp lệ | NOT_RUN | | |
| MNT-04 | P0 | Thiếu giờ khi lên lịch | NOT_RUN | | |
| MNT-05 | P0 | Kết thúc dự kiến trước bắt đầu | NOT_RUN | | |
| MNT-06 | P0 | Lịch chặn thuê thời lượng 0 | NOT_RUN | | |
| MNT-07 | P0 | Bắt đầu từ phiếu Mới | NOT_RUN | | |
| MNT-08 | P0 | Bắt đầu phiếu đã lên lịch | NOT_RUN | | |
| MNT-09 | P0 | Không sửa chặn thuê khi xe đang thuê | NOT_RUN | | |
| MNT-10 | P0 | Phiếu không chặn thuê | NOT_RUN | | |
| MNT-11 | P0 | Hoàn tất thiếu kết quả | NOT_RUN | | |
| MNT-12 | P0 | Hoàn tất phiếu chặn cuối cùng | NOT_RUN | | |
| MNT-13 | P0 | Hai phiếu chặn cùng xe | NOT_RUN | | |
| MNT-14 | P0 | Hủy phiếu đang chạy | NOT_RUN | | |
| MNT-15 | P1 | Hủy phiếu mới hoặc lịch tương lai | NOT_RUN | | |
| MNT-16 | P0 | Không chuyển ngược phiếu kết thúc | NOT_RUN | | |
| MNT-17 | P0 | Khóa sửa cấu trúc phiếu running | NOT_RUN | | |
| MNT-18 | P1 | Không đổi xe phiếu đã kết thúc | NOT_RUN | | |
| MNT-19 | P0 | Chi phí âm và miễn phí | NOT_RUN | | |
| MNT-20 | P1 | Thời gian thực tế sai | NOT_RUN | | |
| MNT-21 | P1 | Mốc tiếp theo phải sau ngày phiếu | NOT_RUN | | |
| MNT-22 | P1 | Cập nhật mốc xe từ phiếu mới nhất | NOT_RUN | | |
| MNT-23 | P1 | Sao chép phiếu bảo dưỡng | NOT_RUN | | |
| MNT-24 | P1 | Không bắt đầu phiếu hoặc xe lưu trữ | NOT_RUN | | |
| MNT-25 | P1 | Đến hạn chưa tự động chặn xe | NOT_RUN | | |
| MNT-26 | P1 | Sửa ghi chú lịch sử không đổi hiện tại | NOT_RUN | | |
| AVL-01 | P0 | Xe đủ điều kiện | NOT_RUN | | |
| AVL-02 | P0 | Xe chưa đạt kỹ thuật | NOT_RUN | | |
| AVL-03 | P0 | Xe bị khóa chủ động | NOT_RUN | | |
| AVL-04 | P0 | Lịch bảo dưỡng trùng một phần đầu | NOT_RUN | | |
| AVL-05 | P0 | Lịch bảo dưỡng trùng một phần cuối | NOT_RUN | | |
| AVL-06 | P0 | Thuê bao trùm bảo dưỡng | NOT_RUN | | |
| AVL-07 | P0 | Bảo dưỡng bao trùm thuê | NOT_RUN | | |
| AVL-08 | P0 | Khoảng trùng hoàn toàn | NOT_RUN | | |
| AVL-09 | P1 | Tiếp giáp đầu lịch bảo dưỡng | NOT_RUN | | |
| AVL-10 | P1 | Tiếp giáp cuối lịch bảo dưỡng | NOT_RUN | | |
| AVL-11 | P0 | Running quá giờ dự kiến vẫn chặn | NOT_RUN | | |
| AVL-12 | P1 | Không chặn bởi nháp/hủy/hoàn tất | NOT_RUN | | |
| AVL-13 | P1 | Không chặn bởi phiếu không chặn thuê | NOT_RUN | | |
| AVL-14 | P0 | Khoảng thuê rỗng hoặc đảo | NOT_RUN | | |
| AVL-15 | P0 | Kiểm tra lại sau khi xe đổi điều kiện | NOT_RUN | | |
| AVL-16 | P1 | Đang thuê không cấm mọi lịch tương lai | NOT_RUN | | |
| CON-01 | P0 | Hợp đồng đầy đủ | NOT_RUN | | |
| CON-02 | P0 | Giờ không bị mất khi lưu | NOT_RUN | | |
| CON-03 | P0 | Giá thuê chụp tại lúc chọn | NOT_RUN | | |
| CON-04 | P0 | Tiền thuê mẫu hai ngày | NOT_RUN | | |
| CON-05 | P0 | Không lặp cùng xe trong một hợp đồng | NOT_RUN | | |
| CON-06 | P0 | Không giữ chỗ hai hợp đồng trùng | NOT_RUN | | |
| CON-07 | P0 | Hai hợp đồng trùng một phần | NOT_RUN | | |
| CON-08 | P0 | Hai hợp đồng bao trùm hoặc bằng nhau | NOT_RUN | | |
| CON-09 | P1 | Hai hợp đồng tiếp giáp | NOT_RUN | | |
| CON-10 | P0 | Nháp và hủy có giữ chỗ không | NOT_RUN | | |
| CON-11 | P0 | Không sửa xe/giờ để né trùng | NOT_RUN | | |
| CON-12 | P1 | Ràng buộc ngày thuê tối thiểu/tối đa | NOT_RUN | | |
| CON-13 | P1 | Hợp đồng nhiều xe | NOT_RUN | | |
| CON-14 | P0 | Dữ liệu bắt buộc hợp đồng | NOT_RUN | | |
| CON-15 | P1 | Mã hợp đồng và tiền cọc | NOT_RUN | | |
| CON-16 | P0 | Đổi xe cập nhật hợp đồng | NOT_RUN | | |
| CON-17 | P1 | Xem hợp đồng lịch sử | NOT_RUN | | |
| CON-18 | P0 | Hủy hợp đồng đã thu tiền | NOT_RUN | | |
| OPS-01 | P0 | Phiếu vận hành liên kết hợp đồng | NOT_RUN | | |
| OPS-02 | P0 | Giao xe thông thường | NOT_RUN | | |
| OPS-03 | P0 | Giao xe thiếu điều kiện tiền | NOT_RUN | | |
| OPS-04 | P0 | Không giao khi xe không sẵn sàng | NOT_RUN | | |
| OPS-05 | P0 | Xác nhận giao lặp | NOT_RUN | | |
| OPS-06 | P0 | Chưa giao không được nhận trả | NOT_RUN | | |
| OPS-07 | P0 | Nhận trả thông thường | NOT_RUN | | |
| OPS-08 | P0 | Nhận trả chưa kiểm tra | NOT_RUN | | |
| OPS-09 | P0 | Trả xe có lỗi | NOT_RUN | | |
| OPS-10 | P0 | Trả xe cần sửa | NOT_RUN | | |
| OPS-11 | P0 | Nhận trả lặp | NOT_RUN | | |
| OPS-12 | P0 | Giữ khóa thuê khi trả | NOT_RUN | | |
| OPS-13 | P0 | Pin giao/trả được giữ riêng | NOT_RUN | | |
| OPS-14 | P0 | Biên pin dưới 20 phần trăm | NOT_RUN | | |
| OPS-15 | P1 | Pin âm hoặc hơn 100 | NOT_RUN | | |
| OPS-16 | P1 | Thiếu pin hoặc ODO | NOT_RUN | | |
| OPS-17 | P1 | Địa điểm và phí giao nhận | NOT_RUN | | |
| OPS-18 | P1 | Ghi phụ kiện và ngoại quan | NOT_RUN | | |
| OPS-19 | P0 | Đổi xe trong chuyến | NOT_RUN | | |
| OPS-20 | P0 | Đổi sang xe không đủ điều kiện | NOT_RUN | | |
| OPS-21 | P0 | Một hợp đồng nhiều xe trả cùng lúc | NOT_RUN | | |
| INC-01 | P0 | Ghi sự cố đúng xe đúng chuyến | NOT_RUN | | |
| INC-02 | P0 | Một chuyến hai sự cố | NOT_RUN | | |
| INC-03 | P0 | Tạo Charge bồi thường | NOT_RUN | | |
| INC-04 | P0 | Chống tạo Charge lặp | NOT_RUN | | |
| INC-05 | P1 | Phân biệt phí hai sự cố | NOT_RUN | | |
| INC-06 | P1 | Bên có lỗi và quyết định khách | NOT_RUN | | |
| INC-07 | P0 | Liên kết thay xe | NOT_RUN | | |
| INC-08 | P1 | Không thay xe bằng chính nó | NOT_RUN | | |
| INC-09 | P0 | Xác nhận thay xe lặp | NOT_RUN | | |
| INC-10 | P1 | Sự cố sau khi đã quyết toán | NOT_RUN | | |
| FIN-01 | P0 | Thu tiền thuê gốc | NOT_RUN | | |
| FIN-02 | P0 | Thu cọc | NOT_RUN | | |
| FIN-03 | P0 | Chưa xác nhận Payment chưa coi là đã thu | NOT_RUN | | |
| FIN-04 | P0 | Tiền ở Operations lấy từ Finance | NOT_RUN | | |
| FIN-05 | P0 | Charge số lượng nhân đơn giá | NOT_RUN | | |
| FIN-06 | P0 | Miễn trễ 10 phút | NOT_RUN | | |
| FIN-07 | P0 | Miễn trễ đúng 15 phút | NOT_RUN | | |
| FIN-08 | P0 | Trễ 16 phút | NOT_RUN | | |
| FIN-09 | P0 | Trễ đúng 60 phút | NOT_RUN | | |
| FIN-10 | P0 | Trễ 65 phút | NOT_RUN | | |
| FIN-11 | P1 | Trả sớm và qua nửa đêm | NOT_RUN | | |
| FIN-12 | P1 | Biên 15 phút và 1 giây | NOT_RUN | | |
| FIN-13 | P0 | Giá pin từ danh mục | NOT_RUN | | |
| FIN-14 | P0 | Không phí pin đúng 20 phần trăm | NOT_RUN | | |
| FIN-15 | P0 | Quyết toán không phụ phí | NOT_RUN | | |
| FIN-16 | P0 | Quyết toán phụ phí nhỏ hơn cọc | NOT_RUN | | |
| FIN-17 | P0 | Quyết toán phụ phí lớn hơn cọc | NOT_RUN | | |
| FIN-18 | P0 | Phụ phí bằng cọc | NOT_RUN | | |
| FIN-19 | P0 | Nhiều loại phí cộng đúng | NOT_RUN | | |
| FIN-20 | P0 | Quyết toán lặp | NOT_RUN | | |
| FIN-21 | P0 | Thu tiền/hoàn tiền nhấn lặp | NOT_RUN | | |
| FIN-22 | P0 | Charge nháp/hủy không bị cộng sai | NOT_RUN | | |
| FIN-23 | P1 | Giá và tiền tệ không sai dấu | NOT_RUN | | |
| FIN-24 | P1 | Giá theo ngày hiệu lực | NOT_RUN | | |
| FIN-25 | P0 | Không lẫn hợp đồng cùng khách | NOT_RUN | | |
| FIN-26 | P1 | Phụ phí đã được trả riêng | NOT_RUN | | |
| FIN-27 | P1 | Liên kết hóa đơn nếu thuộc phạm vi | NOT_RUN | | |
| E2E-01 | P0 | Chuyến chuẩn trọn vòng | NOT_RUN | | |
| E2E-02 | P0 | Chuyến trễ giờ và thiếu pin | NOT_RUN | | |
| E2E-03 | P0 | Chuyến hỏng vượt cọc | NOT_RUN | | |
| E2E-04 | P0 | Đổi xe giữa chuyến | NOT_RUN | | |
| E2E-05 | P0 | Bảo dưỡng tương lai ngăn đặt nhầm | NOT_RUN | | |
| E2E-06 | P0 | Hai khách tranh cùng xe | NOT_RUN | | |
| E2E-07 | P0 | Khóa thuê giữa lúc chuẩn bị giao | NOT_RUN | | |
| E2E-08 | P0 | Không sử dụng tiền của chuyến khác | NOT_RUN | | |
| E2E-09 | P0 | Bảo dưỡng xong rồi thuê lại | NOT_RUN | | |
| E2E-10 | P0 | Hoàn tiền không giải phóng xe chưa trả | NOT_RUN | | |
| E2E-11 | P1 | Hai chuyến kế tiếp giữ đúng lịch sử | NOT_RUN | | |
| E2E-12 | P0 | Tất cả màn hình khớp sau tải lại | NOT_RUN | | |
| ACL-01 | P0 | Bắc quản lý xe | NOT_RUN | | |
| ACL-02 | P0 | Kỹ thuật viên quản lý bảo dưỡng | NOT_RUN | | |
| ACL-03 | P0 | Quản trị Fleet không vượt workflow | NOT_RUN | | |
| ACL-04 | P0 | Người ngoài Fleet | NOT_RUN | | |
| ACL-05 | P0 | Giang giao/trả bằng quyền thật | NOT_RUN | | |
| ACL-06 | P0 | Nhân không tự nhận đã thu tiền | NOT_RUN | | |
| ACL-07 | P0 | Giang không tự thay khoản thu đã xác nhận | NOT_RUN | | |
| ACL-08 | P1 | Quyền cộng dồn | NOT_RUN | | |
| ACL-09 | P1 | Hai công ty nếu sử dụng | NOT_RUN | | |
| ACL-10 | P1 | Đổi người dùng trên cùng trình duyệt | NOT_RUN | | |
| REP-01 | P0 | Hai phiên xác nhận giao cùng xe | NOT_RUN | | |
| REP-02 | P0 | Hai phiên tạo phí cùng sự cố | NOT_RUN | | |
| REP-03 | P0 | Hai phiên quyết toán cùng hợp đồng | NOT_RUN | | |
| REP-04 | P0 | Tab nhận trả cũ sau chuyến mới | NOT_RUN | | |
| REP-05 | P1 | Refresh ngay sau xác nhận | NOT_RUN | | |
| REP-06 | P1 | Mất mạng ở phía trình duyệt | NOT_RUN | | |
| REP-07 | P0 | Lỗi ở bước cuối không để cập nhật dở | NOT_RUN | | |
| REP-08 | P1 | Hủy sửa form | NOT_RUN | | |
| UI-01 | P1 | Kanban đủ bốn trạng thái | NOT_RUN | | |
| UI-02 | P1 | Tìm xe theo ba tiêu chí | NOT_RUN | | |
| UI-03 | P1 | Bộ lọc xe | NOT_RUN | | |
| UI-04 | P1 | Tìm và nhóm bảo dưỡng | NOT_RUN | | |
| UI-05 | P1 | Tra cứu chứng từ xuyên phân hệ | NOT_RUN | | |
| UI-06 | P1 | Tiếng Việt, số và giờ | NOT_RUN | | |
| UI-07 | P1 | Tải lại và đếm số bản ghi | NOT_RUN | | |
| SCP-01 | P1 | Không yêu cầu pin asset ngoài phạm vi | NOT_RUN | | |
| SCP-02 | P1 | Phụ kiện đúng mức đơn giản | NOT_RUN | | |
| SCP-03 | P0 | Đối chiếu dữ liệu thật trước/sau test | NOT_RUN | | |
| SCP-04 | P0 | Chạy lại lỗi sau sửa | NOT_RUN | | |
| SCP-05 | P0 | Đóng băng bản đã kiểm | NOT_RUN | | |
| SCP-06 | P0 | Buổi demo thử từ đăng nhập | NOT_RUN | | |


## Mẫu ghi một lỗi

- Mã lỗi: BUG-…; ca: …; bản đang thử: …
- Tài khoản/nhóm quyền: …; xe/hợp đồng/ticket/Charge/Payment: …
- Chuẩn bị và dữ liệu nhập: …
- Bước đầu tiên sai: …
- Mong đợi: …; trích yêu cầu Word/ảnh hoặc quyết định Q: …
- Thực tế sau tải lại: …; ảnh/thời gian/thông báo lỗi: …
- Có làm sai xe/lịch/tiền hoặc chặn demo không: …
- Người xử lý/bản sửa: …; ngày kiểm lại/kết quả/bằng chứng: …

## Tổng hợp trước khi nộp

- Tổng ca áp dụng: …; PASS: …; FAIL: …; BLOCKED: …; PARTIAL: …; NOT_RUN: …; N/A có lý do: …
- P0 còn FAIL/chưa thử: …
- Các quyết định Q còn thiếu: …
- Lỗi còn lại / ảnh hưởng / nhóm trưởng xác nhận: …
- Bản chạy demo đã kiểm lại: …; người kiểm: …; ngày giờ: …
- Thời điểm đóng băng code/config/database: …; backup của bản này: …

Không chuyển trạng thái hàng loạt sang PASS vì một chuyến mẫu chạy được. Nếu có sửa sau kiểm, ghi bản mới và chạy lại ca lỗi cùng các ca liên quan.
