# Dữ liệu Fleet giả lập một năm

Đã nhập vào database `motorbike_fleet_simple_20261002`, truy cập http://localhost:8072. Tài khoản demo vẫn là `admin` / `admin`.

Lịch sử nghiệp vụ từ **02/10/2025 đến hết 01/10/2026**. Toàn bộ xe, model, đối tác, giá và tình huống là dữ liệu giả lập phục vụ đồ án.

## Quy mô

- Giữ 3 xe và 2 hồ sơ demo ban đầu.
- Bổ sung 36 xe XE101–XE136: 24 xe từ tháng 10/2025, thêm 6 xe tháng 01/2026 và 6 xe tháng 05/2026.
- Tổng cộng **39 xe**, gồm **37 xe chưa lưu trữ và 2 xe đã lưu trữ**.
- Bổ sung 4 model thuộc thương hiệu Demo E-Motion, 3 nhà cung cấp, 4 kỹ thuật viên và 4 loại dịch vụ.
- Bổ sung 298 hồ sơ bảo dưỡng: 275 hoàn tất, 6 hủy, 12 đã lên lịch, 3 đang thực hiện, 2 nháp. Tổng cả dữ liệu ban đầu: **300 hồ sơ**.
- 9 hồ sơ của xe đã lưu trữ cũng được Odoo chuẩn lưu trữ. Màn hình thường hiển thị 291 hồ sơ còn active; bỏ lọc active/thêm bộ lọc Đã lưu trữ khi đối chiếu toàn bộ.
- Chi phí 275 hồ sơ hoàn tất: **102.450.000 VND**. Hồ sơ đang sửa có chi phí dự kiến; lịch tương lai và đề xuất nháp chưa phát sinh chi phí.

## Tình trạng 36 xe mới

| Tình trạng | Số xe |
| --- | ---: |
| Sẵn sàng | 20 |
| Đang thuê (trạng thái giả lập) | 8 |
| Chờ kiểm tra sau trả | 3 |
| Đang bảo dưỡng | 3 |
| Đã ngừng khai thác/lưu trữ | 2 |

Trong 20 xe sẵn sàng, 2 xe bị khóa thuê vì kiểm kê/đào tạo; đạt kỹ thuật không tự gỡ khóa. Lịch bảo dưỡng tương lai là dữ liệu nhập tay; bản tuần 6 chưa có kiểm tra/chặn lịch thuê.

## Phân bố lịch sử

| Tháng | Hồ sơ hoàn tất | Chi phí (VND) |
| --- | ---: | ---: |
| 2025-10 | 1 | 650.000 |
| 2025-11 | 28 | 8.440.000 |
| 2025-12 | 14 | 6.630.000 |
| 2026-01 | 21 | 6.000.000 |
| 2026-02 | 25 | 9.220.000 |
| 2026-03 | 17 | 6.870.000 |
| 2026-04 | 26 | 8.780.000 |
| 2026-05 | 23 | 9.210.000 |
| 2026-06 | 36 | 16.150.000 |
| 2026-07 | 19 | 4.920.000 |
| 2026-08 | 30 | 8.750.000 |
| 2026-09 | 33 | 16.230.000 |
| 2026-10 | 2 | 600.000 |

Khoảng 12 tháng đi qua 13 nhãn tháng: tháng 10/2025 chỉ tính từ ngày 02, tháng 10/2026 chỉ tính ngày 01.

## Cách xem

1. Làm mới trang (F5) sau khi đăng nhập.
2. Fleet → Xe máy điện: tìm XE101–XE136 bằng tìm kiếm chuẩn Odoo và mở form để nhập/sửa thông tin.
3. Fleet → Bảo dưỡng xe điện: mở hồ sơ để xem/sửa trạng thái, chi phí, thời gian và kết quả.
4. Dùng bộ lọc Đã lưu trữ để xem XE135–XE136 và lịch sử liên quan.

## Giới hạn và tính nhất quán

Không tạo hợp đồng Rental, khách thuê hoặc bản ghi Inspection vì các model đó chưa có trong repo. Đang thuê và chờ kiểm tra là trạng thái Fleet giả lập; không có doanh thu hay lịch sử thuê/trả đầy đủ.

Bộ dữ liệu được tạo ở bản trước và giữ nguyên khi đưa dự án về tuần 6. Script nhập lại hiện dùng CRUD trực tiếp cho trạng thái và thời gian, không cần workflow hoặc mô phỏng đồng hồ. Không giả mạo thời điểm audit create_date/write_date; email/tracking khi seed được tắt. Chi phí dùng VND; cấu hình tiền tệ công ty demo đã đổi từ USD sang VND.

Đã kiểm tra: ngày thực hiện không trước ngày nhận xe; thời gian thực tế hợp lệ, không chồng nhau trên cùng xe; hồ sơ hoàn tất có kết quả; xe sẵn sàng/đang thuê đạt kỹ thuật; xe đang sửa chưa đạt kỹ thuật trong bộ dữ liệu mẫu; dữ liệu truy cập được qua API web đăng nhập admin.

Script dùng external IDs `fleet_year_demo.*`; chạy lại sau khi đã seed chỉ kiểm tra và xuất lại tổng hợp, không tạo trùng. Chỉ chạy trên database demo được chỉ định.

## Script và sao lưu

- Nhập dữ liệu: `scripts/load_year_demo.py` (sao lưu trước, sau đó chạy `scripts/seed_year_demo.py` qua Odoo shell).
- Tổng hợp máy đọc: `docs/FLEET_YEAR_DEMO_SUMMARY.json`.
- Sao lưu trước khi nhập thành công: `%TEMP%/codex-fleet-simple-20261002/before-year-demo-20261002-183627/`.
- Sao lưu sau khi nhập: `archive/year-demo-20261002/database.dump` và thư mục `filestore/` đi kèm. Không chứa cấu hình kết nối/mật khẩu plaintext.
- Bản backup dữ liệu được loại khỏi Git bằng `.gitignore`; vẫn tồn tại trên máy để phục hồi bằng PostgreSQL/Odoo.

## Phạm vi hiện hành

Module `19.0.3.1.0` dừng ở tuần 6: mọi trạng thái/mốc bảo dưỡng do người dùng sửa trực tiếp. Dữ liệu một năm được giữ để xem và thử CRUD, không có báo cáo mới, availability hoặc tự động giao/trả. Sau nâng cấp, fingerprint toàn bộ 39 dòng xe và 300 dòng bảo dưỡng không đổi.
