# Tách file giao diện Fleet ngày 16 tháng 10 năm 2026

Phạm vi: tổ chức lại XML của Fleet `18.0.5.7.0` trên bản tích hợp Odoo 18. Giữ nguyên model, quyền, phương thức nghiệp vụ và phiên bản module.

## Cấu trúc mới

Năm file được nạp theo thứ tự trong `custom_addons/motorbike_fleet_management/__manifest__.py`:

| File trong thư mục views | Nội dung | Số khai báo |
| --- | --- | ---: |
| fleet_vehicle_views.xml | Form, list, search và Kanban phương tiện | 4 |
| fleet_catalog_views.xml | Form/list/search dòng xe và form hãng xe | 4 |
| fleet_service_views.xml | Form, search và list bảo dưỡng | 3 |
| fleet_actions.xml | Action mở màn hình, lựa chọn view và tên action danh mục | 6 |
| fleet_menu.xml | Menu nghiệp vụ và điều chỉnh menu chuẩn | 14 |

File gộp `fleet_views.xml` được thay bằng năm file trên; không tiếp tục nạp file gộp để tránh khai báo lặp. Các báo cáo cũ liên kết tới file gộp mô tả phiên bản lịch sử.

## Kiểm tra cấu trúc

- Đối chiếu đủ 31 khai báo trước/sau, không trùng hoặc thiếu XML ID.
- Nội dung từng khai báo bằng nhau khi chuẩn hóa khoảng trắng giữa các node XML; các biểu thức điều kiện, domain, context, nhóm quyền, nhãn và tham chiếu giữ nguyên.
- Kiểm tra thứ tự tham chiếu XML ID nội bộ: các view được nạp trước action, action trước menu.
- Mọi đường dẫn `data` trong manifest tồn tại. Các thuộc tính manifest ngoài danh sách đường dẫn view giữ nguyên.
- Đối chiếu hash xác nhận các model, ACL, kiểm thử và ba module khác không bị sửa trong lượt tách file.

## Bản sao và kiểm chứng runtime

Bản trước khi tách nằm trong `archive/view-split-20261016-214745/baseline-addons`. Đây là bản sao phục vụ kiểm chứng/hoàn tác, không phải source chính để nộp.

Database thử riêng: `fleet_team_test_view_split_20261016`. Trình kiểm thử không nâng cấp database demo Odoo 19 ở cổng 8072, không đổi cấu hình hoặc khởi động lại server đó.

Kết quả thực chạy:

- Cài bản XML gốc cùng đủ bốn module trên database riêng thành công.
- Nâng cấp với năm file XML mới và chạy bộ kiểm thử Fleet/Core/Operations: **71/71 đạt, 0 failed, 0 errors**, tiến trình exit 0. Finance được cài và nạp cùng hệ thống; kết quả này không tuyên bố bao phủ mọi nghiệp vụ Finance.
- Đối chiếu riêng lần nâng cấp Fleet: 31 bản ghi view/action/menu giữ nguyên ID và các thuộc tính chức năng; 11 view kết hợp kế thừa giống hệt; 11 kiến trúc view sau `get_view` giống hệt.
- Hash toàn bộ dòng của 29 bảng nghiệp vụ Fleet/Rental/Finance trước/sau lần nâng cấp riêng Fleet bằng nhau. Có dữ liệu kiểm chứng riêng gồm xe và bảo dưỡng đã lên lịch; không thử trên database nộp.
- Báo cáo so sánh cuối: `archive/view-split-20261016-214745/runtime-comparison.json`; cả bốn nhóm `records`, `combined_views`, `rendered_views`, `business_tables` đều có danh sách khác biệt rỗng.
- Log kết quả 71 test: `archive/view-split-20261016-214745/regression-71.log`. Bản gốc, hash source và kiểm tra tương đương cấu trúc nằm cùng thư mục sao lưu.

Phương pháp đối chiếu được điều chỉnh để không nhầm tác động nâng cấp các module khác với việc tách Fleet: lượt chạy hồi quy nạp lại cả bốn module làm thay đổi hash một số bảng danh mục/chứng từ; lượt so sánh cuối nạp bản XML gốc rồi chỉ nâng cấp Fleet sang bản tách. Lượt cuối xác nhận toàn bộ 29 bảng giữ nguyên. Giá trị Many2one khi so sánh được chuẩn hóa tuple/list qua JSON, giữ nguyên ID và tên; không bỏ qua thuộc tính chức năng.

Giới hạn: kiểm chứng trên database thử Odoo 18 cùng source hiện tại, không phải chứng nhận mọi lỗi nghiệp vụ của hệ thống đều đã hết. Không chụp/duyệt trực quan mọi màn hình bằng trình duyệt; kiểm tra kiến trúc form và các kiểm thử Form/HTTP hiện có đã đạt. Database thật của nhóm vẫn cần quy trình sao lưu/nâng cấp riêng khi triển khai; lượt này không triển khai lên database đó.

## Cách hoàn tác nếu cần

Chỉ thực hiện khi cần quay về cách gom file cũ, không chép đè toàn bộ dự án:

1. Khôi phục `views/fleet_views.xml` từ bản sao trước tách.
2. Khôi phục riêng danh sách view trong manifest thành `views/fleet_views.xml`.
3. Bỏ năm file mới khỏi danh sách nạp; có thể xóa chúng khi chắc chắn không còn được dùng.
4. Kiểm lại module trên bản thử trước khi nâng cấp môi trường nộp. Dữ liệu và XML ID không cần chuyển đổi vì không đổi định danh.

Khi bàn giao nhóm, đưa đủ năm file mới và manifest cùng nhau. Không chép riêng thư mục views rồi để manifest cũ tham chiếu file đã bỏ. Bộ source này là Odoo 18; không nâng cấp nó trực tiếp lên database demo Odoo 19.
