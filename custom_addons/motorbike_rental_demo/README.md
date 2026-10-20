> Hiện hành: Demo `18.0.1.2.3`, yêu cầu Fleet `18.0.5.12.0`. Bỏ lịch dự kiến; các phiếu chờ xử lý ở trạng thái Mới, không giữ lịch xe. Các mô tả lịch dự kiến bên dưới là thông tin của bản cũ. XML ID giữ nguyên để không sinh bộ demo trùng khi nâng cấp.

# Bản dữ liệu bảo dưỡng định kỳ 18.0.1.2.2

Yêu cầu **Fleet 18.0.5.9.0** trở lên. Bộ dữ liệu hiện có **14 xe**, **7 phiếu bảo dưỡng mẫu**, 18 dòng xe/bảng giá, 3 khách hàng, 3 hợp đồng và 2 phiếu vận hành. Số phiếu thực tế có thể nhiều hơn nếu bạn đã tạo thêm khi thử; không xóa các phiếu đó. Sáu xe và các hợp đồng cũ được giữ nguyên; bổ sung tám xe để minh họa bảo dưỡng.

File mới `data/periodic_demo.xml` được nạp sau catalog.xml và data.xml. Tên hãng/dòng là mẫu thực; biển số, lịch sử, chi phí và trạng thái xe là dữ liệu giả lập. Ngày mốc mới tính theo ngày cài, sau đó giữ nguyên khi nâng cấp. Mỗi máy cài vào ngày khác có ngày tuyệt đối khác nhau nhưng cùng tình huống ban đầu.

**Chính sách cửa hàng giả lập:** Evo200/Feliz S: 2.000 km hoặc 3 tháng; Weaver: 2.500 km hoặc 3 tháng, mốc nào đến trước. Báo sớm 200 km/7 ngày. Không khẳng định đây là chu kỳ do hãng khuyến nghị. Các giá trị được gán riêng cho từng xe demo; xe mới tạo không tự kế thừa cấu hình từ dòng xe.

| Biển số giả lập | Dòng xe | ODO | Tình huống lúc cài |
|---|---|---:|---|
| 59-S3 482.61 | Evo200 | 6.240 | Chưa đến hạn; có hồ sơ định kỳ hoàn tất ở 5.800 km |
| 59-S3 482.62 | Feliz S | 9.850 | Còn 150 km tới mốc 10.000; đã hẹn phiếu định kỳ sau 2 ngày |
| 59-S3 482.63 | Evo200 | 12.000 | Đến đúng mốc bảo dưỡng 12.000 km |
| 59-S3 482.64 | Weaver | 15.280 | Vượt mốc 15.000 km 280 km; có lịch sử đã hoàn tất |
| 59-S3 482.65 | Weaver | 7.420 | Còn 5 ngày đến hạn theo lịch |
| 59-S3 482.66 | Feliz S | 4.350 | Quá hạn theo ngày 4 ngày, chưa tới ngưỡng km |
| 59-S3 482.67 | Evo200 | 8.320 | Xe tiếp nhận từ đội cũ, thiếu mốc ban đầu đã xác minh |
| 59-S3 482.68 | Weaver | 18.760 | Đang thực hiện phiếu định kỳ, trạng thái Bảo dưỡng |

Các xe mới tự sinh mã XE khi nạp, dùng XML ID để liên kết; mã số có thể khác giữa các database. Có ngày đưa vào sử dụng, màu xe, ngoại quan và ghi chú phụ kiện. Hai phiếu lịch sử có ODO chụp khi hoàn tất, chi phí và kết quả công việc; một phiếu mới đang chạy, một phiếu đã lên lịch.

Khi cài module Demo trên database mới, XML nạp đầy đủ. Khi chuyển từ chính sách theo dòng xe sang từng xe, migration Fleet 18.0.5.9.0 sao chép cấu hình cũ xuống từng xe một lần; không chạy lại chuỗi giao/nhận cũ. Các bản ghi mới dùng noupdate, không tự reset cảnh báo/ngày mốc khi nâng cấp lần sau.

---

## Bộ dữ liệu thuê xe ban đầu và cách cài chung

# Bộ dữ liệu mẫu chung của nhóm

File tình huống nghiệp vụ: `data/data.xml`. Danh mục hãng, 18 dòng xe và bảng giá: `data/catalog.xml` (nạp trước). Module tùy chọn `motorbike_rental_demo` phụ thuộc Finance, qua đó phụ thuộc Operations, Rental Core và Fleet. Cần bản tích hợp Odoo 18 đã có API giao/nhận và trường ODO. Không cần thêm file này vào manifest của các module nghiệp vụ.

## Cài đặt

Trước khi tạo hợp đồng demo, cấu hình tiền tệ của công ty là **VND** trong Settings → Companies. Bộ dữ liệu có 18 bảng giá VND; hợp đồng mới lấy tiền tệ mặc định từ công ty. Trên database thử `fleet_team_test_dev_20261017`, cấu hình này đã được sửa ngày 18/10/2026. Không đổi tiền tệ công ty đã phát sinh bút toán kế toán; Odoo sẽ chặn thao tác đó. Module dữ liệu mẫu không tự ghi đè tiền tệ công ty của thành viên.

Đưa cả thư mục `motorbike_rental_demo` vào `custom_addons`, cập nhật danh sách ứng dụng, bỏ bộ lọc Apps và tìm **Motorbike Rental Demo Data**, sau đó cài đặt. Hoặc sau khi sao lưu database và dừng web:

```bash
docker compose run --rm web odoo -d TEN_DATABASE -i motorbike_rental_demo --stop-after-init --no-http
docker compose up -d web
```

Đây là dữ liệu minh họa, không phải số liệu kinh doanh thật. Ngày tham chiếu cố định 18/10/2026, lịch thuê 18–21/10 và lịch bảo dưỡng 20/10; nếu demo ở thời điểm khác cần chỉnh ngày trong XML trước khi cài trên database mới. Trường Datetime trong XML là UTC; giao diện hiển thị theo múi giờ tài khoản. Thời điểm thao tác giao/nhận thực tế được workflow ghi theo lúc nạp file.

## Nội dung

- 2 hãng, 18 dòng xe, 18 bảng giá thuê mẫu VND; 3 khách hàng minh họa.
- 6 xe, mã/biển số `DEMO-W8-001` đến `DEMO-W8-006`.
- 3 hợp đồng: một nháp để demo xác nhận/giao xe, một đang thuê, một đã trả/hoàn tất.
- 2 phiếu vận hành được lấy xe từ hợp đồng và thực hiện giao/nhận bằng API nghiệp vụ.
- 3 phiếu bảo dưỡng: một đang sửa, một lên lịch, một lịch sử hoàn tất.
- 2 phiếu cọc nháp, 1 phụ phí vệ sinh nháp có liên kết hợp đồng/khách hàng. Chưa tạo hóa đơn kế toán hoặc xác nhận thanh toán.

| Mã xe | Tình huống ban đầu |
|---|---|
| DEMO-W8-001 | Sẵn sàng, hợp đồng nháp để thao tác demo; ODO 100 |
| DEMO-W8-002 | Sẵn sàng nhưng khóa thuê để kiểm kê |
| DEMO-W8-003 | Đang thuê; ODO 1000 |
| DEMO-W8-004 | Đã trả, Chờ kiểm tra; ODO cập nhật từ 2000 lên 2080 |
| DEMO-W8-005 | Bảo dưỡng đang chạy, sửa đèn |
| DEMO-W8-006 | Sẵn sàng nhưng lịch bảo dưỡng chặn đặt xe trong khoảng 20/10 |

XML có `noupdate="1"`, các XML ID cố định giúp giữ quan hệ dù ID số khác giữa các máy. Những lần nâng cấp module không chạy lại chuỗi giao/nhận hoặc ghi đè dữ liệu mẫu. Không import lại bằng `mode='init'` trên database đã cài; không dùng gỡ/cài lại module để reset dữ liệu, vì có bản ghi đã thuê/bảo dưỡng được bảo vệ. Muốn khôi phục tình huống ban đầu, dùng database thử mới hoặc bản backup trước khi cài.

Cài cùng file cho mọi thành viên tạo cùng bộ dữ liệu ban đầu; các thao tác sau đó trên từng máy không tự đồng bộ. Không push database/config/mật khẩu lên GitHub.


## Danh mục thực tế đã thống nhất ngày 18/10/2026

- **VinFast (10):** Evo200, Evo200 Lite, Feliz S, Klara S (2022), Vento S, Theon S, Ludo, Impes, Tempest, Klara A2.
- **Dat Bike (8):** Weaver, Weaver 200, Weaver++, Quantum, Quantum S1, Quantum S2, Quantum S3, ERA.
- Các dòng gồm cả mẫu đời cũ, không khẳng định cả 18 đều đang bán mới. Tên hãng/dòng theo hãng; giá thuê do nhóm giả lập, không phải giá hãng công bố.
- Nguồn VinFast: https://vinfastauto.com/vn_vi/cac-mau-xe-may-dien-vinfast-dang-mua
- Nguồn Dat Bike: https://dat.bike/cac-dong-xe-may-dien-cua-dat-bike/

Fleet `18.0.5.7.1` ẩn Danh mục và các menu hãng/dòng con cho mọi vai trò bằng `active=False`; không xóa bảng hoặc các liên kết dữ liệu. Ô chọn dòng xe trong hồ sơ phương tiện chỉ chọn mẫu có sẵn, không tạo nhanh. Đây là ẩn giao diện, không phải khóa API/ORM với quản trị viên.

Bộ dữ liệu lưu trữ hãng chuẩn Odoo khác chỉ khi chưa có dòng xe; không xóa hãng có liên kết. Trên database đang chạy thử không có hãng khác đang dùng. Khi cài vào dữ liệu riêng của nhóm đã có hãng/dòng khác, phải đối chiếu trước; không tự xóa dữ liệu của thành viên.

Với database đã cài phiên bản demo 18.0.1.0.0, nâng cấp cả Fleet và Demo. Migration 18.0.1.1.0 chỉ chuẩn hóa tên danh mục đã thống nhất và lưu trữ hãng không dùng; không chạy lại giao/nhận, không đặt lại trạng thái xe hoặc giá đã chốt trên hợp đồng.
