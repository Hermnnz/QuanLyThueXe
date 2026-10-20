# Vai trò Fleet, xe ngừng hoạt động và hoàn tất bảo dưỡng — 20/10/2026

Fleet 18.0.5.13.0. Mở rộng quy trình hiện có; không đổi các phần Rental/Finance của nhóm.

## Quy trình

Hoàn tất phiếu có chặn thuê, nếu không còn phiếu chặn thuê nào đang thực hiện: xe tự Sẵn sàng và đạt kỹ thuật. Kết quả công việc bắt buộc. Nếu còn phiếu chặn thuê khác, xe vẫn Bảo dưỡng. Hủy phiếu cuối: về Chờ kiểm tra, không tự xác nhận kỹ thuật. Khóa thuê thủ công giữ nguyên; Sẵn sàng không đồng nghĩa được đặt nếu còn khóa.

## Ngừng hoạt động

Dùng Lưu trữ hoặc bỏ Đang sử dụng: active=False, operational_status=inactive, technical_ready=False. Xe có cột Ngừng hoạt động trong Kanban nhờ action mở cả bản ghi lưu trữ; mặc định danh sách chọn xe trong Rental vẫn loại active=False và điều kiện Fleet từ chối thuê. Không kéo thả trạng thái. Xe đang thuê hoặc đang sửa phải nhận trả/hoàn tất hoặc hủy phiếu trước. Khôi phục active=True về Chờ kiểm tra, chưa đạt kỹ thuật; quản lý xác nhận mới Sẵn sàng. Không xóa xe, kể cả quản lý.

Nhãn khóa thuê/cảnh báo nằm trong cụm góc trên bên phải của thẻ, có thể xếp dọc. Thanh kỹ thuật giữ bên dưới thông tin xe. Không đổi logic hạn bảo dưỡng vì thay vị trí nhãn.

## Vai trò

- Quản lý xe: kế thừa quyền quản lý Fleet, xem/tạo/sửa/quản lý phiếu, lưu trữ/khôi phục, hủy phiếu và xác nhận kỹ thuật. Vẫn tuân thủ không xóa xe, không giảm ODO, không xóa phiếu đang thực hiện hoặc sửa nội dung phiếu đã kết thúc.
- Nhân viên quản lý xe: xem/tạo xe và phiếu Mới, không sửa trực tiếp hồ sơ, chi phí, ODO hay phiếu; không xóa/lưu trữ/khôi phục/hủy/xác nhận kỹ thuật riêng. Được Bắt đầu phiếu Mới và Hoàn tất phiếu đang thực hiện. Hoàn tất mở hộp thoại chỉ nhập Kết quả, xác nhận cập nhật đúng result/state theo luồng được kiểm soát. Không cấp write tổng quát cho nhân viên. Kiểm tra quyền cả phiếu lẫn xe và công ty trước khi chạy phần cập nhật hệ thống. Các phương thức chuyển trạng thái nội bộ không gọi qua RPC.
- Kỹ thuật viên cũ kế thừa vai trò nhân viên; quản lý Fleet chuẩn vẫn có quyền quản lý để không làm mất quyền tài khoản quản lý hiện tại. Không thay nhóm quyền admin local hiện có.

Hai tài khoản demo được tạo riêng trong database local bằng ORM, không nằm trong XML/manifest và không ghi mật khẩu vào tài liệu Git. Thông tin đăng nhập được gửi trực tiếp trong chat. Nếu người khác cài source, tạo user và chọn đúng nhóm vai trò; nâng cấp module để nạp ACL/view mới.

Bản sao lưu trước đợt đổi ở đường dẫn trong archive/latest-fleet-batch-backup.txt: source.zip, runtime.zip và database.dump. Không xóa ảnh hoặc filestore. Chưa push thay đổi này lên GitHub.

## Xác minh triển khai

Bản gộp trên database thử: 106/106 kiểm tra đạt (Fleet, Rental Core/website, Operations, Demo). Kiểm tra tập trung sau hoàn thiện quyền/giao diện: 10/10 đạt trên database local, gồm ngăn nhập trạng thái qua context mặc định và ngăn khôi phục hỗn hợp làm đổi trạng thái xe đang thuê. Đăng nhập HTTP thực tế bằng fleet_manager và fleet_staff thành công; quản lý có form sửa, nhân viên có form chỉ xem nhưng vẫn tạo và thao tác qua quy trình. Cột inactive hiện trong read_group khi mở active_test=False. API write/unlink/cancel của nhân viên bị chặn, kiểm tra bằng recordset rỗng không sửa dữ liệu thật.

Tài khoản quản lý Fleet và nhân viên chỉ được tạo trong database fleet_team_test_dev_20261017, không đưa lên GitHub. Không gửi mật khẩu trong code nguồn được theo dõi.
