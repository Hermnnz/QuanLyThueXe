# Odoo Electric Motorbike Rental ERP

> Dự án học phần xây dựng quy trình cho thuê xe máy điện trên Odoo 18, từ tiếp nhận yêu cầu đến giao xe, xử lý sự cố, thu hồi và quyết toán hợp đồng.

## Dự án giải quyết bài toán gì?

Ở một cửa hàng cho thuê xe, thông tin xe, hợp đồng, người đang giữ xe và các khoản tiền thường nằm ở nhiều nơi. Nhân viên cần biết **xe nào thực sự có thể giao**, **khách đã trả đủ tiền trước khi ký chưa**, **đã thu hồi hết xe chưa** và **cuối chuyến phải hoàn hay thu thêm bao nhiêu**.

Nhóm xây dựng một luồng làm việc chung cho bốn mảng: quản lý đội xe (**Fleet**), hợp đồng (**Rental Core**), giao/thu hồi và sự cố (**Operations**), thu tiền và quyết toán (**Finance**). Các bước liên kết với nhau để hạn chế xác nhận hợp đồng trùng xe, giao xe chưa đạt kỹ thuật hoặc đóng hợp đồng khi chưa thu hồi đủ xe.

## Một chuyến thuê diễn ra như thế nào?

Ví dụ, khách thuê một xe trong một ngày với **tiền thuê 600.000đ** và **tiền cọc 500.000đ**:

1. **Tiếp nhận yêu cầu:** Khách gửi thông tin trên website hoặc nhân viên lập hợp đồng tại quầy. Yêu cầu từ website tạo **hợp đồng nháp** để nhân viên kiểm tra; bản nháp chưa giữ chỗ chắc chắn cho xe.
2. **Kiểm tra và ký hợp đồng:** Nhân viên chọn xe phù hợp. Hệ thống kiểm tra tình trạng kỹ thuật và lịch thuê trước khi xác nhận. Finance tạo hai phiếu thu nháp, tương ứng **600.000đ tiền thuê** và **500.000đ tiền cọc**. Sau khi nhận đủ cả hai khoản ngoài đời, nhân viên xác nhận trên hợp đồng; hợp đồng và hai phiếu thu cùng chuyển sang đã xác nhận.
3. **Giao xe:** Nhân viên lập phiếu vận hành từ hợp đồng và xác nhận giao xe. Operations ghi nhận chiếc xe đã giao; Fleet chuyển xe sang **đang thuê**; hợp đồng chuyển sang **đang thuê**. Từ khi đã bắt đầu giao xe, không được hủy trực tiếp hợp đồng.
4. **Xử lý phát sinh:** Nếu có sự cố, nhân viên ghi nhận xe gặp sự cố, bên chịu lỗi và mức phí. Sự cố do khách gây ra và có tiền phạt sẽ tạo **phụ phí nháp** để xử lý; lỗi do xe/công ty không thu phí của khách. Trường hợp cần sửa chữa có thể tạo hồ sơ bên Fleet.
5. **Thu hồi và quyết toán:** Nhân viên xác nhận thu hồi xe. Finance chỉ cho lập hóa đơn khi **tất cả xe trong phiếu vận hành đã được thu hồi**. Hóa đơn gồm tiền thuê và các phụ phí đã xác nhận; hệ thống đối chiếu với những phiếu tiền đã ghi nhận để hiển thị số cần hoàn hoặc thu thêm.
6. **Kết thúc:** Nhân viên thực hiện việc hoàn/thu tiền ngoài đời rồi xác nhận trên hóa đơn. Finance ghi phiếu tiền tương ứng và hợp đồng tự chuyển sang **hoàn tất**.

Trong ví dụ trên, nếu không có phụ phí thì khách được **hoàn 500.000đ cọc**. Nếu có phụ phí được xác nhận là **100.000đ**, khách được **hoàn 400.000đ**. Tiền thuê 600.000đ đã thu lúc ký hợp đồng, nên không thu lại trên hóa đơn.

## Bốn phân hệ phối hợp ra sao?

| Phân hệ | Trách nhiệm trong chuyến thuê |
| --- | --- |
| **Fleet Management** | Quản lý hồ sơ xe, trạng thái sẵn sàng/đang thuê/chờ kiểm tra, điều kiện kỹ thuật và bảo dưỡng. |
| **Rental Core** | Tiếp nhận yêu cầu từ website, quản lý khách hàng, bảng giá, hợp đồng và kiểm tra xe có bị trùng lịch thuê. |
| **Operations** | Lập phiếu giao/thu hồi, theo dõi từng xe thực tế trong chuyến thuê và ghi nhận sự cố. |
| **Finance** | Ghi nhận tiền thuê và cọc trả trước, phụ phí, hóa đơn cuối chuyến, khoản hoàn/thu thêm và trạng thái quyết toán hợp đồng. |

## Phạm vi hiện tại

Đây là **đồ án học phần**, tập trung vào quy trình vận hành và quyết toán tiền thuê. Hóa đơn sử dụng `account.move` của Odoo, còn tiền thuê, cọc và hoàn/thu thêm được theo dõi bằng phiếu tiền của dự án; hệ thống chưa triển khai đối soát kế toán đầy đủ như một sản phẩm thương mại. Quy trình đổi xe nêu trên cũng đang ở giai đoạn thiết kế.

**Công nghệ:** Odoo 18, Python, PostgreSQL, Docker Compose. Mã nguồn bốn phân hệ nằm trong [`custom_addons/`](custom_addons/); tài liệu nghiệp vụ và kiểm thử nằm trong [`docs/`](docs/).
