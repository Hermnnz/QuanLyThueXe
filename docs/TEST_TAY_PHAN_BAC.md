# Các ca Bắc cần tự kiểm trước khi nộp

Chỉ kiểm phần Fleet và bảo dưỡng của Bắc tại http://localhost:8072/. Không yêu cầu bạn tự kiểm hợp đồng, tính phí, thu tiền hoặc quyết toán của các thành viên khác.

Chuẩn đúng sai: các tài liệu Word nhóm cung cấp, gồm bộ tuần 8 và file nghiệp vụ. Code đang chạy không phải đáp án. Chỗ Word khác nhau phải xác nhận với nhóm trưởng.

Dùng xe và phiếu có mã TEST, không sửa/xóa dữ liệu cần đem nộp. Sau mỗi lần lưu hoặc xác nhận, tải lại trang để xem dữ liệu đã được giữ đúng chưa. Mỗi dòng chỉ đánh đạt khi đã làm đủ các biến thể. Tất cả ô dưới đây hiện chưa được kiểm thử.

## 16 ca bạn tự làm trên màn hình Fleet

| STT | Bạn làm gì | Kết quả phải thấy | Kết quả của bạn |
| --- | --- | --- | --- |
| 1 | Vào Phương tiện, tạo xe TEST-X01; chọn dòng xe, nhập biển số giả, ngày sử dụng và mô tả; lưu rồi mở lại. | Giữ đúng thông tin; xe mới Chờ kiểm tra, chưa đạt kỹ thuật. | ☐ Đạt ☐ Lỗi |
| 2 | Tạo thêm xe cùng mã TEST-X01. Sau đó thử lại với mã của một xe TEST đã lưu trữ. | Cả hai trường hợp đều không cho trùng mã. | ☐ Đạt ☐ Lỗi |
| 3 | Với xe TEST chưa có bảo dưỡng chạy, bấm Xác nhận đạt kỹ thuật. | Xe sang Sẵn sàng, cờ Đạt kỹ thuật bật. | ☐ Đạt ☐ Lỗi |
| 4 | Bật Khóa thuê nhưng để lý do trống; thử chỉ nhập dấu cách; sau đó nhập lý do Kiểm kê và lưu. | Hai lần đầu bị chặn; có lý do thật thì lưu được. Xe có thể vẫn đạt kỹ thuật nhưng bị khóa thuê. | ☐ Đạt ☐ Lỗi |
| 5 | Trên xe đang khóa có lý do, bấm Xác nhận đạt kỹ thuật nếu đủ điều kiện. Sau đó chủ động bỏ khóa và lưu. | Xác nhận kỹ thuật không tự xóa khóa/lý do; chỉ thao tác bỏ khóa của bạn mới mở khóa. | ☐ Đạt ☐ Lỗi |
| 6 | Thử kéo xe sang cột trạng thái khác trên Kanban; thử sửa trực tiếp trạng thái/cờ đạt kỹ thuật trên form. | Không đổi trực tiếp được; phải đi qua thao tác nghiệp vụ. | ☐ Đạt ☐ Lỗi |
| 7 | Sao chép một xe TEST đã đạt kỹ thuật. | Xe mới không giữ nguyên mã cũ và không tự được coi là đạt kỹ thuật. | ☐ Đạt ☐ Lỗi |
| 8 | Lưu trữ một xe TEST không có chuyến đang diễn ra; tìm qua bộ lọc Đã lưu trữ; khôi phục. | Tìm lại được; lịch sử không mất; khôi phục đúng xe, không tạo bản sao. | ☐ Đạt ☐ Lỗi |
| 9 | Tạo phiếu bảo dưỡng cho xe TEST: nhập nội dung, ngày, loại, ghi chú, chi phí; lưu. Thử ba loại Định kỳ/Sửa chữa/Khẩn cấp trên các phiếu riêng. | Lưu đúng dữ liệu và loại; phiếu Mới chưa tự làm xe chuyển sang Bảo dưỡng. | ☐ Đạt ☐ Lỗi |
| 10 | Trên các phiếu riêng, thử Lên lịch khi thiếu giờ; cuối trước đầu; đầu bằng cuối và có chặn thuê. Sau đó nhập khoảng hợp lệ 10:00–12:00. | Ba trường hợp sai bị chặn; lịch hợp lệ lên được Đã lên lịch, xe chưa tự chuyển Bảo dưỡng. | ☐ Đạt ☐ Lỗi |
| 11 | Bắt đầu phiếu có Chặn thuê trên xe sẵn sàng. Thử xác nhận kỹ thuật cho xe khi phiếu còn chạy. | Phiếu Đang thực hiện, có giờ bắt đầu; xe Bảo dưỡng/chưa đạt kỹ thuật; không xác nhận sẵn sàng được lúc này. | ☐ Đạt ☐ Lỗi |
| 12 | Khi phiếu đang chạy, thử đổi xe, đổi Chặn thuê, lưu trữ hoặc xóa phiếu. | Đều bị chặn; không làm mất phiếu đang xử lý. | ☐ Đạt ☐ Lỗi |
| 13 | Thử Hoàn tất khi chưa nhập kết quả hoặc chỉ có dấu cách. Sau đó nhập kết quả sửa thật, Hoàn tất rồi xác nhận kỹ thuật trên xe. | Thiếu kết quả bị chặn. Hoàn tất hợp lệ đưa xe về Chờ kiểm tra/chưa đạt; chỉ sau xác nhận kỹ thuật xe mới Sẵn sàng. | ☐ Đạt ☐ Lỗi |
| 14 | Trên xe TEST khác: bắt đầu phiếu chặn thuê rồi Hủy. Làm thêm trường hợp hai phiếu chặn cùng chạy và chỉ kết thúc một phiếu. | Hủy phiếu chạy cuối cùng đưa xe về Chờ kiểm tra. Còn một phiếu chặn đang chạy thì xe vẫn Bảo dưỡng. | ☐ Đạt ☐ Lỗi |
| 15 | Tạo phiếu không Chặn thuê, Bắt đầu rồi Hoàn tất. Ở phiếu riêng thử chi phí -1 và 0; ngày bảo dưỡng tiếp theo bằng/trước ngày phiếu. | Phiếu không chặn không tự đổi trạng thái xe; chi phí âm bị chặn, 0 được nhận; mốc tiếp theo phải sau ngày phiếu. | ☐ Đạt ☐ Lỗi |
| 16 | Sao chép phiếu đã xong; xem kết quả/giờ thực tế. Từ form xe mở lịch sử bảo dưỡng; tìm xe theo mã/biển/dòng và thử các bộ lọc trạng thái, khóa, đến hạn, lưu trữ. | Bản sao không mang kết quả/giờ thực tế cũ; lịch sử mở đúng xe; tìm/lọc khớp dữ liệu. | ☐ Đạt ☐ Lỗi |

Khi kiểm ca 13–14, dùng các phiếu/xe riêng hoặc chuẩn bị lại đúng trạng thái đầu. Không sửa trạng thái xe bằng tay để tiếp tục một ca đang lỗi.

## 4 ca phối hợp với Giang để kiểm phần Fleet đã nối

Bạn kiểm kết quả trên xe; Giang thao tác giao/trả trên màn hình Operations. Nếu bản 8072 chỉ có Fleet hoặc chưa nối Operations, ghi Chưa kiểm được; không đánh đạt và không cần tìm nút giao/trả trên form Fleet.

| STT | Giang và bạn làm gì | Kết quả Fleet cần kiểm | Kết quả của bạn |
| --- | --- | --- | --- |
| 17 | Giang giao xe TEST sẵn sàng, đủ điều kiện, ODO đầu 1.000; rồi trả với ODO 1.080. Bạn mở lại xe sau từng bước. | Giao xong xe Đang thuê; sau trả ODO hiện tại 1.080; trạng thái sau trả theo quyết định nhóm trưởng bên dưới. | ☐ Đạt ☐ Lỗi ☐ Chưa kiểm được |
| 18 | Thử giao các xe TEST: đang khóa, chưa đạt kỹ thuật, đã lưu trữ, đang có bảo dưỡng chạy chặn thuê. | Đều không giao được. Thêm trường hợp xe đang thuê: không xác nhận kỹ thuật hoặc bắt đầu bảo dưỡng chặn thuê được. | ☐ Đạt ☐ Lỗi ☐ Chưa kiểm được |
| 19 | Giang thử ODO giao thấp hơn số xe, ODO trả thấp hơn lúc giao và số âm. | Đều bị chặn; không đổi trạng thái/ODO/phiếu một phần sau báo lỗi. | ☐ Đạt ☐ Lỗi ☐ Chưa kiểm được |
| 20 | Bạn lên lịch bảo dưỡng chặn thuê 10:00–12:00. Phối hợp kiểm thuê 11:00–13:00, 08:00–10:00 và 12:00–14:00 qua luồng đã nối kiểm tra Fleet. | Lịch giao nhau bị chặn; hai khoảng tiếp giáp không bị chặn chỉ do lịch bảo dưỡng này. Phiếu đang chạy chưa xong vẫn chặn dù qua giờ dự kiến. | ☐ Đạt ☐ Lỗi ☐ Chưa kiểm được |

**Một điểm cần chốt:** ảnh bổ sung tuần 8 minh họa trả xe thẳng về `available`, còn file nghiệp vụ mô tả Giang nhận về `pending_inspection` để Bắc kiểm tra. Ghi quyết định nhóm trưởng ở đây: … Không lấy trạng thái code đang trả ra để tự kết luận đúng.

## Ghi lỗi và kết luận

Mỗi lỗi chỉ cần ghi: số ca, mã xe/phiếu, dữ liệu vừa nhập, bước sai, kết quả thực tế, ảnh chụp. Không đổi một ca sang Đạt chỉ vì người khác nói đã sửa; làm lại ca đó sau sửa.

- Ca 1–16: Đạt …/16; Lỗi …; Chưa làm …
- Ca 17–20: Đạt …/4; Lỗi …; Chưa kiểm được …
- Quy trình trả xe nhóm trưởng đã chốt: …
- Lỗi còn trước khi nộp: …

Danh sách này là lượt kiểm tập trung cho phần Bắc, không phải tuyên bố đã kiểm hết mọi biên hoặc toàn bộ bốn phân hệ. Những phần chưa thử phải ghi rõ khi báo nhóm.
